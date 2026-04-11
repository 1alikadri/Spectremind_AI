from __future__ import annotations

import subprocess

from app.tools.wrappers.nmap_wrapper import NmapWrapper


def test_nmap_wrapper_returns_timeout_result(monkeypatch):
    wrapper = NmapWrapper()

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["nmap", "-Pn", "-sV", "test.local"], timeout=120)

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = wrapper.run("test.local")

    assert result["tool"] == "nmap"
    assert result["returncode"] == 124
    assert "timed out" in result["stderr"].lower()