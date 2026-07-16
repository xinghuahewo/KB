#!/usr/bin/env python3
"""Serve exported static frontend and proxy BGP KB paths to FastAPI.

This keeps the deployed frontend a static `out/` bundle while avoiding browser
CORS issues: the browser talks to this same-origin server, and only this server
proxies API/source requests to the BGP KB FastAPI service.
"""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import urllib.error
import urllib.request


PROXY_PREFIXES = ("/api/", "/health", "/sources/", "/entities/", "/search")


class StaticProxyHandler(SimpleHTTPRequestHandler):
    backend_base_url = "http://127.0.0.1:8000"

    def do_GET(self):  # noqa: N802
        if self._should_proxy():
            self._proxy()
            return
        super().do_GET()

    def do_POST(self):  # noqa: N802
        if self._should_proxy():
            self._proxy()
            return
        self.send_error(404, "Not found")

    def do_DELETE(self):  # noqa: N802
        if self._should_proxy():
            self._proxy()
            return
        self.send_error(404, "Not found")

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type,x-bgp-client-id")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.end_headers()

    def _should_proxy(self) -> bool:
        return any(self.path == prefix or self.path.startswith(prefix) for prefix in PROXY_PREFIXES)

    def _proxy(self) -> None:
        length = int(self.headers.get("content-length", "0") or "0")
        body = self.rfile.read(length) if length else None
        target = f"{self.backend_base_url.rstrip('/')}{self.path}"
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "content-length", "connection", "accept-encoding"}
        }
        request = urllib.request.Request(target, data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                self.send_response(response.status)
                content_type = response.headers.get("content-type", "")
                for key, value in response.headers.items():
                    if key.lower() in {"connection", "transfer-encoding", "content-length"}:
                        continue
                    self.send_header(key, value)
                if "text/event-stream" in content_type:
                    self.send_header("X-Accel-Buffering", "no")
                    self.end_headers()
                    while True:
                        line = response.readline()
                        if not line:
                            break
                        self.wfile.write(line)
                        self.wfile.flush()
                    return
                payload = response.read()
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as error:
            payload = error.read()
            self.send_response(error.code)
            self.send_header("Content-Type", error.headers.get("content-type", "application/json"))
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as error:  # pragma: no cover - deployment utility
            payload = f'{{"detail":"BGP FastAPI unavailable: {error}"}}'.encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=3001)
    parser.add_argument("--directory", default="out")
    parser.add_argument("--backend", default=os.environ.get("BGP_RAG_BASE_URL", "http://127.0.0.1:8000"))
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        raise SystemExit(f"static directory not found: {directory}")

    StaticProxyHandler.backend_base_url = args.backend
    handler = lambda *handler_args, **handler_kwargs: StaticProxyHandler(  # noqa: E731
        *handler_args, directory=str(directory), **handler_kwargs
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {directory} on http://{args.host}:{args.port}, proxy backend={args.backend}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
