import shutil
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts" / "deployment"

pytestmark = pytest.mark.fast


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()


def test_health_check_script_reports_healthy():
    """health_check.sh should succeed when endpoints return 200."""
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    workdir = Path(tempfile.mkdtemp())
    workdir.chmod(0o755)
    try:
        env_file = workdir / ".env"
        env_file.write_text("DEVSYNTH_ENV=testing\n")
        env_file.chmod(0o600)
        url = f"http://127.0.0.1:{port}"
        cmd = f"cd '{workdir}' && {SCRIPTS_DIR / 'health_check.sh'} {url} {url} {url}"
        result = subprocess.run(
            ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "All services are healthy" in result.stdout
    finally:
        server.shutdown()
        thread.join()
        shutil.rmtree(workdir)
