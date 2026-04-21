---
name: config
description: View and edit any softwaresoftware plugin's userConfig values in ~/.claude/settings.json. Works for any installed plugin — reads the plugin's userConfig schema and guides you through changing values.
argument-hint: "[plugin-name]"
---

# softwaresoftware config

Generic configuration manager for any softwaresoftware plugin with a `userConfig` schema.

## Arguments

- Optional plugin name (e.g., `/softwaresoftware:config claude-browser-bridge`).
- If omitted, list all installed plugins that have a `userConfig` schema and ask the user to pick one (or show softwaresoftware's own config by default).

## Why this exists

Claude Code does not re-prompt for `userConfig` values after first enable, and `/softwaresoftware:install` usually skips the prompt entirely. The only supported way to change a plugin's userConfig is to edit `~/.claude/settings.json` directly, then run `/reload-plugins`. This skill does that editing for the user.

## Workflow

### Step 1 — Resolve the target plugin

- If the user supplied a plugin name as an argument, use it.
- If not, enumerate `~/.claude/plugins/cache/*/*/` dirs (each is `<marketplace>/<plugin>/<version>/`). For each, read `.claude-plugin/plugin.json` and check if it has a non-empty `userConfig`. List matches to the user like:
  ```
  Installed plugins with configurable options:
    1. claude-browser-bridge (3.2.2) — 1 setting
    2. notify-slack (1.0.0) — 1 setting
    3. banking-vault (1.0.0) — 5 settings
  Which plugin do you want to configure? (number or name)
  ```
  Then ask the user to pick one.

### Step 2 — Locate the plugin's manifest

Find the plugin.json. Look in order:
1. `~/.claude/plugins/cache/*/<plugin-name>/*/.claude-plugin/plugin.json` — the installed copy. If multiple versions exist, pick the highest semver.
2. If the plugin was loaded via `--plugin-dir`, the user may need to point at a source path. Only fall back to asking the user if step 1 finds nothing.

Read its `userConfig`. If empty or absent, tell the user the plugin has no configurable settings and exit.

### Step 3 — Show current values

Read `~/.claude/settings.json`. Look up `pluginConfigs.<plugin-name>.options.<field>` for each userConfig field. Display a numbered table:

```
Config for <plugin-name>:

  1. <field_name> (<type>)                         [sensitive: yes/no]
     <title> — <description>
     Current: <current_value or "(default: <default>)" or "(not set)">

  2. <field_name> ...
```

**For sensitive fields:** show `Current: ●●●●●● (set)` or `Current: (not set)` — never display the actual stored value, even when reading from settings.json.

### Step 4 — Ask what to change

```
Change a setting? (number, or 'done' to finish)
```

### Step 5 — Prompt for new value (type-aware)

For the selected field:

- **boolean:** prompt `true / false` — reject anything else.
- **string:** prompt the new value. Show the description and default as context.
- **directory:** prompt for a path. Check with `Bash` that the path exists and is a directory. Offer to create it if not, using `mkdir -p`.
- **file:** prompt for a path. Check with `Bash` that the file exists. If it doesn't, confirm before writing the value anyway.
- **number:** prompt numeric input. Validate against `min` / `max` if present.

If `multiple: true`, accept a comma-separated list and store as JSON array.

### Step 6 — Sensitive field handling

If `sensitive: true`:

1. Warn the user clearly:
   ```
   ⚠️  This field is marked sensitive. The documented storage for sensitive
   values is the OS keychain. This skill writes to ~/.claude/settings.json
   instead, which is a plain JSON file on disk.
   
   Proceed anyway? (y / N)
   ```
2. Only write to settings.json if the user confirms.

### Step 7 — Write settings.json

1. Read `~/.claude/settings.json` (or create `{}` if missing).
2. Ensure `pluginConfigs.<plugin-name>.options` exists as an object.
3. Set the new value. Preserve existing keys. Preserve JSON formatting (2-space indent).
4. Use the `Edit` or `Write` tool — read first, write back the full file atomically.

### Step 8 — Confirm + reload

```
✓ Set pluginConfigs.<plugin-name>.options.<field> = <value>

Run /reload-plugins now? (Y / n)
```

If yes, tell the user to run `/reload-plugins` — this skill cannot invoke other slash commands directly, so surface the instruction clearly. Note that some plugins (MCP servers) also need Claude Code restarted to pick up env var changes on the MCP subprocess.

### Step 9 — Loop or exit

After each edit, return to step 3 (show current state). Loop until the user says `done`.

## Edge cases

- **Plugin not found in cache:** ask the user if they loaded it via `--plugin-dir` and want to point at a source path manually.
- **Multiple installed versions:** pick the highest semver silently, but mention which version's schema is being used in the output.
- **Field removed from schema but still in settings.json:** show it as "(orphaned — no longer in schema)" and offer to remove.
- **Required field set to empty:** reject — show the error and re-prompt.
- **Comments in settings.json:** the file is strict JSON. If the user has comments (unusual), warn before editing.

## Rules

- Never display stored sensitive values. Show `●●●●●● (set)` instead.
- Never delete fields the user didn't ask to clear.
- Never touch keys outside `pluginConfigs.<plugin-name>.options`.
- Never restart Claude Code automatically. Only suggest it.
- When no argument is given and the user asks about softwaresoftware's own settings, route to the softwaresoftware plugin specifically (not a generic list).
