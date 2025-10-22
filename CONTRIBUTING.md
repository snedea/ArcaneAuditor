# 🧙 Contributing to Arcane Auditor

Thank you for your interest in contributing! This project welcomes community collaboration. Please read this guide before submitting changes.

---

## 🌿 Branch Strategy
> ⚠️ Important: Do not create branches or pull requests from `main`. The `main` branch is protected and used only for stable releases. All work must begin from the `develop` branch.

Arcane Auditor uses a protected branching model:

| Branch    | Purpose              | Who Can Merge | How Code Gets In          |
| --------- | -------------------- | ------------- | ------------------------- |
| `develop` | Active development   | Maintainer    | ✅ Pull Requests (PRs)     |
| `main`    | Stable/release‑ready | Maintainer    | ✅ PRs from `develop` only |

> 🚫 **PRs targeting `main` will not be accepted.**
> ✅ **All contributions must target the `develop` branch.**

---

## 🚀 How to Contribute

### 1.) Fork the Repository

```bash
# Fork the repository on GitHub, then clone YOUR fork
git clone https://github.com/<your-username>/ArcaneAuditor.git
cd ArcaneAuditor

# IMPORTANT: Switch to the develop branch
git checkout develop

# Create your feature branch from develop
git checkout -b feature/my-feature-name
```

Use clear, descriptive names:

* `feature/improve-reporting-ui`
* `fix/null-reference-error`
* `docs/add-configuration-guide`

### 2) Make Changes

* Follow the existing structure and style.
* Include tests or examples when applicable.
* Keep PRs focused; one logical change per PR is ideal.

### 3) Commit Cleanly

Use conventional commits:

```bash
git commit -m "feat: add complexity threshold to ScriptNestingLevelRule"
```

Common prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

### 4) Open a Pull Request **to `develop`**

Provide:

* A clear summary of *what* changed and *why*
* Any configuration impact or new flags
* Screenshots for UI changes (when relevant)

The maintainer reviews, may request updates, and merges when ready.

---

## ✅ PR Acceptance Criteria

A PR is more likely to be accepted quickly if it:

* 🎯 Solves a specific, well‑described problem
* 🧠 Preserves clarity, maintainability, and readability
* 🧪 Includes tests or usage examples when appropriate
* 🧩 Avoids breaking changes (or documents them and discusses ahead of time)

---

## 🧠 Proposing Larger Features

Before investing in significant work, please open an **Issue** or **Discussion** to confirm scope and direction. This saves time and ensures alignment with the roadmap.

---

## 🛡️ Code of Conduct

Please be respectful and constructive. Keep discussions professional, technical, and solution‑oriented.

---

## 🔮 Governance

This project currently has a **single maintainer** who reviews contributions, manages releases, and determines long‑term direction to ensure quality and consistency.

---

## 🙌 Thanks!

Every contribution of code, docs, bug reports, or ideas, helps the community build cleaner, more maintainable Workday Extend apps.

If Arcane Auditor helps you, ⭐ star the repo and share it!

> *May your code be clean, your audits arcane, and your complexity ever decreasing.* ✨
