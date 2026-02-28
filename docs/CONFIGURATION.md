`<a id="configuration-guide"></a>`

# Arcane Auditor Configuration Guide 📜

[⬅️ Back to Main README](../README.md) | [🧠 Rules Overview](RULES.md)

All configuration files for Arcane Auditor live under `config/rules/`, organized for clarity and update safety.

---

## 📁 Directory Overview

| Install Type                       | Location                                                      |
| ---------------------------------- | ------------------------------------------------------------- |
| **Desktop App (Windows)**    | `%AppData%\ArcaneAuditor\config\rules\`                     |
| **Desktop App (macOS)**      | `~/Library/Application Support/ArcaneAuditor/config/rules/` |
| **Source / UV Installation** | `./config/rules/` in your project directory                 |

### Desktop App Structure

```
%AppData%\ArcaneAuditor\config\rules\  (Windows)
~/Library/Application Support/ArcaneAuditor/config/rules/  (macOS)
├── teams/        → Shared team/project configs
└── personal/     → Your private overrides
```

> **Note:** Desktop app includes built-in presets (`development`, `production-ready`) that are selectable in the UI but not user-editable files.

### Source Installation Structure

```
./config/rules/
├── presets/      → Built-in app defaults (editable)
├── teams/        → Shared team/project configs
└── personal/     → Your private overrides
```


## 🎯 Configuration Layers

| Layer              | Desktop App                | Source Installation        | Purpose                                  | Priority   |
| ------------------ | -------------------------- | -------------------------- | ---------------------------------------- | ---------- |
| **Preset**   | Built-in (UI only)         | `config/rules/presets/`  | Default app-provided configurations      | 🔹 Lowest  |
| **Team**     | `config/rules/teams/`    | `config/rules/teams/`    | Shared standards for your project        | 🔸 Medium  |
| **Personal** | `config/rules/personal/` | `config/rules/personal/` | Developer overrides and debugging tweaks | 🔺 Highest |

### Built-in Presets

- **`development`** – lenient for daily work (allows console logs, unused code)
- **`production-ready`** – strict for deployment and CI/CD validation

---

## ⚙️ Using Configurations

### 🧰 Command Line

```bash
# Run with a built-in preset
ArcaneAuditorCLI review-app myapp.zip --config development

# Run with a team or personal config
ArcaneAuditorCLI review-app myapp.zip --config my-team-config
```

### 💻 Desktop App Interface

All available configurations are automatically detected and selectable in the UI:

- Built-in Presets
- Team Configurations
- Personal Configurations

---

## 🛡️ Update Safety

| Directory     | Managed By  | Desktop App    | Source Install | Overwritten on Update? | Notes                     |
| ------------- | ----------- | -------------- | -------------- | ---------------------- | ------------------------- |
| `presets/`  | Application | N/A (built-in) | ✅             | ⚠️ Yes               | Updated with each release |
| `teams/`    | Your team   | ✅             | ✅             | 🚫                     | Protected; gitignored     |
| `personal/` | You         | ✅             | ✅             | 🚫                     | Private; never modified   |

> **Desktop App Note:** Configs are stored in platform-specific locations (`%AppData%\ArcaneAuditor\` on Windows, `~/Library/Application Support/ArcaneAuditor/` on macOS) so your edits persist across updates.

---

## 🧩 Creating Custom Configurations

### Team Configuration

**Desktop App:**
Create `%AppData%\ArcaneAuditor\config\rules\teams\my-team-config.json` (Windows)
or `~/Library/Application Support/ArcaneAuditor/config/rules/teams/my-team-config.json` (macOS)

**Source Installation:**

```bash
# Copy a preset as a starting point
cp config/rules/presets/production-ready.json config/rules/teams/my-team-config.json

# Edit it to match your team's standards
ArcaneAuditorCLI review-app myapp.zip --config my-team-config
```

### Personal Configuration

**Desktop App:**
Create `%AppData%\ArcaneAuditor\config\rules\personal\debug-mode.json` (Windows)
or `~/Library/Application Support/ArcaneAuditor/config/rules/personal/debug-mode.json` (macOS)

**Source Installation:**

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
ArcaneAuditorCLI review-app myapp.zip --config debug-mode
```

---

## 🔧 Advanced: Port Configuration

The desktop app runs a local server internally (default port 8080). If you experience port conflicts with other applications, you can configure the port via `web_service_config.json`:

> **Note:** Most users never need to change this. The default port works fine unless you have another application already using port 8080.

### 📁 Location

| Install Type                       | Location                                                    |
| ---------------------------------- | ----------------------------------------------------------- |
| **Desktop App (Windows)**    | `%AppData%\ArcaneAuditor\config\web\`                     |
| **Desktop App (macOS)**      | `~/Library/Application Support/ArcaneAuditor/config/web/` |
| **Source / UV Installation** | `./config/web/` in your project directory                 |

### ⚙️ Configuration Options

```json
{
  "host": "127.0.0.1",
  "port": 8080,
  "log_level": "info"
}
```

| Setting       | Default       | Description                                                 |
| ------------- | ------------- | ----------------------------------------------------------- |
| `host`      | `127.0.0.1` | Server host address                                         |
| `port`      | `8080`      | Server port number                                          |
| `log_level` | `info`      | Logging level (`debug`, `info`, `warning`, `error`) |

### 🔧 Override Methods

**1. Configuration File**

- Desktop App: Create `web_service_config.json` in the location above
- Source: Copy from `config/web/web_service_config.json.sample` and edit

**2. Command Line Arguments (Source Installation Only)**

```bash
uv run web/server.py --port 3000 --host 0.0.0.0
```

---

## 📚 Additional Resources

- [Rule Documentation](RULES.md) – Detailed rule descriptions
- [Custom Rules Guide](CUSTOM_RULES.md) – Creating custom validation rules

[⬆️ Back to Top](#configuration-guide)
