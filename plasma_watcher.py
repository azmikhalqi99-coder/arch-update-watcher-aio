import os
import shutil
import subprocess
import tempfile
from pathlib import Path

APP_NAME = "Arch Update Watcher AIO"
VERSION = "0.1"

SUPPORTED_DISTROS = {
    "arch": {
        "name": "Arch Linux",
        "manager": "pacman",
    },
    "debian": {
        "name": "Debian",
        "manager": "apt",
    },
    "ubuntu": {
        "name": "Ubuntu",
        "manager": "apt",
    },
    "fedora": {
        "name": "Fedora",
        "manager": "dnf",
    },
    "opensuse-leap": {
        "name": "openSUSE Leap",
        "manager": "zypper",
    },
    "opensuse-tumbleweed": {
        "name": "openSUSE Tumbleweed",
        "manager": "zypper",
    },
    "alpine": {
        "name": "Alpine Linux",
        "manager": "apk",
    },
    "void": {
        "name": "Void Linux",
        "manager": "xbps",
    },
}

TERMINALS = [
    ("konsole", ["-e"]),
    ("gnome-terminal", ["--"]),
    ("xfce4-terminal", ["--command"]),
    ("mate-terminal", ["--"]),
    ("qterminal", ["-e"]),
    ("lxterminal", ["-e"]),
    ("kitty", []),
    ("alacritty", ["-e"]),
    ("xterm", ["-e"]),
]


def run_command(command, timeout=120):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = "\n".join(
            part.strip()
            for part in (result.stdout, result.stderr)
            if part.strip()
        )
        return result.returncode, output

    except FileNotFoundError:
        return 127, f"Command not found: {command[0]}"

    except subprocess.TimeoutExpired:
        return 124, "The command timed out."

    except OSError as exc:
        return 1, str(exc)


def show_dialog(kind, message, title=None):
    if not shutil.which("kdialog"):
        print("ERROR: KDialog is not installed.")
        print(message)
        return None

    command = [
        "kdialog",
        "--title",
        title or f"{APP_NAME} v{VERSION}",
    ]

    if kind == "warning":
        command.append("--warningyesno")
    elif kind == "question":
        command.append("--yesno")
    elif kind == "error":
        command.append("--error")
    else:
        command.append("--msgbox")

    command.append(message)

    try:
        result = subprocess.run(command, check=False, timeout=300)
        return result.returncode == 0

    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Dialog error: {exc}")
        return None


def read_os_release():
    info = {}
    path = Path("/etc/os-release")

    if not path.is_file():
        return info

    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            info[key] = value.strip().strip('"').strip("'")

    except OSError:
        return {}

    return info


def detect_distro():
    info = read_os_release()
    distro_id = info.get("ID", "").lower()

    distro = SUPPORTED_DISTROS.get(distro_id)

    if distro is None:
        return None

    return {
        "id": distro_id,
        **distro,
    }


def check_dependencies(distro):
    missing = []

    if not shutil.which("kdialog"):
        missing.append("kdialog")

    manager = distro["manager"]

    required_commands = {
        "pacman": ["pacman"],
        "apt": ["apt"],
        "dnf": ["dnf"],
        "zypper": ["zypper"],
        "apk": ["apk"],
        "xbps": ["xbps-install"],
    }

    for command in required_commands[manager]:
        if not shutil.which(command):
            missing.append(command)

    if manager == "pacman" and not (
        shutil.which("checkupdates") or shutil.which("pacman")
    ):
        missing.append("checkupdates or pacman")

    return missing


def check_updates(distro):
    manager = distro["manager"]

    if manager == "pacman":
        if shutil.which("checkupdates"):
            code, output = run_command(["checkupdates"])

            if code == 2 and not output:
                return True, "No official repository updates available."

            if code != 0:
                return False, (
                    "Could not check Arch Linux updates.\n\n"
                    f"Exit code: {code}\n{output}"
                )

            if not output:
                return True, "No official repository updates available."

            return True, output

        code, output = run_command(["pacman", "-Qu"])

        if code != 0:
            return False, f"pacman failed:\n{output}"

        return True, output or "No updates found."

    if manager == "apt":
        code, output = run_command(
            ["apt", "list", "--upgradable"],
            timeout=180,
        )

        if code != 0:
            return False, f"APT failed:\n{output}"

        packages = [
            line for line in output.splitlines()
            if "/" in line
            and not line.lower().startswith("listing")
            and not line.lower().startswith("warning")
        ]

        return True, "\n".join(packages) if packages else "No updates found."

    if manager == "dnf":
        code, output = run_command(
            ["dnf", "check-update"],
            timeout=180,
        )

        if code == 0:
            return True, output or "No updates found."

        if code == 100:
            return True, output or "Updates are available."

        return False, f"DNF failed (exit code {code}):\n{output}"

    if manager == "zypper":
        code, output = run_command(
            ["zypper", "--non-interactive", "list-updates"],
            timeout=180,
        )

        if code != 0:
            return False, f"Zypper failed:\n{output}"

        if "no updates found" in output.lower():
            return True, "No updates found."

        return True, output or (
            "Zypper completed, but returned no update details."
        )

    if manager == "apk":
        code, output = run_command(
            ["apk", "version", "-l", "<"],
            timeout=180,
        )

        if code != 0:
            return False, f"APK failed:\n{output}"

        return True, output or "No updates found."

    if manager == "xbps":
        code, output = run_command(
            ["xbps-install", "-Mun"],
            timeout=180,
        )

        if code != 0:
            return False, f"XBPS failed:\n{output}"

        return True, output or "No updates found."

    return False, "Unsupported package manager."


def get_upgrade_command(distro):
    manager = distro["manager"]

    if manager == "pacman":
        if shutil.which("yay"):
            return ["yay", "-Syu"]

        return ["sudo", "pacman", "-Syu"]

    if manager == "apt":
        return ["sudo", "apt", "update", "&&", "sudo", "apt", "upgrade"]

    if manager == "dnf":
        return ["sudo", "dnf", "upgrade"]

    if manager == "zypper":
        return ["sudo", "zypper", "update"]

    if manager == "apk":
        return ["sudo", "apk", "update", "&&", "sudo", "apk", "upgrade"]

    if manager == "xbps":
        return ["sudo", "xbps-install", "-Su"]

    return None


def launch_upgrade(distro):
    manager = distro["manager"]

    if manager == "apt":
        shell_command = "sudo apt update && sudo apt upgrade"

    elif manager == "apk":
        shell_command = "sudo apk update && sudo apk upgrade"

    else:
        command = get_upgrade_command(distro)

        if not command:
            show_dialog("error", "No upgrade command is available.")
            return

        shell_command = " ".join(command)

    terminal = next(
        (
            (name, args)
            for name, args in TERMINALS
            if shutil.which(name)
        ),
        None,
    )

    if terminal is None:
        show_dialog(
            "error",
            "No supported terminal emulator was found.\n"
            "Install a supported terminal and try again.",
        )
        return

    terminal_name, terminal_args = terminal

    try:
        temp_dir = Path(tempfile.gettempdir()) / "arch-update-watcher"
        temp_dir.mkdir(parents=True, exist_ok=True)

        script_path = temp_dir / "run-upgrade.sh"

        script_path.write_text(
            "#!/bin/sh\n"
            f"{shell_command}\n"
            'status=$?\n'
            'printf "\\nUpgrade process exited with code %s.\\n" "$status"\n'
            'read -r -p "Press Enter to close this window..."\n'
            'exit "$status"\n',
            encoding="utf-8",
        )

        script_path.chmod(0o700)

        if terminal_name == "xfce4-terminal":
            command = [
                terminal_name,
                "--command",
                f"/bin/sh {str(script_path)!r}",
            ]
        else:
            command = [
                terminal_name,
                *terminal_args,
                "/bin/sh",
                str(script_path),
            ]

        subprocess.Popen(command)

    except OSError as exc:
        show_dialog("error", f"Could not launch the upgrade terminal:\n{exc}")


def main():
    distro = detect_distro()

    if distro is None:
        show_dialog(
            "error",
            "This distribution is not supported by "
            f"{APP_NAME} v{VERSION}.\n\n"
            "Supported: Arch, Debian, Ubuntu, Fedora, "
            "openSUSE Leap/Tumbleweed, Alpine and Void.",
        )
        return

    missing = check_dependencies(distro)

    if missing:
        show_dialog(
            "error",
            "Missing required commands:\n\n"
            + "\n".join(missing)
            + "\n\nInstall the missing dependencies and try again.",
        )
        return

    warnings = [
        (
            "Warning 1 of 3",
            "This application checks package updates using your "
            "distribution's package manager.\n\nContinue?",
        ),
        (
            "Warning 2 of 3",
            "Update checks may contact configured software repositories "
            "and require an internet connection.\n\nContinue?",
        ),
        (
            "Warning 3 of 3",
            "System upgrades can change installed packages and may "
            "require administrator privileges.\n\nContinue?",
        ),
    ]

    for title, message in warnings:
        result = show_dialog("warning", message, title)

        if result is not True:
            return

    show_dialog(
        "info",
        f"Detected distribution: {distro['name']}\n\n"
        "Checking for updates. This may take a while.",
    )

    success, output = check_updates(distro)

    if not success:
        show_dialog("error", output)
        return

    show_dialog(
        "info",
        f"Distribution: {distro['name']}\n\n"
        f"Update check result:\n\n{output}",
        "Update Check Results",
    )

    if output == "No updates found." or (
        "No official repository updates available." in output
    ):
        return

    if show_dialog(
        "question",
        "Would you like to open a terminal and start the system upgrade?\n\n"
        "Review the command before proceeding.",
    ):
        launch_upgrade(distro)


if __name__ == "__main__":
    main()
