#!/usr/bin/env python3
"""Local demo UI for nishanttyagi-agenttrust — runs real demo, serves dashboard."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
VENV_PY = Path(os.environ.get("AGENTTRUST_PYTHON", sys.executable))
HOST, PORT = "127.0.0.1", 8765
LAST: dict = {"ok": False, "raw": "", "parsed": {}}


def parse_demo(stdout: str) -> dict:
    kv = {}
    for line in stdout.splitlines():
        if "=" in line and not line.startswith(" "):
            k, _, v = line.partition("=")
            if re.fullmatch(r"[a-z0-9_]+", k.strip()):
                kv[k.strip()] = v.strip()
    steps = [
        {
            "id": "payment_deny",
            "title": "Wrong payment ₹1501 → Priya",
            "clause": "Policy deny",
            "ok": kv.get("red_exit") == "1",
            "detail": f"exit {kv.get('red_exit', '?')} · {kv.get('rule_id', '')}",
            "tone": "deny",
        },
        {
            "id": "payment_allow",
            "title": "Sealed ₹1500 → Priya",
            "clause": "Seal + witness",
            "ok": kv.get("green_exit") == "0" and kv.get("witness_matched") == "True",
            "detail": f"exit {kv.get('green_exit', '?')} · {kv.get('adapter_id', '')} · {kv.get('target_resource', '')}",
            "tone": "allow",
        },
        {
            "id": "regression",
            "title": "Replay settled 150100 vs golden blocked",
            "clause": "CI regression",
            "ok": kv.get("regression_exit") == "3",
            "detail": f"exit {kv.get('regression_exit', '?')} · AgentEval compare_runs",
            "tone": "regress",
        },
        {
            "id": "email",
            "title": "Email seal (wrong → right)",
            "clause": "email.sandbox",
            "ok": kv.get("email_red_exit") == "1" and kv.get("email_green_exit") == "0",
            "detail": f"red {kv.get('email_red_exit')} / green {kv.get('email_green_exit')} · {kv.get('email_rule_id', '')}",
            "tone": "allow",
        },
        {
            "id": "delete",
            "title": "data.delete",
            "clause": "No KS adapter",
            "ok": kv.get("delete_seal") == "blocked",
            "detail": f"{kv.get('delete_rule_id')} · seal={kv.get('delete_seal')}",
            "tone": "blocked",
        },
        {
            "id": "deploy",
            "title": "deploy.release",
            "clause": "No KS adapter",
            "ok": kv.get("deploy_seal") == "blocked",
            "detail": f"{kv.get('deploy_rule_id')} · seal={kv.get('deploy_seal')}",
            "tone": "blocked",
        },
    ]
    return {
        "kv": kv,
        "steps": steps,
        "manifest": kv.get("manifest_hash", ""),
        "version": "0.1.0",
    }


def run_demo() -> dict:
    env = os.environ.copy()
    cwd = tempfile.mkdtemp(prefix="agenttrust-ui-")
    proc = subprocess.run(
        [str(VENV_PY), "-m", "agenttrust.demo"],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=120,
    )
    raw = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    parsed = parse_demo(proc.stdout or "")
    chain_src = Path(cwd) / "evidence-pack" / "chain.json"
    chain = None
    report_html = None
    if chain_src.is_file():
        chain = json.loads(chain_src.read_text(encoding="utf-8"))
        out_html = ROOT / "last-report.html"
        r = subprocess.run(
            [str(VENV_PY), "-m", "agenttrust.report", str(chain_src), str(out_html)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if out_html.is_file():
            report_html = out_html.read_text(encoding="utf-8")
    result = {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "raw": raw,
        "parsed": parsed,
        "chain": chain,
        "cwd": cwd,
    }
    if report_html:
        result["report_built"] = True
    LAST.clear()
    LAST.update(result)
    (ROOT / "last-run.json").write_text(json.dumps(result, indent=2)[:200000], encoding="utf-8")
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quieter
        sys.stderr.write("ui %s\n" % (fmt % args))

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/api/last":
            self._send(200, json.dumps(LAST or {"ok": False, "parsed": {"steps": []}}).encode(), "application/json")
            return
        if path == "/last-report.html" and (ROOT / "last-report.html").is_file():
            self._send(200, (ROOT / "last-report.html").read_bytes(), "text/html; charset=utf-8")
            return
        if path.startswith("/static/"):
            f = ROOT / path.lstrip("/")
            if f.is_file():
                self._send(200, f.read_bytes(), "application/octet-stream")
                return
        self._send(404, b"not found", "text/plain")

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/run":
            try:
                result = run_demo()
                self._send(200, json.dumps(result).encode(), "application/json")
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": str(e)}).encode(), "application/json")
            return
        self._send(404, b"not found", "text/plain")


def main():
    if not VENV_PY.is_file():
        print("Missing python at", VENV_PY, file=sys.stderr)
        sys.exit(1)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"AgentTrust UI → http://{HOST}:{PORT}/", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
