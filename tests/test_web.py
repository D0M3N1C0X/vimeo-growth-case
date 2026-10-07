"""The interactive model's JavaScript gives the same numbers as Python."""
import shutil
import subprocess

import pytest

import build_web
import config as C


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_javascript_reproduces_python():
    build_web.write_vectors()
    r = subprocess.run(["node", str(C.ROOT / "tests" / "js" / "check_model.mjs")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "1200 of 1200" in r.stdout
