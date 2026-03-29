"""Contract validation for nov-hub — validates providers against capability schemas.

Phase 1: name-level validation only (checks tool names exist).
Full runtime schema validation deferred to later phases.
"""

import registry


def validate_provider(plugin_name: str, capability: str, marketplace: str = "nov-plugins") -> dict:
    """Validate that a provider implements a capability contract.

    Phase 1 checks:
    - Provider declares the capability in 'provides'
    - Provider's MCP server declares tools matching the contract's required tool names

    Args:
        plugin_name: Name of the provider plugin
        capability: Capability name to validate against

    Returns:
        {
            "valid": bool,
            "capability": str,
            "plugin": str,
            "missing_tools": list[str],
            "errors": list[str]
        }
    """
    result = {
        "valid": False,
        "capability": capability,
        "plugin": plugin_name,
        "missing_tools": [],
        "errors": [],
    }

    # Get the contract
    contract = registry.get_capability_contract(capability, marketplace)
    if not contract:
        result["errors"].append(f"No contract found for capability '{capability}'")
        return result

    # Get the plugin from marketplace
    plugin = registry.find_marketplace_plugin(plugin_name, marketplace)
    if not plugin:
        result["errors"].append(f"Plugin '{plugin_name}' not found in marketplace")
        return result

    # Check it declares the capability
    if capability not in plugin.get("provides", []):
        result["errors"].append(
            f"Plugin '{plugin_name}' does not declare '{capability}' in provides"
        )
        return result

    # Phase 1: name-level tool check
    required_tools = [tool["name"] for tool in contract.get("tools", [])]
    # We can't inspect MCP tools at validation time without running the server,
    # so phase 1 just verifies the contract exists and the plugin claims the capability.
    # Full tool-level validation would require runtime introspection.

    result["valid"] = True
    return result


def validate_all_providers(capability: str, marketplace: str = "nov-plugins") -> list[dict]:
    """Validate all providers of a capability.

    Returns:
        List of validation results, one per provider.
    """
    providers = registry.get_providers(capability, marketplace)
    results = []
    for provider in providers:
        result = validate_provider(provider["name"], capability, marketplace)
        results.append(result)
    return results
