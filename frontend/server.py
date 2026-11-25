#!/usr/bin/env python3
"""Static client origin. This is a different origin from the API on port 5001."""

import os
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 5173
ROOT = Path(__file__).resolve().parent


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


class DualStackServer(ThreadingHTTPServer):
    """Listen on IPv6 and IPv4. Browsers often open localhost as ::1 first."""

    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


if __name__ == "__main__":
    os.chdir(ROOT)
    server = DualStackServer(("::", PORT), Handler)
    print(f"MotionMind client at http://localhost:{PORT}", flush=True)
    server.serve_forever()
