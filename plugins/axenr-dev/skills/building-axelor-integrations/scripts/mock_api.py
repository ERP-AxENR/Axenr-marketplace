#!/usr/bin/env python3
"""Generic emulator of a third-party HTTP API, built from its public documentation.

    python3 -I mock_api.py <scenario.py> <port> <journal.jsonl>

The scenario file (plain Python) declares the routes the connector calls, with the response shapes
the documentation shows (cite the doc URL next to each route):

    ROUTES = [("GET", r"/api/v1/users", get_users), ("POST", r"/api/v1/items", create_item)]
    SCENARIOS = {"base": {...}, "edge": {...}}   # optional data sets, switched at runtime
    def get_users(req): return 200, {"data": paginate(DATA()["users"], req)}

Each handler receives a Request (method, path, query dict, json body, headers, match groups,
scenario name) and returns (status, body) or (status, body, headers).

Admin routes (never called by the connector):
    POST /__admin/scenario  {"name": "edge"}                        switch the data set
    POST /__admin/inject    {"path": "regex", "status": 429, "count": 2}   fail the next calls
    POST /__admin/inject    {"path": "regex", "hang": 30, "count": 1}      answer after 30 s
    GET  /__admin/journal   the calls received so far

Every call is appended to the journal (JSON lines, Authorization redacted): the journal is the proof
of what the connector really sends. Stop it with `kill <pid>` found by
`pgrep -f "^python3 -I .*mock_api.py"` -- a `pkill -f mock_api` also kills the shell that runs it.
"""
import importlib.util
import json
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

STATE = {"scenario": "base", "inject": []}
LOCK = threading.RLock()  # never held while sleeping or writing to the socket


class Request:
    def __init__(self, handler, body, groups):
        u = urlparse(handler.path)
        self.method, self.path = handler.command, u.path
        self.query = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(u.query).items()}
        self.headers, self.json, self.groups = handler.headers, body, groups
        self.scenario = STATE["scenario"]

    def arg(self, name, default=None):
        return self.query.get(name, default)


def paginate(items, req, offset_param="offset", limit_param="limit", default_limit=100):
    """Slice a list as the API pages it; override in the scenario when the API pages differently."""
    offset = int(req.arg(offset_param, 0) or 0)
    limit = int(req.arg(limit_param, default_limit) or default_limit)
    return items[offset:offset + limit]


def load(path):
    spec = importlib.util.spec_from_file_location("scenario", path)
    mod = importlib.util.module_from_spec(spec)
    mod.paginate = paginate
    spec.loader.exec_module(mod)
    return mod


def take_injection(path):
    with LOCK:
        for rule in STATE["inject"]:
            if rule.get("count", 0) > 0 and re.search(rule["path"], path):
                rule["count"] -= 1
                return dict(rule)
    return None


def make_handler(scenario_mod, journal_path):
    routes = [(m, re.compile(p + r"/?$"), fn) for m, p, fn in scenario_mod.ROUTES]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n).decode() if n else ""
            try:
                return json.loads(raw) if raw else None
            except ValueError:
                return raw

        def _send(self, status, body, headers=None, request_body=None):
            data = body if isinstance(body, (bytes, str)) else json.dumps(body, ensure_ascii=False)
            data = data.encode() if isinstance(data, str) else data
            entry = {"t_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "method": self.command, "path": self.path,
                     "status": status, "body": request_body,
                     "auth": "present" if self.headers.get("Authorization") else "absent"}
            with LOCK, open(journal_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self.send_response(status)
            self.send_header("Content-Type", (headers or {}).pop("Content-Type", "application/json"))
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _admin(self, body):
            p = urlparse(self.path).path
            if p == "/__admin/scenario" and self.command == "POST":
                with LOCK:
                    STATE["scenario"] = (body or {}).get("name", "base")
                return self._send(200, {"scenario": STATE["scenario"]})
            if p == "/__admin/inject" and self.command == "POST":
                with LOCK:
                    STATE["inject"].append(dict(body or {}))
                return self._send(200, {"inject": STATE["inject"]})
            if p == "/__admin/journal":
                with open(journal_path, encoding="utf-8") as f:
                    return self._send(200, [json.loads(line) for line in f if line.strip()])
            return self._send(404, {"detail": "unknown admin route"})

        def _dispatch(self):
            body = self._body() if self.command in ("POST", "PUT", "PATCH") else None
            path = urlparse(self.path).path
            if path.startswith("/__admin/"):
                return self._admin(body)
            rule = take_injection(path)
            if rule and rule.get("hang"):
                time.sleep(float(rule["hang"]))
            if rule and rule.get("status"):
                return self._send(int(rule["status"]), rule.get("body", {"detail": "injected"}), None, body)
            for method, regex, fn in routes:
                m = regex.match(path)
                if method == self.command and m:
                    try:
                        out = fn(Request(self, body, m.groups()))
                    except Exception as e:  # a scenario bug must show up in the journal, not hang the call
                        return self._send(500, {"detail": f"emulator error: {e!r}"}, None, body)
                    status, payload = out[0], out[1]
                    return self._send(status, payload, dict(out[2]) if len(out) > 2 else None, body)
            return self._send(404, {"detail": f"route not emulated: {self.command} {path}"}, None, body)

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _dispatch

    return Handler


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    mod = load(sys.argv[1])
    open(sys.argv[3], "a").close()
    server = ThreadingHTTPServer(("127.0.0.1", int(sys.argv[2])), make_handler(mod, sys.argv[3]))
    server.daemon_threads = True
    print(f"mock on 127.0.0.1:{sys.argv[2]}, {len(mod.ROUTES)} routes, journal {sys.argv[3]}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
