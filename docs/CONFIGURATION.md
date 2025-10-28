`<a id="configuration-guide"></a>`

# Arcane Auditor Configuration Guide 📜

[⬅️ Back to Main README](../README.md) | [🧠 Rules Overview](RULES.md)

All configuration files for Arcane Auditor live under `config/rules/`, organized for clarity and update safety.

---

## 📁 Directory Overview

| Install Type                            | Location                                      |
| --------------------------------------- | --------------------------------------------- |
| **Packaged Executable (Windows)** | `%AppData%\ArcaneAuditor\config\rules\`     |
| **Source / UV Installation**      | `./config/rules/` in your project directory |

```
config/rules/
├── presets/      → Built-in app defaults
├── teams/        → Shared team/project configs
└── personal/     → Your private overrides
```

> 🪄 **Upgrade Note (v1.0 → v1.1):**
> UV users -> move configs from:
> `config/personal/` → `config/rules/personal/`
> and
> `config/teams/` → `config/rules/teams/`.

---

## 🎯 Configuration Layers

| Layer              | Path                       | Purpose                                  | Priority   |
| ------------------ | -------------------------- | ---------------------------------------- | ---------- |
| **Preset**   | `config/rules/presets/`  | Default app-provided configurations      | 🔹 Lowest  |
| **Team**     | `config/rules/teams/`    | Shared standards for your project        | 🔸 Medium  |
| **Personal** | `config/rules/personal/` | Developer overrides and debugging tweaks | 🔺 Highest |

### Built-in Presets

- **`development.json`** – lenient for daily work (allows console logs, unused code)
- **`production-ready.json`** – strict for deployment and CI/CD validation

---

## ⚙️ Using Configurations

### 🧰 Command Line

```bash
# Run with a built-in preset
ArcaneAuditorCLI.exe review-app myapp.zip --config development

# Run with a team or personal config
ArcaneAuditorCLI.exe review-app myapp.zip --config my-team-config
```

### 🌐 Web Interface

All available configurations are automatically detected and selectable under:

- Built-in Presets
- Team Configurations
- Personal Configurations

---

## 🛡️ Update Safety

| Directory     | Managed By  | Versioned | Overwritten on Update? | Notes                     |
| ------------- | ----------- | --------- | ---------------------- | ------------------------- |
| `presets/`  | Application | ✅        | ⚠️ Yes               | Updated with each release |
| `teams/`    | Your team   | 🚫        | 🚫                     | Protected; gitignored     |
| `personal/` | You         | 🚫        | 🚫                     | Private; never modified   |

> **Windows Note:** Executable versions store configs in `%AppData%\ArcaneAuditor\config\rules\` so your edits persist across updates.

---

## 🧩 Creating Custom Configurations

### Team Configuration

```bash
# Copy a preset as a starting point
cp config/rules/teams/teams.json.sample config/rules/teams/my-team-config.json

# Edit it to match your team's standards
ArcaneAuditorCLI.exe review-app myapp.zip --config my-team-config
```

### Personal Configuration

```bash
# Create personal override
echo '{
  "rules": {
    "ScriptConsoleLogRule": {
      "enabled": false
    }
  }
}' > config/rules/personal/debug-mode.json

# Use it
ArcaneAuditorCLI.exe review-app myapp.zip --config debug-mode
```

---

## 🌐 Web Service Configuration

The web interface supports configuration via `web_service_config.json`:

### 📁 Location

| Install Type                            | Location                                      |
| --------------------------------------- | --------------------------------------------- |
| **Packaged Executable (Windows)** | `%AppData%\ArcaneAuditor\config\web\`     |
| **Source / UV Installation**      | `./config/web/` in your project directory |

### ⚙️ Configuration Options

```json
{
  "host": "127.0.0.1",
  "port": 8080,
  "open_browser": true,
  "log_level": "info"
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `host` | `127.0.0.1` | Server host address (use `0.0.0.0` for network access) |
| `port` | `8080` | Server port number |
| `open_browser` | `true` | Automatically open browser when server starts |
| `log_level` | `info` | Logging level (`debug`, `info`, `warning`, `error`) |

### 🔧 Override Methods

**1. Command Line Arguments (Highest Priority)**
```bash
# Executable
ArcaneAuditorWeb.exe --port 3000 --host 0.0.0.0 --no-browser

# Source installation
uv run web/server.py --port 3000 --host 0.0.0.0 --no-browser
```

**2. Configuration File**
- Create `web_service_config.json` in the appropriate directory
- Executable users: Automatically created on first run
- Source users: Copy from `config/web/web_service_config.json.sample`

**3. Built-in Defaults (Lowest Priority)**
- Used when no config file exists and no CLI args provided

---

## 📚 Additional Resources

- [Rule Documentation](RULES.md) – Detailed rule descriptions
- [Custom Rules Guide](CUSTOM_RULES.md) – Creating custom validation rules

[⬆️ Back to Top](#configuration-guide)
