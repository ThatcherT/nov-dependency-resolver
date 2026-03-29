"""MCP server for nov-hub — plugin dependency resolver and environment detective."""

from mcp.server.fastmcp import FastMCP

import contracts
import registry
import resolver

mcp = FastMCP("nov-hub")


@mcp.tool()
def check_dependencies(plugin_name: str) -> dict:
    """Check which capabilities a plugin requires and whether they're satisfied.

    Returns satisfied, missing (required), and optional_missing capabilities.
    """
    return resolver.check_dependencies(plugin_name)


@mcp.tool()
def resolve_capability(capability: str) -> list[dict]:
    """Find and rank providers for a capability based on environment match.

    Returns providers sorted by match quality (best match first), with
    environment match details and install status.
    """
    return resolver.resolve(capability)


@mcp.tool()
def get_install_plan(plugin_name: str) -> dict:
    """Generate an ordered install plan for a plugin and its missing dependencies.

    Auto-selects the best provider for each missing capability based on
    environment probes. Returns install order, already satisfied capabilities,
    and any capabilities with no available provider.
    """
    return resolver.get_install_plan(plugin_name)


@mcp.tool()
def verify(plugin_name: str) -> dict:
    """Verify that all of a plugin's required dependencies are satisfied.

    Returns pass/fail with details on what's satisfied and what's missing.
    """
    return resolver.verify(plugin_name)


@mcp.tool()
def detect_environment() -> dict:
    """Detect the current environment — OS, shell, and common binary availability.

    Useful for debugging why a provider wasn't auto-selected.
    """
    return resolver.detect_environment()


@mcp.tool()
def list_capabilities() -> list[dict]:
    """List all capability contracts available in the marketplace.

    Returns the full contract definitions including required tool signatures.
    """
    return registry.list_capability_contracts()


@mcp.tool()
def list_providers(capability: str) -> list[dict]:
    """List all providers for a capability with their environment match status.

    Same as resolve_capability but also includes validation results.
    """
    providers = resolver.resolve(capability)
    validations = contracts.validate_all_providers(capability)
    validation_map = {v["plugin"]: v for v in validations}

    for provider in providers:
        validation = validation_map.get(provider["name"])
        if validation:
            provider["contract_valid"] = validation["valid"]
            provider["contract_errors"] = validation.get("errors", [])

    return providers


if __name__ == "__main__":
    mcp.run()
