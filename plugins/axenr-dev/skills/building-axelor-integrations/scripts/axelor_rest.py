#!/usr/bin/env python3
"""Minimal REST client for an Axelor app (AOP 8), to drive and check an integration under test.

Library (import it from a test script) and small CLI. Standard library only.

    export AXELOR_USER=<login>
    <secret on stdin> | python3 -I axelor_rest.py <base-url> check     # <base-url> = http://<host>:<port>/<context>
    python3 -I axelor_rest.py <base-url> search com.axelor.apps.hr.db.Employee \
        '[{"fieldName":"code","operator":"like","value":"T01"}]' id,name
    python3 -I axelor_rest.py <base-url> action <action-name> <model> <id>

Credentials: the login comes from $AXELOR_USER (or the `user` argument of Axelor()); there is no default account.
The secret is read from standard input when it is piped, from a prompt when stdin is a terminal, or from the
environment variable AXELOR_PASSWORD (acceptable on a disposable environment only: never set it inline in a
command that gets logged). AXELOR_PASSWORD is to be set by the user in their own terminal; never paste the
password into the conversation. Library use: Axelor(base, user, password) falls back to the same variables; a
missing one stops with a clear error.

Login is POST /callback (JSON), checked by the "user" key of GET /ws/public/app/info (a public route: an answer
without that key means no session); every write sends X-CSRF-Token = cookie CSRF-TOKEN.
An Axelor answer can be HTTP 200 with "status": -1: always read the status field (call() raises).
"""
import getpass
import http.cookiejar
import json
import os
import sys
import time
import urllib.request

BATCH = "com.axelor.apps.base.db.Batch"
TRACE = "com.axelor.apps.base.db.TraceBack"


class AxelorError(RuntimeError):
    pass


class Axelor:
    def __init__(self, base, user=None, password=None, timeout=900):
        self.base = base.rstrip("/")
        self.user = user or os.environ.get("AXELOR_USER")
        self.password = password if password is not None else os.environ.get("AXELOR_PASSWORD")
        self.timeout = timeout
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def login(self):
        if not self.user:
            raise AxelorError("no login: set $AXELOR_USER or pass user= to Axelor()")
        if not self.password:
            raise AxelorError("no secret: pipe it on stdin, set AXELOR_PASSWORD (disposable environment only), or pass it to Axelor()")
        self.raw("POST", "/callback", {"username": self.user, "password": self.password})
        # /ws/public/app/info is public and answers without a session too: only its "user" key
        # (added for a logged-in user, AOP 8.2.3 InfoService.info) proves the session is open.
        info = self.raw("GET", "/ws/public/app/info")
        if not (isinstance(info, dict) and info.get("user")):
            raise AxelorError("login failed: GET /ws/public/app/info has no 'user' key")
        if not any(c.name == "CSRF-TOKEN" for c in self.jar):
            raise AxelorError("login failed: no CSRF-TOKEN cookie")
        return self

    def raw(self, method, path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        for c in self.jar:
            if c.name == "CSRF-TOKEN":
                req.add_header("X-CSRF-Token", c.value)
        with self.opener.open(req, timeout=self.timeout) as r:
            body = r.read().decode()
        return json.loads(body) if body else {}

    def call(self, method, path, payload=None):
        res = self.raw(method, path, payload)
        if isinstance(res, dict) and res.get("status", 0) != 0:
            raise AxelorError(f"{method} {path} -> {json.dumps(res)[:800]}")
        return res

    def search(self, model, criteria=None, fields=None, limit=50, offset=0, sort=None):
        payload = {"data": {"criteria": criteria or [], "operator": "and"},
                   "fields": fields or ["id"], "limit": limit, "offset": offset}
        if sort:
            payload["sortBy"] = sort
        return self.call("POST", f"/ws/rest/{model}/search", payload).get("data") or []

    def fetch(self, model, rec_id, fields):
        return (self.call("POST", f"/ws/rest/{model}/{rec_id}/fetch", {"fields": fields}).get("data") or [{}])[0]

    def save(self, model, values):
        """Create (no id) or update (id given; current version fetched when missing)."""
        values = dict(values)
        if values.get("id") and "version" not in values:
            values["version"] = self.fetch(model, values["id"], ["id"]).get("version")
        if values.get("id"):
            res = self.call("POST", f"/ws/rest/{model}/{values['id']}", {"data": values})
        else:
            res = self.call("PUT", f"/ws/rest/{model}", {"data": values})
        return (res.get("data") or [{}])[0]

    def action(self, name, model, context):
        context = dict(context, _model=model)
        return self.call("POST", "/ws/action", {"action": name, "model": model, "data": {"context": context}})

    def wait_batch(self, field, value, after_id=0, timeout=600, poll=2):
        """Wait for the first standard Batch whose <field> (e.g. 'myBatch.id') = value and id > after_id to end."""
        end = time.time() + timeout
        while time.time() < end:
            rows = self.search(BATCH, [{"fieldName": field, "operator": "=", "value": value},
                                       {"fieldName": "id", "operator": ">", "value": after_id}],
                               ["id", "done", "anomaly", "startDate", "endDate", "comments"], limit=5,
                               sort=["-id"])
            if rows and rows[0].get("endDate"):
                return rows[0]
            time.sleep(poll)
        raise AxelorError(f"batch {field}={value} not ended after {timeout} s")

    def traces(self, batch_id, limit=50):
        return self.search(TRACE, [{"fieldName": "batchId", "operator": "=", "value": batch_id}],
                           ["id", "message", "exception", "origin"], limit=limit)

    def last_id(self, model):
        rows = self.search(model, fields=["id"], limit=1, sort=["-id"])
        return rows[0]["id"] if rows else 0


def _secret_from_stdin():
    """Secret for the CLI: the environment first, then piped stdin, then a prompt on a terminal."""
    if os.environ.get("AXELOR_PASSWORD") is not None:
        return None  # Axelor() reads it itself
    if sys.stdin.isatty():
        return getpass.getpass("Axelor secret for %s: " % os.environ.get("AXELOR_USER", "?"))
    return sys.stdin.readline().rstrip("\n")


def main(argv):
    if len(argv) > 1 and argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    if len(argv) < 3:
        sys.exit(__doc__)
    try:
        ax = Axelor(argv[1], password=_secret_from_stdin()).login()
    except AxelorError as exc:
        sys.exit(str(exc))
    cmd = argv[2]
    if cmd == "check":
        menus = ax.raw("GET", "/ws/action/menu/all").get("data") or []
        print(f"login ok, {len(menus)} menus")
    elif cmd == "search":
        crit = json.loads(argv[4]) if len(argv) > 4 else []
        fields = argv[5].split(",") if len(argv) > 5 else ["id"]
        print(json.dumps(ax.search(argv[3], crit, fields), ensure_ascii=False, indent=1))
    elif cmd == "action":
        print(json.dumps(ax.action(argv[3], argv[4], {"id": int(argv[5])}), ensure_ascii=False)[:2000])
    else:
        sys.exit(f"unknown command {cmd}\n{__doc__}")


if __name__ == "__main__":
    main(sys.argv)
