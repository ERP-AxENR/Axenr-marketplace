#!/usr/bin/env python3
"""Axelor REST session shared by the AI agent scripts.

  python3 -I axelor_session.py login <url> <login>    open a session (password typed in this terminal, never echoed)
  python3 -I axelor_session.py check <url>            show the connected user
  python3 -I axelor_session.py logout <url>           delete the stored session

The password never goes through the conversation, the command line or a file: run the login yourself
in your terminal (in Claude Code: `! python3 -I <path>/axelor_session.py login <url> <login>`).
The cookie jar is stored in ~/.axenr-sessions/<host>.jar (mode 600), the same place as the
connecting-axenr-erp-api skill, so a session opened by either tool works for both.

Login strategy: AOP 8.x accepts the form login (urlencoded, HTTP 303); AOP 7.4 refuses it and needs JSON.
Both are tried, form first, and the session is only kept after a real /ws/rest call succeeds.
"""
import getpass
import http.cookiejar
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


def jar_path(base):
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", re.sub(r"^https?://", "", base.rstrip("/")))
    return os.path.expanduser(f"~/.axenr-sessions/{slug}.jar")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class AxelorError(RuntimeError):
    pass


class Session:
    """Cookie session with CSRF header, JSON helpers and SSE streaming."""

    def __init__(self, base, timeout=300):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.jar = http.cookiejar.MozillaCookieJar(jar_path(self.base))
        if os.path.exists(self.jar.filename):
            with open(self.jar.filename) as handle:
                text = handle.read().replace("#HttpOnly_", "")
            self.jar._really_load(io.StringIO(text), self.jar.filename, True, True)
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def csrf(self):
        return next((c.value for c in self.jar if c.name == "CSRF-TOKEN"), "")

    def _request(self, method, path, payload=None, accept="application/json"):
        body = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.base + path, data=body, method=method)
        req.add_header("Accept", accept)
        if body is not None:
            req.add_header("Content-Type", "application/json")
        if method != "GET":
            req.add_header("X-CSRF-Token", self.csrf())
        return req

    def raw(self, method, path, payload=None):
        try:
            with self.opener.open(self._request(method, path, payload), timeout=self.timeout) as resp:
                text = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            raise AxelorError(f"HTTP {exc.code} on {method} {path}: session expired or missing rights") from exc
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise AxelorError(f"non-JSON answer on {path} (login page? expired session?)") from exc

    def rest(self, method, path, payload=None):
        """Call /ws/rest and fail loudly on an Axelor business error (HTTP 200 with status -1)."""
        answer = self.raw(method, path, payload)
        if isinstance(answer, dict) and answer.get("status", 0) != 0:
            data = answer.get("data")
            message = data.get("message") if isinstance(data, dict) else data
            raise AxelorError(f"Axelor status {answer.get('status')} on {path}: {str(message)[:800]}")
        return answer

    def search(self, model, domain=None, context=None, fields=("id",), limit=500, sort=None):
        data = {}
        if domain:
            data = {"_domain": domain, "_domainContext": context or {}}
        payload = {"offset": 0, "limit": limit, "fields": list(fields), "data": data}
        if sort:
            payload["sortBy"] = sort
        return self.rest("POST", f"/ws/rest/{model}/search", payload).get("data") or []

    def stream(self, path, payload):
        """POST and yield the parsed `data:` events of a server-sent event stream."""
        req = self._request("POST", path, payload, accept="*/*")
        with self.opener.open(req, timeout=self.timeout) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    return
                try:
                    yield json.loads(data)
                except json.JSONDecodeError:
                    continue

    def save(self):
        os.makedirs(os.path.dirname(self.jar.filename), mode=0o700, exist_ok=True)
        old = os.umask(0o077)
        self.jar.save(ignore_discard=True, ignore_expires=True)
        os.umask(old)


def login(base, user):
    session = Session(base)
    session.jar.clear()
    password = getpass.getpass(f"Axelor password for {user} on {base}: ")
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(session.jar), _NoRedirect)
    url = session.base + "/callback?client_name=AxelorFormClient"
    attempts = [
        ("form", urllib.parse.urlencode({"username": user, "password": password}).encode(), "application/x-www-form-urlencoded"),
        ("json", json.dumps({"username": user, "password": password}).encode(), "application/json"),
    ]
    for mode, body, ctype in attempts:
        req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": ctype, "Accept": "application/json"})
        try:
            with opener.open(req, timeout=60) as resp:
                code, location = resp.status, resp.headers.get("Location", "")
        except urllib.error.HTTPError as exc:
            code, location = exc.code, exc.headers.get("Location", "") if exc.headers else ""
        if "error=" in location:
            sys.exit(f"Login refused: {urllib.parse.unquote(location.split('error=')[-1])}")
        if code in (200, 302, 303) and "JSESSIONID" in {c.name for c in session.jar}:
            try:
                session.search("com.axelor.auth.db.User", "self.code = :login", {"login": user}, ("code", "name"), limit=1)
            except AxelorError:
                session.jar.clear()
                continue
            session.save()
            print(f"SESSION OK ({mode} login) for {user} -> {session.jar.filename}")
            return
        session.jar.clear()
    sys.exit("Login failed with both form and JSON modes: check URL, login and password.")


def main(argv):
    if len(argv) < 2 or argv[0] not in ("login", "check", "logout"):
        sys.exit(__doc__)
    action, base = argv[0], argv[1].rstrip("/")
    if action == "login":
        if len(argv) != 3:
            sys.exit(__doc__)
        login(base, argv[2])
    elif action == "logout":
        path = jar_path(base)
        if os.path.exists(path):
            os.remove(path)
        print(f"Session removed: {path}")
    else:
        info = Session(base).raw("GET", "/ws/public/app/info")
        user = info.get("user")
        if not user:
            sys.exit("No valid session: run the login action.")
        print(json.dumps({k: user.get(k) for k in ("login", "name", "group", "lang", "aiChat")}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
