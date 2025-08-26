import shutil
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts" / "deployment"


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()


class _FailHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(500)
        self.end_headers()


@pytest.mark.fast
def test_health_check_script_reports_healthy():
    """health_check.sh should succeed when endpoints return 200.

    ReqID: DEP-02"""
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


@pytest.mark.fast
def test_health_check_script_rejects_root_user():
    """health_check.sh should refuse to run as root.

    ReqID: CON-04"""
    workdir = Path(tempfile.mkdtemp())
    workdir.chmod(0o755)
    try:
        result = subprocess.run(
            [str(SCRIPTS_DIR / "health_check.sh")],
            cwd=workdir,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Please run this script as a non-root user." in result.stderr
    finally:
        shutil.rmtree(workdir)


@pytest.mark.fast
def test_health_check_script_requires_env_file():
    """health_check.sh should fail when the env file is missing.

    ReqID: DEP-04"""
    workdir = Path(tempfile.mkdtemp())
    workdir.chmod(0o755)
    try:
        cmd = f"cd '{workdir}' && {SCRIPTS_DIR / 'health_check.sh'}"
        result = subprocess.run(
            ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Missing environment file" in result.stderr
    finally:
        shutil.rmtree(workdir)


@pytest.mark.fast
def test_health_check_script_requires_strict_permissions():
    """health_check.sh should enforce 600 permissions on the env file.

    ReqID: CON-04"""
    workdir = Path(tempfile.mkdtemp())
    workdir.chmod(0o755)
    try:
        env_file = workdir / ".env"
        env_file.write_text("DEVSYNTH_ENV=testing\n")
        env_file.chmod(0o644)
        cmd = f"cd '{workdir}' && {SCRIPTS_DIR / 'health_check.sh'}"
        result = subprocess.run(
            ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "must have 600 permissions" in result.stderr
    finally:
        shutil.rmtree(workdir)


@pytest.mark.fast
def test_health_check_script_rejects_invalid_url():
    """health_check.sh should validate provided URLs.

    ReqID: DEP-03"""
    workdir = Path(tempfile.mkdtemp())
    workdir.chmod(0o755)
    try:
        env_file = workdir / ".env"
        env_file.write_text("DEVSYNTH_ENV=testing\n")
        env_file.chmod(0o600)
        cmd = (
            f"cd '{workdir}' && {SCRIPTS_DIR / 'health_check.sh'} not-a-url"
            " not-a-url not-a-url"
        )
        result = subprocess.run(
            ["su", "nobody", "-s", "/bin/bash", "-c", cmd],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Invalid URL" in result.stderr
    finally:
        shutil.rmtree(workdir)


@pytest.mark.fast
def test_health_check_script_fails_on_unhealthy_endpoint():
    """health_check.sh should report failure when an endpoint is unhealthy.

    ReqID: DEP-01"""
    server = HTTPServer(("127.0.0.1", 0), _FailHandler)
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
        assert result.returncode != 0
        assert f"Health check failed for {url}" in result.stderr
    finally:
        server.shutdown()
        thread.join()
        shutil.rmtree(workdir)
