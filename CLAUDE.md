# CLAUDE.md — nov-dependency-resolver

Plugin dependency resolver for Claude Code. Detects environment, resolves capabilities to providers, auto-selects based on environment probes, generates install plans.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/nov-dependency-resolver:setup` | Diagnose environment and resolve plugin dependencies |

## Stack

- Python 3.11+, FastMCP, stdlib only (no external deps beyond mcp)
- 8 generic environment probes (OS, shell, binary, port, env, mcp, plugin, file)
- Reads: installed_plugins.json, settings.json, marketplace.json, capabilities/*.json

## Architecture

- `probes.py` — 8 generic environment detection primitives
- `registry.py` — reads marketplace, installed plugins, capability contracts
- `contracts.py` — validates providers against capability contracts (declaration + grants check)
- `resolver.py` — dependency diff engine, provider ranking, install plan generation
- `server.py` — FastMCP server exposing 7 MCP tools

## MCP Tools

- `check_dependencies(plugin_name)` — what's satisfied/missing
- `resolve_capability(capability)` — ranked providers for a capability
- `get_install_plan(plugin_name)` — ordered install list with auto-selected providers
- `verify(plugin_name)` — pass/fail on all deps
- `detect_environment()` — full environment snapshot
- `list_capabilities()` — all contracts from marketplace
- `list_providers(capability)` — providers with match + validation status

## Development

```bash
pip install "mcp[cli]"
python server.py                # run MCP server
make test                       # run tests
```

Install as plugin:
```bash
claude --plugin-dir /home/thatcher/projects/nov/projects/plugins/nov-dependency-resolver
```

## Capability System

Plugins declare dependencies on capabilities — semantic contracts that providers satisfy.

**How it works:** A plugin's marketplace.json entry has `requires: ["notification"]`. nov-dependency-resolver's `check_dependencies` reads this, finds providers that have `provides: ["notification"]`, runs environment probes against each provider's `environment` conditions, and auto-selects the best match.

**Contracts are semantic, not signatures.** Capability contracts describe behavior (input, output, determinism guarantees) and hint registries. They do NOT mandate specific tool names. Providers implement the capability with whatever tool names make sense. Claude handles routing at runtime based on available tools and the contract description.

**Marketplace fields per plugin:** `requires`, `optional`, `provides`, `built_in_capabilities`, `environment` (probe conditions for auto-selection).

**Adding a new capability:** Create `capabilities/<name>.json` in the marketplace repo with behavior description and hints. Create a provider plugin, add it to marketplace.json with `provides` and `environment`. Resolver picks it up automatically.

**Consumer skills use intent, not tool names.** Instead of hardcoding `send_notification(...)`, consumer skills say "Use the notification capability to alert the user with message X and urgency Y." Claude figures out which installed tool satisfies the capability and calls it.

**Dependency preamble — dual discovery.** When a consumer skill checks for missing capabilities, it should present two paths: (1) marketplace providers via `get_install_plan`, and (2) any MCP tools already in Claude's context that could satisfy the capability (e.g., a Gmail MCP satisfying notification). The user chooses, then the skill smoke tests the solution before proceeding.

**Probes are generic** — never plugin-specific. They check: os, shell, binary in PATH, TCP port, env var, MCP server, installed plugin, file exists. New providers = marketplace metadata only.
