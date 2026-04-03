"""Tests for marketplace.json schema validation.

Validates the real marketplace.json against the expected schema to catch
issues like invalid source types before they break Claude Code's parser.
"""

import json
import os
import re

import pytest

MARKETPLACE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "softwaresoftware-marketplace",
    ".claude-plugin",
    "marketplace.json",
)

VALID_CATEGORIES = {
    "development",
    "research",
    "utilities",
    "provider",
    "framework",
    "toolkit",
}


@pytest.fixture
def marketplace():
    with open(MARKETPLACE_PATH) as f:
        return json.load(f)


@pytest.fixture
def plugins(marketplace):
    return marketplace["plugins"]


class TestMarketplaceTopLevel:
    def test_has_name(self, marketplace):
        assert "name" in marketplace
        assert isinstance(marketplace["name"], str)

    def test_has_plugins(self, marketplace):
        assert "plugins" in marketplace
        assert isinstance(marketplace["plugins"], list)
        assert len(marketplace["plugins"]) > 0

    def test_external_registries_are_valid(self, marketplace):
        registries = marketplace.get("external_registries", {})
        for name, info in registries.items():
            assert "repo" in info, f"External registry '{name}' missing 'repo'"


class TestPluginSource:
    """Source field must always be {"source": "github", "repo": "owner/repo"}.

    Claude Code validates this field and rejects non-github source types.
    The old "source": "registry" format is not supported.
    """

    def test_every_plugin_has_source(self, plugins):
        for p in plugins:
            assert "source" in p, f"Plugin '{p['name']}' missing 'source'"

    def test_source_is_github(self, plugins):
        for p in plugins:
            source = p["source"]
            assert source.get("source") == "github", (
                f"Plugin '{p['name']}' has source type '{source.get('source')}' — "
                f"must be 'github'. Claude Code rejects non-github source types."
            )

    def test_source_has_repo(self, plugins):
        for p in plugins:
            source = p["source"]
            assert "repo" in source, f"Plugin '{p['name']}' source missing 'repo'"
            assert re.match(r"^[\w.-]+/[\w.-]+$", source["repo"]), (
                f"Plugin '{p['name']}' has invalid repo format: '{source['repo']}'"
            )

    def test_no_registry_in_source(self, plugins):
        """The 'registry' field must be at the plugin level, not nested in source."""
        for p in plugins:
            assert "registry" not in p["source"], (
                f"Plugin '{p['name']}' has 'registry' inside source — "
                f"move it to a top-level plugin field instead."
            )


class TestPluginRequiredFields:
    def test_has_name(self, plugins):
        for p in plugins:
            assert "name" in p
            assert isinstance(p["name"], str)
            assert len(p["name"]) > 0

    def test_has_description(self, plugins):
        for p in plugins:
            assert "description" in p, f"Plugin '{p['name']}' missing 'description'"

    def test_has_version(self, plugins):
        for p in plugins:
            assert "version" in p, f"Plugin '{p['name']}' missing 'version'"
            assert re.match(r"^\d+\.\d+\.\d+$", p["version"]), (
                f"Plugin '{p['name']}' version '{p['version']}' is not valid semver"
            )

    def test_has_author(self, plugins):
        for p in plugins:
            assert "author" in p, f"Plugin '{p['name']}' missing 'author'"
            assert "name" in p["author"], f"Plugin '{p['name']}' author missing 'name'"


class TestPluginCapabilityFields:
    def test_requires_is_list(self, plugins):
        for p in plugins:
            assert isinstance(p.get("requires", []), list), (
                f"Plugin '{p['name']}' requires must be a list"
            )

    def test_optional_is_list(self, plugins):
        for p in plugins:
            assert isinstance(p.get("optional", []), list), (
                f"Plugin '{p['name']}' optional must be a list"
            )

    def test_provides_is_list(self, plugins):
        for p in plugins:
            assert isinstance(p.get("provides", []), list), (
                f"Plugin '{p['name']}' provides must be a list"
            )

    def test_environment_is_dict(self, plugins):
        for p in plugins:
            assert isinstance(p.get("environment", {}), dict), (
                f"Plugin '{p['name']}' environment must be a dict"
            )

    def test_valid_category(self, plugins):
        for p in plugins:
            if "category" in p:
                assert p["category"] in VALID_CATEGORIES, (
                    f"Plugin '{p['name']}' has invalid category '{p['category']}'. "
                    f"Valid: {VALID_CATEGORIES}"
                )


class TestPluginExternalConsistency:
    """External plugins must have registry info and valid external_registries references."""

    def test_external_plugins_have_registry(self, plugins):
        for p in plugins:
            if p.get("external"):
                assert "registry" in p, (
                    f"External plugin '{p['name']}' missing 'registry' field"
                )

    def test_registry_references_exist(self, marketplace):
        registries = marketplace.get("external_registries", {})
        for p in marketplace["plugins"]:
            if "registry" in p:
                assert p["registry"] in registries, (
                    f"Plugin '{p['name']}' references registry '{p['registry']}' "
                    f"which is not defined in external_registries"
                )

    def test_non_external_plugins_have_no_registry(self, plugins):
        for p in plugins:
            if not p.get("external"):
                assert "registry" not in p, (
                    f"Non-external plugin '{p['name']}' should not have 'registry' field"
                )


class TestPluginUniqueness:
    def test_unique_names(self, plugins):
        names = [p["name"] for p in plugins]
        duplicates = [n for n in names if names.count(n) > 1]
        assert len(duplicates) == 0, f"Duplicate plugin names: {set(duplicates)}"
