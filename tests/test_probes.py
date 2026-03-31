"""Tests for probes.py — generic environment detection primitives."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import probes


def test_probe_os():
    result = probes.probe_os()
    assert result in ("linux", "darwin", "windows")


def test_probe_shell(monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/bash")
    monkeypatch.delenv("PSModulePath", raising=False)
    assert probes.probe_shell() == "bash"


def test_probe_shell_zsh(monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.delenv("PSModulePath", raising=False)
    assert probes.probe_shell() == "zsh"


def test_probe_shell_powershell(monkeypatch):
    monkeypatch.setenv("PSModulePath", "/some/path")
    assert probes.probe_shell() == "powershell"


def test_probe_binary_exists():
    assert probes.probe_binary("python") is True or probes.probe_binary("python3") is True


def test_probe_binary_missing():
    assert probes.probe_binary("definitely_not_a_real_binary_12345") is False


def test_probe_port_closed():
    # Port 1 is almost certainly not listening
    assert probes.probe_port("127.0.0.1", 1, timeout=0.5) is False


def test_probe_env_set(monkeypatch):
    monkeypatch.setenv("NOV_HUB_TEST_VAR", "yes")
    assert probes.probe_env("NOV_HUB_TEST_VAR") is True


def test_probe_env_unset(monkeypatch):
    monkeypatch.delenv("NOV_HUB_TEST_VAR", raising=False)
    assert probes.probe_env("NOV_HUB_TEST_VAR") is False


def test_probe_file_exists(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    assert probes.probe_file(str(f)) is True


def test_probe_file_missing(tmp_path):
    assert probes.probe_file(str(tmp_path / "nope.txt")) is False


def test_probe_plugin(mock_home, installed_plugins):
    assert probes.probe_plugin("notify-linux") is True
    assert probes.probe_plugin("nonexistent") is False


def test_probe_mcp_from_installed(mock_home, installed_plugins):
    assert probes.probe_mcp("notify-linux") is True
    assert probes.probe_mcp("nonexistent") is False


def test_gather_facts_list_values(monkeypatch):
    """List values in environment reqs expand into individual fact entries."""
    monkeypatch.setattr(probes, "probe_os", lambda: "linux")
    env_reqs = [{"os": ["linux", "darwin", "windows"]}]
    facts = probes.gather_facts(env_reqs)
    assert facts["os:linux"] is True
    assert facts["os:darwin"] is False
    assert facts["os:windows"] is False


def test_gather_facts(monkeypatch):
    monkeypatch.delenv("PSModulePath", raising=False)
    env_reqs = [
        {"os": "linux", "binary": "python"},
        {"os": "darwin"},
    ]
    facts = probes.gather_facts(env_reqs)
    assert "os:linux" in facts
    assert "os:darwin" in facts
    assert "binary:python" in facts
    # Each key should be a bool
    for v in facts.values():
        assert isinstance(v, bool)


def test_gather_facts_unknown_probe():
    env_reqs = [{"unknown_probe": "value"}]
    facts = probes.gather_facts(env_reqs)
    assert facts["unknown_probe:value"] is False
