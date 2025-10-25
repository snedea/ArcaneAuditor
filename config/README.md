`<a id="configuration-guide"></a>`

# Arcane Auditor Configuration Guide 📜

[⬅️ Back to Main README](../README.md) | [🧠 Rules Overview](../parser/rules/RULE_BREAKDOWN.md)

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

## 📚 Additional Resources

- [Rule Documentation](../parser/rules/RULE_BREAKDOWN.md) – Detailed rule descriptions
- [Custom Rules Guide](../parser/rules/custom/README.md) – Creating custom validation rules

[⬆️ Back to Top](#configuration-guide)
