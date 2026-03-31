"""Contract validation for nov-dependency-resolver — validates providers against capability contracts.

Contracts are semantic — they describe behavior, not tool signatures.
Validation checks that providers declare the capability and a contract exists.
Claude handles tool routing at runtime based on available tools.
"""

import registry


def validate_provider(plugin_name: str, capability: str, marketplace: str = "claude-plugins-nov") -> dict:
    """Validate that a provider can satisfy a capability contract.

    Checks:
    - Provider declares the capability in 'provides'
    - A capability contract exists

    Args:
        plugin_name: Name of the provider plugin
        capability: Capability name to validate against

    Returns:
        {
            "valid": bool,
            "capability": str,
            "plugin": str,
            "errors": list[str]
        }
    """
    result = {
        "valid": False,
        "capability": capability,
        "plugin": plugin_name,
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

    result["valid"] = True
    return result


def validate_all_providers(capability: str, marketplace: str = "claude-plugins-nov") -> list[dict]:
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
