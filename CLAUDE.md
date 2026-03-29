# CLAUDE.md — nov-hub

Plugin dependency resolver for Claude Code. Detects environment, resolves capabilities to providers, auto-selects based on environment probes, generates install plans.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/nov-hub:setup` | Diagnose environment and resolve plugin dependencies |

## Stack

- Python 3.11+, FastMCP, stdlib only (no external deps beyond mcp)
- 8 generic environment probes (OS, shell, binary, port, env, mcp, plugin, file)
- Reads: installed_plugins.json, settings.json, marketplace.json, capabilities/*.json

## Architecture

- `probes.py` — 8 generic environment detection primitives
- `registry.py` — reads marketplace, installed plugins, capability contracts
- `contracts.py` — validates providers against capability schemas (phase 1: name-level)
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
claude --plugin-dir /home/thatcher/projects/nov/projects/plugins/nov-hub
```
