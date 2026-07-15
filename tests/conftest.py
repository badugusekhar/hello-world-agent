import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest


@pytest.fixture(scope="session")
def flask_base_url():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    base = f"http://127.0.0.1:{port}"
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    env = os.environ.copy()
    env.update({
        "FLASK_APP": "web/app.py",
        "FLASK_DEBUG": "0",
        "ANTHROPIC_API_KEY": "",
    })

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "flask", "run",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--no-reload",
            "--no-debugger",
        ],
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    deadline = time.monotonic() + 20.0
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            pytest.fail(
                f"Flask exited early (rc={proc.returncode})\n"
                f"stdout:\n{stdout.decode(errors='replace')}\n"
                f"stderr:\n{stderr.decode(errors='replace')}"
            )
        try:
            urllib.request.urlopen(base, timeout=1)
            break
        except Exception:
            time.sleep(0.25)
    else:
        proc.terminate()
        pytest.fail(f"Flask did not start within 20 s on port {port}")

    yield base

    proc.terminate()
    try:
        proc.wait(5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def base_url(flask_base_url):
    return flask_base_url
