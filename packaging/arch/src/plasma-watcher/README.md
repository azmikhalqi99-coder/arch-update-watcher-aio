# 🐧 Arch Update Watcher AIO

**Version:** 0.1  
**Type:** Linux Update Checker  
**Language:** Python 3  
**Interface:** KDialog  
**Status:** Early Development 🚧

Arch Update Watcher AIO is a Python-based utility designed to check available system updates and optionally launch a terminal to upgrade packages.

Although originally developed on Arch Linux, the project aims to support several Linux distributions.

> ⚠️ Version 0.1 is an early prototype. Compatibility with every listed distribution and terminal emulator has not yet been verified.

## ✨ Features

- 🐧 Detects supported Linux distributions.
- 📦 Checks available package updates.
- 🖥️ Uses KDialog for graphical dialogs.
- ⚠️ Displays three separate warning dialogs before checking updates.
- 🔍 Uses distribution-specific package management commands.
- 🚀 Offers an option to launch a terminal for system upgrades.
- 🛑 Does not automatically start a system upgrade without user confirmation.
- ❌ Displays an error when the distribution or required dependencies are unsupported.

## 🐧 Supported Distributions

| Distribution | Package Manager | Update Check |
|---|---|---|
| Arch Linux | pacman | `checkupdates` or `pacman -Qu` |
| Debian | APT | `apt list --upgradable` |
| Ubuntu | APT | `apt list --upgradable` |
| Fedora | DNF | `dnf check-update` |
| openSUSE Leap | Zypper | `zypper list-updates` |
| openSUSE Tumbleweed | Zypper | `zypper list-updates` |
| Alpine Linux | APK | `apk version -l '<'` |
| Void Linux | XBPS | `xbps-install -Mun` |

**Compatibility status:** These distributions are intended targets for version 0.1. Testing is required before each can be considered fully supported.

Linux distributions derived from those listed are not automatically guaranteed to work.

## 📋 Requirements

- Python 3
- KDialog
- A supported Linux distribution
- The appropriate package management tools
- Internet access when repository access is required
- A supported terminal emulator for the upgrade workflow

A graphical desktop session must be available for KDialog to display its dialogs.

## 🚀 Getting Started

### 1. Clone the repository

Replace the example repository URL below with the actual Git repository URL.

```bash
git clone <REPOSITORY_URL>
cd plasma-watcher
```

### 2. Check Python syntax

```bash
python -m py_compile plasma_watcher.py
```

If the command completes without an error, Python's syntax check has passed.

### 3. Run the application

```bash
python plasma_watcher.py
```

No automatic system upgrade should be started simply by launching the application.

## ⚠️ Important Notes

### Arch Linux and AUR

The standard Arch update check covers official repository packages.

AUR updates are not included in the `checkupdates` results. Although `yay` may be used for the upgrade workflow when installed, this does not mean AUR updates have been independently checked.

### System upgrades

System upgrades may change installed packages, remove conflicting packages, or require administrator privileges.

Always review the commands and package manager output before confirming an upgrade.

Keep important files backed up and follow your distribution's recommended upgrade procedures.

### Desktop environments

KDialog is associated with KDE applications, but its availability outside KDE depends on installation and desktop session configuration.

Terminal launch behavior can also differ between terminal emulators. Compatibility must be tested rather than assumed.

### Unsupported systems

If a distribution is not explicitly supported, the application should report that it cannot proceed.

Do not assume that sharing the same package manager guarantees compatibility.

## 🛣️ Roadmap

### v0.1 — Initial Prototype

- [x] Initial Python implementation
- [x] Distribution detection structure
- [x] Multi-distribution package manager design
- [x] Three warning dialogs
- [x] Optional upgrade workflow
- [ ] Test on Arch Linux
- [ ] Verify update detection on each supported distribution
- [ ] Test terminal launching across desktop environments
- [ ] Improve error handling and compatibility reporting

### Future Versions

Potential improvements include:

- Better package update summaries
- More reliable detection of package manager errors
- AUR update detection
- Additional terminal emulator support
- More distribution-specific compatibility tests
- Improved graphical interface

## 🤝 Credits

**Project concept and direction:** Human developer  
**Coding assistance:** OpenAI ChatGPT

The project concept, requirements, and development direction were provided by a human developer. ChatGPT was used as a coding assistant during development.

## 📄 License

The project license must match the license file included in the repository. If no license has been selected, the project should not yet claim a specific open-source license.

---

**Arch Update Watcher AIO v0.1**  
*One utility, multiple Linux distributions. 🐧*
