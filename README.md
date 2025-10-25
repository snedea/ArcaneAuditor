![Arcane Auditor Logo](assets/arcane-auditor-logo.png)

*A mystical code review tool for Workday Extend applications.*

> ⚗️ **Validate. Visualize. Improve.** — PMD, Pod, and Script compliance with wizard-level precision.

![Version](https://img.shields.io/badge/version-1.1.0-blue?style=for-the-badge)
[![Download](https://img.shields.io/badge/🚀-Download_Latest-orange?style=for-the-badge)](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases)

---

## ✨ Overview

Arcane Auditor channels ancient wisdom through **42 validation rules** to reveal subtle code quality issues invisible to compilers but obvious to master developers.

It analyzes:

- **📄 PMD** – Page definitions with embedded scripts and endpoints  
- **🧩 Pod** – Reusable widget components  
- **📜 Script** – Function libraries and utilities  
- **🏗️ AMD / 🔒 SMD** – Application and security manifests  

**Key Traits**

- 🧙 Always-ready reviewer that understands Extend best practices  
- 🔍 Precise line-level detection  
- 🧠 Context-aware validation (cross-file and cross-field)  
- ⚙️ Update-safe configuration layering  
- 📊 Multiple output formats: Console, Excel, JSON, and Web

---

## 🚀 Quick Start — *No Install Required (Windows Only — macOS coming soon!)*


**New in v1.1:** Arcane Auditor now ships as a self-contained executable.  
No Python, no setup — just download and run.

> 🍎 **macOS Users:** Executables are Windows-only for now. Use the [Developer Installation](#-developer-installation-optional) section below for macOS setup.

### 1. Download
Get the latest build from [GitHub Releases](https://github.com/Developers-and-Dragons/ArcaneAuditor/releases):

- `ArcaneAuditorWeb.exe` → **Web Interface (Recommended)**
- `ArcaneAuditorCLI.exe` → **Command Line Interface**

### 2. Run

- **Web:** double-click `ArcaneAuditorWeb.exe` → your browser opens automatically  
- **CLI:**  
  ```bash
  ArcaneAuditorCLI.exe review-app myapp.zip
  ```

### 3. Review
Upload a ZIP of your Extend app or drop individual `.pmd`, `.pod`, `.script`, `.amd`, `.smd` files.  
Results appear instantly — download Excel or JSON reports as needed.

**Includes:** all 42 rules, all configuration presets, Excel export, and web UI — fully self-contained.

> 💡 **Windows SmartScreen Notice**<br>
> When running Arcane Auditor for the first time, Windows may still show a “Windows protected your PC” warning.<br>
> Even after code signing, SmartScreen continues to display this notice until Microsoft’s reputation system marks the app as trusted — based on successful downloads and launches over time.
>
> ✅ Your safety is not at risk.<br>
> Click More info → Run anyway to proceed.
>
> Once enough users run the signed version without issues, SmartScreen will automatically stop showing this message.

---

## 🧩 Interfaces at a Glance

| Interface | Best For | Launch | Highlights |
|------------|-----------|---------|-------------|
| 🌐 **Web** | Most users | `ArcaneAuditorWeb.exe` | Drag-and-drop files, auto-browser, dark/light themes |
| ⚔️ **CLI** | CI/CD and power users | `ArcaneAuditorCLI.exe review-app myapp.zip` | Scriptable, supports Excel/JSON output |
| 🧰 **Source (optional)** | Developers extending rules | `uv run main.py ...` | Full source access and development setup |

<details>
<summary>📸 Screenshots</summary>

**Dark Mode:**  
![Web Interface - Dark Mode](assets/results-dark.png)

**Light Mode:**
![Web Interface - Light Mode](assets/results-light.png)

**Issues View:**
![Issues View](assets/issues-dark.png)

**Issues Breakdown:**
![Issues Breakdown](assets/details-dark.png)

**Configuration View:**
![Configuration View](assets/config-dark.png)
</details>

---

## ⚙️ Configuration

Arcane Auditor uses a **layered, update-safe configuration** system:

1. **Built-in Presets**
   - `development` — lenient, allows console logs / work-in-progress code  
   - `production-ready` — strict, deployment-grade validation  
2. **Team Configuration** (`%AppData%\ArcaneAuditor\config\rules\teams\`)
3. **Personal Configuration** (`%AppData%\ArcaneAuditor\config\rules\personal\`)
4. **Command-line overrides** (highest priority)

**Example personal config:**
```json
{
  "rules": {
    "ScriptConsoleLogRule": { "enabled": false },
    "ScriptLongBlockRule": {
      "custom_settings": { "max_lines": 50, "skip_comments": true }
    }
  }
}
```

Use via CLI:
```bash
ArcaneAuditorCLI.exe review-app myapp.zip --config my-config
```

### 🌐 Web Service Configuration

The web interface supports configuration via `web_service_config.json`:

**Executable users:** `%AppData%\ArcaneAuditor\config\web\web_service_config.json`  
**Source users:** `config/web/web_service_config.json`

```json
{
  "host": "127.0.0.1",
  "port": 8080,
  "open_browser": true,
  "log_level": "info"
}
```

> 📖 Full reference: [Configuration Guide](config/README.md)

---

## 🧠 Validation Rules

Arcane Auditor enforces **42 rules** across two realms:

### 📜 Script Quality (23)
Complexity limits • long-function checks • unused variables/functions • naming • magic numbers • descriptive parameters

### 🏗️ Structural Integrity (19)
Widget IDs • endpoint failOnStatusCodes • naming conventions • file structure • security domain checks

> 📖 See full details: [Rule Documentation](parser/rules/RULE_BREAKDOWN.md)

---

## ⚡ Advanced Usage

<details>
<summary>🤖 CI/CD Integration</summary>

| Exit Code | Meaning | Use Case |
|------------|----------|----------|
| **0** | ✅ Clean | No ACTION issues |
| **1** | ⚠️ Issues Found | ACTION issues present |
| **2** | ❌ Usage Error | Invalid files/config |
| **3** | 💥 Runtime Error | Analysis failure |

Example:
```bash
ArcaneAuditorCLI.exe review-app myapp.zip --format json --output report.json
if %ERRORLEVEL% EQU 1 exit /b 1
```
</details>

<details>
<summary>🧩 Context Awareness</summary>

Arcane Auditor detects missing files and adjusts validation scope automatically:

- **Complete** when PMD + AMD + SMD provided  
- **Partial** when some missing (rules skipped with clear indicators)  
- Reports list skipped or partial rules and suggest required files.

</details>

---

## 🧑‍💻 Developer Installation (Optional)

For those extending Arcane Auditor or building from source:

```bash
# Clone and install dependencies
git clone https://github.com/Developers-and-Dragons/ArcaneAuditor.git
cd ArcaneAuditor
uv sync

# Run tests
uv run pytest
```

**UV** automatically installs and manages Python — no manual setup required.  
More details: [UV Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)

---

## 🧙 Contributing

Contributions are welcome!  
Submit pull requests against the **`develop`** branch.

> 📖 See [CONTRIBUTING.md](CONTRIBUTING.md) and [Custom Rules Guide](parser/rules/custom/README.md)

---

## 📚 Documentation

- [Rule Documentation](parser/rules/RULE_BREAKDOWN.md)  
- [Configuration Guide](config/README.md)  
- [Custom Rules Guide](parser/rules/custom/README.md)  
- [Web Service Scripts](WEB_SERVICE_SCRIPTS.md)

---

## 📄 License

Licensed under the **MIT License** — see [LICENSE](LICENSE).

---

⭐ **If Arcane Auditor helps you, star the repo and share the magic!**  
*May the Weave guide your code to perfection.* ✨
