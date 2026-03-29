"""Tests for contracts.py — provider validation against capability contracts."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import contracts


def test_validate_provider_valid(mock_home, marketplace_json, notification_contract):
    result = contracts.validate_provider("notify-linux", "notification")
    assert result["valid"] is True
    assert result["capability"] == "notification"
    assert result["plugin"] == "notify-linux"
    assert result["errors"] == []


def test_validate_provider_no_contract(mock_home, marketplace_json):
    result = contracts.validate_provider("notify-linux", "nonexistent")
    assert result["valid"] is False
    assert "No contract found" in result["errors"][0]


def test_validate_provider_not_in_marketplace(mock_home, marketplace_json, notification_contract):
    result = contracts.validate_provider("nonexistent", "notification")
    assert result["valid"] is False
    assert "not found in marketplace" in result["errors"][0]


def test_validate_provider_doesnt_declare(mock_home, marketplace_json, notification_contract):
    """Cardwatch doesn't provide notification — should fail."""
    result = contracts.validate_provider("cardwatch", "notification")
    assert result["valid"] is False
    assert "does not declare" in result["errors"][0]


def test_validate_all_providers(mock_home, marketplace_json, notification_contract):
    results = contracts.validate_all_providers("notification")
    assert len(results) == 2
    names = [r["plugin"] for r in results]
    assert "notify-linux" in names
    assert "notify-macos" in names
    for r in results:
        assert r["valid"] is True
