#!/usr/bin/env python3
"""Arch Update Watcher AIO: cautious update checker for several Linux distributions."""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

APP_NAME = "Arch Update Watcher AIO"
VERSION = "0.2.1"
GITHUB_REPO = "azmikhalqi99-coder/arch-update-watcher-aio"
API_TIMEOUT = 5

MIN_INTERVAL = 0.1
MAX_INTERVAL = 10.0
MAX_SPAM = 10

SUPPORTED_LANGUAGES = {
    "id": "Bahasa Indonesia",
    "en": "English",
    "fr": "Français",
    "it": "Italiano",
}
DEFAULT_LANGUAGE = "id"
CONFIG_DIR = Path.home() / ".config" / "arch-update-watcher"
CONFIG_FILE = CONFIG_DIR / "language"
CURRENT_LANGUAGE = DEFAULT_LANGUAGE

# Internal sentinel. Never translate, never display. Use t("no_updates") for display.
NO_UPDATES = "__AW_AIO_NO_UPDATES__"

LOCALES = {
    "id": {
        "language_header": "Bahasa yang tersedia:",
        "default": "(default)",
        "language_saved": "Bahasa disimpan: {language}",
        "bad_language": "Bahasa tidak didukung: {language}",
        "unsupported": "Distribusi Linux ini belum didukung.",
        "supported": "Distribusi yang didukung: Arch, Debian, Ubuntu, Fedora, openSUSE Leap/Tumbleweed, Alpine, Void.",
        "missing": "Perintah yang diperlukan belum tersedia:",
        "install_deps": "Pasang dependensi yang diperlukan, lalu coba lagi.",
        "kdialog_missing": "KDialog tidak terpasang. Pesan ditampilkan di terminal.",
        "command_missing": "Perintah tidak ditemukan: {command}",
        "timeout": "Perintah melewati batas waktu.",
        "system_error": "Kesalahan sistem: {error}",
        "dialog_error": "Kesalahan dialog: {error}",
        "warning_title": "Peringatan {n}/3",
        "warning1": "Aplikasi ini memeriksa pembaruan menggunakan pengelola paket distribusimu.\n\nLanjutkan?",
        "warning2": "Pemeriksaan dapat menghubungi repositori perangkat lunak dan memerlukan internet.\n\nLanjutkan?",
        "warning3": "Upgrade sistem dapat mengubah paket terpasang dan memerlukan hak administrator.\n\nLanjutkan?",
        "detected": "Distribusi terdeteksi: {distro}",
        "checking": "Memeriksa pembaruan. Proses ini mungkin memerlukan waktu.",
        "results": "Hasil pemeriksaan pembaruan",
        "no_updates": "Tidak ada pembaruan.",
        "check_failed": "Pemeriksaan pembaruan gagal.",
        "upgrade_prompt": "Buka terminal dan mulai upgrade sistem?",
        "review_command": "Periksa perintah sebelum melanjutkan.",
        "no_upgrade": "Perintah upgrade tidak tersedia.",
        "no_terminal": "Emulator terminal yang didukung tidak ditemukan.\nPasang terminal yang didukung, lalu coba lagi.",
        "upgrade_launch_failed": "Tidak dapat membuka terminal upgrade:\n{error}",
        "upgrade_finished": "Proses upgrade selesai dengan kode {status}.",
        "press_enter": "Tekan Enter untuk menutup jendela ini...",
        "notify_updates": "Pembaruan tersedia",
        "notify_none": "Tidak ada pembaruan yang tersedia.",
        "notify_failed": "Pemeriksaan pembaruan gagal.",
        "spam_limit": "Nilai --spam harus antara 1 dan {max}.",
        "spam_requires_egg": "--spam memerlukan --easter-egg atau --easter-egg-id.",
        "interval_limit": "Interval harus antara {min} dan {max} detik.",
        "pacman_fail": "Gagal memeriksa pembaruan Arch.\nKode keluar: {code}\n{output}",
        "pacman_qu_fail": "pacman -Qu gagal:\n{output}",
        "apt_fail": "APT gagal (kode keluar {code}):\n{output}",
        "dnf_fail": "DNF gagal (kode keluar {code}):\n{output}",
        "zypper_fail": "Zypper gagal (kode keluar {code}):\n{output}",
        "apk_fail": "APK gagal (kode keluar {code}):\n{output}",
        "xbps_fail": "XBPS gagal (kode keluar {code}):\n{output}",
        "updates_available_generic": "Pembaruan tersedia.",
        "new_release_title": "Rilis baru tersedia",
        "new_release_body": "Versi terpasang: {installed}\nRilis terbaru GitHub: {latest}\n\nKunjungi https://github.com/{repo}/releases untuk meninjau.",
    },
    "en": {
        "language_header": "Available languages:",
        "default": "(default)",
        "language_saved": "Language saved: {language}",
        "bad_language": "Unsupported language: {language}",
        "unsupported": "This Linux distribution is not supported.",
        "supported": "Supported distributions: Arch, Debian, Ubuntu, Fedora, openSUSE Leap/Tumbleweed, Alpine, Void.",
        "missing": "Missing required commands:",
        "install_deps": "Install the required dependencies and try again.",
        "kdialog_missing": "KDialog is not installed. Showing the message in the terminal.",
        "command_missing": "Command not found: {command}",
        "timeout": "The command timed out.",
        "system_error": "System error: {error}",
        "dialog_error": "Dialog error: {error}",
        "warning_title": "Warning {n} of 3",
        "warning1": "This application checks updates using your distribution's package manager.\n\nContinue?",
        "warning2": "Update checks may contact software repositories and require internet access.\n\nContinue?",
        "warning3": "System upgrades can change installed packages and may require administrator privileges.\n\nContinue?",
        "detected": "Detected distribution: {distro}",
        "checking": "Checking for updates. This may take a while.",
        "results": "Update Check Results",
        "no_updates": "No updates found.",
        "check_failed": "The update check failed.",
        "upgrade_prompt": "Open a terminal and start the system upgrade?",
        "review_command": "Review the command before proceeding.",
        "no_upgrade": "No upgrade command is available.",
        "no_terminal": "No supported terminal emulator was found.\nInstall a supported terminal and try again.",
        "upgrade_launch_failed": "Could not launch the upgrade terminal:\n{error}",
        "upgrade_finished": "Upgrade process finished with code {status}.",
        "press_enter": "Press Enter to close this window...",
        "notify_updates": "Updates available",
        "notify_none": "No updates are available.",
        "notify_failed": "The update check failed.",
        "spam_limit": "--spam must be between 1 and {max}.",
        "spam_requires_egg": "--spam requires --easter-egg or --easter-egg-id.",
        "interval_limit": "Interval must be between {min} and {max} seconds.",
        "pacman_fail": "Could not check Arch updates.\nExit code: {code}\n{output}",
        "pacman_qu_fail": "pacman -Qu failed:\n{output}",
        "apt_fail": "APT failed (exit code {code}):\n{output}",
        "dnf_fail": "DNF failed (exit code {code}):\n{output}",
        "zypper_fail": "Zypper failed (exit code {code}):\n{output}",
        "apk_fail": "APK failed (exit code {code}):\n{output}",
        "xbps_fail": "XBPS failed (exit code {code}):\n{output}",
        "updates_available_generic": "Updates are available.",
        "new_release_title": "New release available",
        "new_release_body": "Installed version: {installed}\nLatest GitHub release: {latest}\n\nVisit https://github.com/{repo}/releases to review it.",
    },
    "fr": {
        "language_header": "Langues disponibles :",
        "default": "(par défaut)",
        "language_saved": "Langue enregistrée : {language}",
        "bad_language": "Langue non prise en charge : {language}",
        "unsupported": "Cette distribution Linux n'est pas prise en charge.",
        "supported": "Distributions prises en charge : Arch, Debian, Ubuntu, Fedora, openSUSE Leap/Tumbleweed, Alpine, Void.",
        "missing": "Commandes requises manquantes :",
        "install_deps": "Installez les dépendances requises, puis réessayez.",
        "kdialog_missing": "KDialog n'est pas installé. Le message sera affiché dans le terminal.",
        "command_missing": "Commande introuvable : {command}",
        "timeout": "La commande a dépassé le délai autorisé.",
        "system_error": "Erreur système : {error}",
        "dialog_error": "Erreur de dialogue : {error}",
        "warning_title": "Avertissement {n}/3",
        "warning1": "Cette application vérifie les mises à jour avec le gestionnaire de paquets de votre distribution.\n\nContinuer ?",
        "warning2": "La vérification peut contacter les dépôts logiciels et nécessite une connexion Internet.\n\nContinuer ?",
        "warning3": "Les mises à niveau peuvent modifier les paquets installés et nécessiter des privilèges administrateur.\n\nContinuer ?",
        "detected": "Distribution détectée : {distro}",
        "checking": "Vérification des mises à jour. Cela peut prendre un certain temps.",
        "results": "Résultats de la vérification",
        "no_updates": "Aucune mise à jour disponible.",
        "check_failed": "Échec de la vérification des mises à jour.",
        "upgrade_prompt": "Ouvrir un terminal et lancer la mise à niveau du système ?",
        "review_command": "Vérifiez la commande avant de continuer.",
        "no_upgrade": "Aucune commande de mise à niveau n'est disponible.",
        "no_terminal": "Aucun émulateur de terminal pris en charge n'a été trouvé.\nInstallez-en un, puis réessayez.",
        "upgrade_launch_failed": "Impossible de lancer le terminal de mise à niveau :\n{error}",
        "upgrade_finished": "Le processus de mise à niveau s'est terminé avec le code {status}.",
        "press_enter": "Appuyez sur Entrée pour fermer cette fenêtre...",
        "notify_updates": "Mises à jour disponibles",
        "notify_none": "Aucune mise à jour disponible.",
        "notify_failed": "Échec de la vérification des mises à jour.",
        "spam_limit": "--spam doit être compris entre 1 et {max}.",
        "spam_requires_egg": "--spam nécessite --easter-egg ou --easter-egg-id.",
        "interval_limit": "L'intervalle doit être compris entre {min} et {max} secondes.",
        "pacman_fail": "Impossible de vérifier les mises à jour Arch.\nCode de sortie : {code}\n{output}",
        "pacman_qu_fail": "Échec de pacman -Qu :\n{output}",
        "apt_fail": "Échec d'APT (code de sortie {code}) :\n{output}",
        "dnf_fail": "Échec de DNF (code de sortie {code}) :\n{output}",
        "zypper_fail": "Échec de Zypper (code de sortie {code}) :\n{output}",
        "apk_fail": "Échec d'APK (code de sortie {code}) :\n{output}",
        "xbps_fail": "Échec de XBPS (code de sortie {code}) :\n{output}",
        "updates_available_generic": "Des mises à jour sont disponibles.",
        "new_release_title": "Nouvelle version disponible",
        "new_release_body": "Version installée : {installed}\nDernière version GitHub : {latest}\n\nVisitez https://github.com/{repo}/releases pour l'examiner.",
    },
    "it": {
        "language_header": "Lingue disponibili:",
        "default": "(predefinita)",
        "language_saved": "Lingua salvata: {language}",
        "bad_language": "Lingua non supportata: {language}",
        "unsupported": "Questa distribuzione Linux non è supportata.",
        "supported": "Distribuzioni supportate: Arch, Debian, Ubuntu, Fedora, openSUSE Leap/Tumbleweed, Alpine, Void.",
        "missing": "Comandi richiesti mancanti:",
        "install_deps": "Installa le dipendenze richieste e riprova.",
        "kdialog_missing": "KDialog non è installato. Il messaggio verrà mostrato nel terminale.",
        "command_missing": "Comando non trovato: {command}",
        "timeout": "Il comando ha superato il limite di tempo.",
        "system_error": "Errore di sistema: {error}",
        "dialog_error": "Errore della finestra di dialogo: {error}",
        "warning_title": "Avviso {n} di 3",
        "warning1": "Questa applicazione controlla gli aggiornamenti tramite il gestore pacchetti della distribuzione.\n\nContinuare?",
        "warning2": "Il controllo può contattare i repository software e richiede una connessione Internet.\n\nContinuare?",
        "warning3": "Gli aggiornamenti di sistema possono modificare i pacchetti installati e richiedere privilegi amministrativi.\n\nContinuare?",
        "detected": "Distribuzione rilevata: {distro}",
        "checking": "Controllo degli aggiornamenti. Potrebbe volerci un po'.",
        "results": "Risultati del controllo aggiornamenti",
        "no_updates": "Nessun aggiornamento disponibile.",
        "check_failed": "Controllo degli aggiornamenti non riuscito.",
        "upgrade_prompt": "Aprire un terminale e avviare l'aggiornamento del sistema?",
        "review_command": "Controlla il comando prima di procedere.",
        "no_upgrade": "Nessun comando di aggiornamento disponibile.",
        "no_terminal": "Non è stato trovato un emulatore di terminale supportato.\nInstallane uno e riprova.",
        "upgrade_launch_failed": "Impossibile avviare il terminale di aggiornamento:\n{error}",
        "upgrade_finished": "Il processo di aggiornamento è terminato con codice {status}.",
        "press_enter": "Premi Invio per chiudere questa finestra...",
        "notify_updates": "Aggiornamenti disponibili",
        "notify_none": "Non sono disponibili aggiornamenti.",
        "notify_failed": "Controllo degli aggiornamenti non riuscito.",
        "spam_limit": "--spam deve essere compreso tra 1 e {max}.",
        "spam_requires_egg": "--spam richiede --easter-egg o --easter-egg-id.",
        "interval_limit": "L'intervallo deve essere compreso tra {min} e {max} secondi.",
        "pacman_fail": "Impossibile verificare gli aggiornamenti di Arch.\nCodice di uscita: {code}\n{output}",
        "pacman_qu_fail": "pacman -Qu non riuscito:\n{output}",
        "apt_fail": "APT non riuscito (codice di uscita {code}):\n{output}",
        "dnf_fail": "DNF non riuscito (codice di uscita {code}):\n{output}",
        "zypper_fail": "Zypper non riuscito (codice di uscita {code}):\n{output}",
        "apk_fail": "APK non riuscito (codice di uscita {code}):\n{output}",
        "xbps_fail": "XBPS non riuscito (codice di uscita {code}):\n{output}",
        "updates_available_generic": "Aggiornamenti disponibili.",
        "new_release_title": "Nuova versione disponibile",
        "new_release_body": "Versione installata: {installed}\nUltima versione GitHub: {latest}\n\nVisita https://github.com/{repo}/releases per esaminarla.",
    },
}

SUPPORTED_DISTROS = {
    "arch": {"name": "Arch Linux", "manager": "pacman"},
    "debian": {"name": "Debian", "manager": "apt"},
    "ubuntu": {"name": "Ubuntu", "manager": "apt"},
    "linuxmint": {"name": "Linux Mint", "manager": "apt"},
    "pop": {"name": "Pop!_OS", "manager": "apt"},
    "fedora": {"name": "Fedora", "manager": "dnf"},
    "rhel": {"name": "Red Hat Enterprise Linux", "manager": "dnf"},
    "centos": {"name": "CentOS", "manager": "dnf"},
    "opensuse-leap": {"name": "openSUSE Leap", "manager": "zypper"},
    "opensuse-tumbleweed": {"name": "openSUSE Tumbleweed", "manager": "zypper"},
    "alpine": {"name": "Alpine Linux", "manager": "apk"},
    "void": {"name": "Void Linux", "manager": "xbps"},
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


def t(key, **kwargs):
    table = LOCALES.get(CURRENT_LANGUAGE) or LOCALES[DEFAULT_LANGUAGE]
    text = table.get(key) or LOCALES[DEFAULT_LANGUAGE].get(key, key)
    if not kwargs:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text


def load_language():
    global CURRENT_LANGUAGE
    try:
        value = CONFIG_FILE.read_text(encoding="utf-8").strip().lower()
        if value in SUPPORTED_LANGUAGES:
            CURRENT_LANGUAGE = value
            return
    except OSError:
        pass
    CURRENT_LANGUAGE = DEFAULT_LANGUAGE


def save_language(language):
    global CURRENT_LANGUAGE
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(t("bad_language", language=language))
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(language + "\n", encoding="utf-8")
    os.replace(tmp, CONFIG_FILE)
    CURRENT_LANGUAGE = language


def run_command(command, timeout=180):
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
        output = "\n".join(
            part.strip() for part in (result.stdout, result.stderr) if part.strip()
        )
        return result.returncode, output
    except FileNotFoundError:
        return 127, t("command_missing", command=command[0])
    except subprocess.TimeoutExpired:
        return 124, t("timeout")
    except OSError as exc:
        return 1, t("system_error", error=exc)


def show_dialog(kind, message, title=None):
    title = title or f"{APP_NAME} v{VERSION}"
    kdialog = shutil.which("kdialog")
    if not kdialog:
        print(t("kdialog_missing"))
        print(f"{title}\n{'-' * len(title)}\n{message}")
        if kind in ("warning", "question"):
            try:
                answer = input("[y/N] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return None
            table = LOCALES.get(CURRENT_LANGUAGE) or LOCALES[DEFAULT_LANGUAGE]
            yes_words = ("y", "ya", "iya", "yes", "oui", "si")
            return answer in yes_words
        return None

    command = [kdialog, "--title", title]
    command.append({
        "warning": "--warningyesno",
        "question": "--yesno",
        "error": "--error",
    }.get(kind, "--msgbox"))
    command.append(message)
    try:
        result = subprocess.run(command, check=False, timeout=300)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(t("dialog_error", error=exc))
        return None


def notify(title, message):
    if not shutil.which("notify-send"):
        return False
    try:
        subprocess.run(
            ["notify-send", "-a", APP_NAME, title, message],
            check=False,
            timeout=10,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


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
        for candidate in info.get("ID_LIKE", "").lower().split():
            if candidate in SUPPORTED_DISTROS:
                distro = SUPPORTED_DISTROS[candidate]
                distro_id = candidate
                break
    if distro is None:
        return None
    return {"id": distro_id, **distro}


def check_dependencies(distro):
    required = {
        "pacman": ["pacman"],
        "apt": ["apt"],
        "dnf": ["dnf"],
        "zypper": ["zypper"],
        "apk": ["apk"],
        "xbps": ["xbps-install"],
    }
    return [cmd for cmd in required[distro["manager"]] if not shutil.which(cmd)]


def check_updates(distro):
    manager = distro["manager"]

    if manager == "pacman":
        if shutil.which("checkupdates"):
            code, output = run_command(["checkupdates"])
            if code == 2 and not output:
                return True, NO_UPDATES
            if code != 0:
                return False, t("pacman_fail", code=code, output=output)
            return True, output if output else NO_UPDATES

        code, output = run_command(["pacman", "-Qu"])
        if code == 0:
            return True, output if output else NO_UPDATES
        if code == 1 and not output:
            return True, NO_UPDATES
        return False, t("pacman_qu_fail", output=output)

    if manager == "apt":
        code, output = run_command(["apt", "list", "--upgradable"], timeout=240)
        if code != 0:
            return False, t("apt_fail", code=code, output=output)
        packages = [
            line for line in output.splitlines()
            if "/" in line and not line.lower().startswith(("listing", "warning"))
        ]
        return True, "\n".join(packages) if packages else NO_UPDATES

    if manager == "dnf":
        code, output = run_command(["dnf", "check-update"], timeout=240)
        if code == 0:
            return True, output if output else NO_UPDATES
        if code == 100:
            return True, output if output else t("updates_available_generic")
        return False, t("dnf_fail", code=code, output=output)

    if manager == "zypper":
        code, output = run_command(
            ["zypper", "--non-interactive", "list-updates"], timeout=240
        )
        if code != 0:
            return False, t("zypper_fail", code=code, output=output)
        if "no updates found" in output.lower():
            return True, NO_UPDATES
        return True, output if output else NO_UPDATES

    if manager == "apk":
        code, output = run_command(["apk", "version", "-l", "<"], timeout=240)
        if code != 0:
            return False, t("apk_fail", code=code, output=output)
        return True, output if output else NO_UPDATES

    if manager == "xbps":
        code, output = run_command(["xbps-install", "-Mun"], timeout=240)
        if code != 0:
            return False, t("xbps_fail", code=code, output=output)
        return True, output if output else NO_UPDATES

    return False, "Unsupported package manager."


def get_upgrade_shell_command(distro):
    manager = distro["manager"]
    commands = {
        "pacman": "if command -v yay >/dev/null 2>&1; then yay -Syu; else sudo pacman -Syu; fi",
        "apt": "sudo apt update && sudo apt upgrade",
        "dnf": "sudo dnf upgrade",
        "zypper": "sudo zypper update",
        "apk": "sudo apk update && sudo apk upgrade",
        "xbps": "sudo xbps-install -Syu",
    }
    return commands.get(manager)


def launch_upgrade(distro):
    shell_command = get_upgrade_shell_command(distro)
    if not shell_command:
        show_dialog("error", t("no_upgrade"))
        return
    terminal = next(((name, args) for name, args in TERMINALS if shutil.which(name)), None)
    if terminal is None:
        show_dialog("error", t("no_terminal"))
        return
    terminal_name, terminal_args = terminal
    try:
        temp_dir = Path(tempfile.gettempdir()) / "arch-update-watcher"
        temp_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        script_path = temp_dir / "run-upgrade.sh"
        finished = t("upgrade_finished", status="%s")
        press_enter = t("press_enter")
        script_path.write_text(
            "#!/bin/sh\nset +e\n"
            + shell_command + "\n"
            + "status=$?\n"
            + f'printf "\\n{finished}\\n" "$status"\n'
            + f'printf "{press_enter}\\n"\n'
            + 'read -r _\n'
            + 'exit "$status"\n',
            encoding="utf-8",
        )
        script_path.chmod(0o700)
        if terminal_name == "xfce4-terminal":
            command = [terminal_name, "--command", f"/bin/sh {str(script_path)!r}"]
        else:
            command = [terminal_name, *terminal_args, "/bin/sh", str(script_path)]
        subprocess.Popen(command, start_new_session=True)
    except OSError as exc:
        show_dialog("error", t("upgrade_launch_failed", error=exc))


def latest_github_release():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{APP_NAME}/{VERSION}",
    })
    try:
        with urllib.request.urlopen(request, timeout=API_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        tag = str(data.get("tag_name", "")).strip()
        if not tag:
            return None, "GitHub returned no release tag."
        return tag.removeprefix("v"), None
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        return None, str(exc)


def version_tuple(value):
    parts = value.strip().lstrip("v").split(".")
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return ()


def check_release_notice():
    latest, error = latest_github_release()
    if error:
        return
    if version_tuple(latest) and version_tuple(latest) > version_tuple(VERSION):
        show_dialog(
            "info",
            t("new_release_body", installed=VERSION, latest=latest, repo=GITHUB_REPO),
            t("new_release_title"),
        )


def show_penguin_egg(suffix=""):
    show_dialog(
        "info",
        "🐧 AIO detected!\n\n'Tux says: check twice, upgrade once.'\n"
        "Built for curious Linux tinkerers.",
        "Secret penguin" + suffix,
    )


def show_indonesian_egg(suffix=""):
    show_dialog("info", "🌴\n\nHIDUP JOKOWI", "PRABOWO" + suffix)


def list_languages():
    print(t("language_header"))
    for code, name in SUPPORTED_LANGUAGES.items():
        marker = f" {t('default')}" if code == DEFAULT_LANGUAGE else ""
        print(f"  {code}: {name}{marker}")


def main():
    global CURRENT_LANGUAGE

    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{VERSION}")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--language", choices=list(SUPPORTED_LANGUAGES),
                        help="Set and save the interface language.")
    parser.add_argument("--list-languages", action="store_true",
                        help="List supported languages and exit.")
    parser.add_argument("--easter-egg", action="store_true",
                        help="Show the penguin easter egg and exit.")
    parser.add_argument("--easter-egg-id", action="store_true",
                        help="Show the Indonesian easter egg and exit.")
    parser.add_argument("--spam", type=int, metavar="N",
                        help="Repeat the selected easter egg N times (1-10). "
                             "Each popup waits for the previous one to be closed.")
    parser.add_argument("--interval", type=float, default=1.0, metavar="S",
                        help="Seconds between repeated popups (default: 1).")
    args = parser.parse_args()

    load_language()

    if args.language:
        try:
            save_language(args.language)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))

    if args.list_languages:
        list_languages()
        return 0

    if args.spam is not None:
        if not (args.easter_egg or args.easter_egg_id):
            parser.error(t("spam_requires_egg"))
        if args.spam < 1 or args.spam > MAX_SPAM:
            parser.error(t("spam_limit", max=MAX_SPAM))
        if args.interval < MIN_INTERVAL or args.interval > MAX_INTERVAL:
            parser.error(t("interval_limit", min=MIN_INTERVAL, max=MAX_INTERVAL))
        for i in range(1, args.spam + 1):
            suffix = f" ({i}/{args.spam})" if args.spam > 1 else ""
            if args.easter_egg_id:
                show_indonesian_egg(suffix)
            else:
                show_penguin_egg(suffix)
            if i < args.spam:
                time.sleep(args.interval)
        return 0

    if args.easter_egg_id:
        show_indonesian_egg()
        return 0
    if args.easter_egg:
        show_penguin_egg()
        return 0

    distro = detect_distro()
    if distro is None:
        show_dialog("error", f"{t('unsupported')}\n\n{t('supported')}")
        return 1

    missing = check_dependencies(distro)
    if missing:
        show_dialog(
            "error",
            f"{t('missing')}\n\n" + "\n".join(missing) + f"\n\n{t('install_deps')}",
        )
        return 1

    for n in (1, 2, 3):
        if show_dialog("warning", t(f"warning{n}"), t("warning_title", n=n)) is not True:
            return 0

    check_release_notice()

    show_dialog("info", f"{t('detected', distro=distro['name'])}\n\n{t('checking')}")
    success, output = check_updates(distro)
    if not success:
        notify(t("notify_failed"), t("check_failed"))
        show_dialog("error", f"{t('check_failed')}\n\n{output}")
        return 1

    if output == NO_UPDATES:
        result_text = t("no_updates")
        notify(t("notify_none"), result_text)
    else:
        result_text = output
        notify(t("notify_updates"), result_text[:400])

    show_dialog(
        "info",
        f"{t('detected', distro=distro['name'])}\n\n{t('results')}:\n\n{result_text}",
        t("results"),
    )

    if output == NO_UPDATES:
        return 0

    if show_dialog("question", f"{t('upgrade_prompt')}\n\n{t('review_command')}"):
        launch_upgrade(distro)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())