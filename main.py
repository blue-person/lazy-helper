# Libraries
import argparse
import ctypes
import os
import random
import subprocess
import sys
import time
import tomllib
from datetime import datetime
from pathlib import Path


# Get the base directory of the script or executable
def get_base_dir() -> Path:
    # In a --onefile build, __file__ points at a temporary folder, not the .exe
    onefile_binary = os.environ.get("NUITKA_ONEFILE_BINARY")
    if onefile_binary:
        return Path(onefile_binary).resolve().parent
    if "__compiled__" in globals():
        return Path(sys.argv[0]).resolve().parent
    return Path(__file__).resolve().parent


# Constants
SETTINGS_PATH = get_base_dir() / "settings.toml"

# Settings file template
DEFAULT_SETTINGS_TOML = """\
# When to press the key
## always: press the key all the time
## auto:   press the key only while the process in "process_name" is running
## awake:  never press any key, only prevent the system from sleeping
mode = "auto"

# Key to press to keep the session active
## Supported values: numlock, scrolllock, capslock, f13, f14, f15, shift, ctrl, alt
key = "numlock"

# Process to look for (only used in "auto" mode)
process_name = "discord.exe"

# Seconds to wait before checking again if the process is running (only used in "auto" mode)
process_check_interval = 15

# Seconds to wait between key presses
[press_interval]
min = 15
max = 90
"""

# Valid operating modes
MODES = ("always", "auto", "awake")

# Keys
KEYEVENTF_KEYUP = 0x0002

# Supported keys mapped to their Windows virtual-key codes.
VK_CODES = {
    "numlock": 0x90,
    "scrolllock": 0x91,
    "capslock": 0x14,
    "f13": 0x7C,
    "f14": 0x7D,
    "f15": 0x7E,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
}

# SetThreadExecutionState flags
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

# Console control events
CTRL_C_EVENT = 0
CTRL_BREAK_EVENT = 1
CTRL_CLOSE_EVENT = 2
CTRL_LOGOFF_EVENT = 5
CTRL_SHUTDOWN_EVENT = 6

# Keep a reference so the callback is not garbage collected.
_console_handler_ref = None


# Functions
def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_settings_file() -> None:
    if SETTINGS_PATH.exists():
        return
    SETTINGS_PATH.write_text(DEFAULT_SETTINGS_TOML, encoding="utf-8")
    print(
        f"{now()} - settings.toml not found, created with default values at {SETTINGS_PATH}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Keeps the session active by simulating a key press."
    )
    parser.add_argument(
        "--mode",
        choices=MODES,
        help="Override the mode from settings.toml (always, auto or awake)",
    )
    return parser.parse_args()


def load_settings(cli_mode: str | None = None) -> dict:
    ensure_settings_file()
    try:
        with open(SETTINGS_PATH, "rb") as f:
            data = tomllib.load(f)
    except OSError as exc:
        sys.exit(f"{now()} - Could not read settings file: {exc}")
    except tomllib.TOMLDecodeError as exc:
        sys.exit(f"{now()} - Invalid settings.toml: {exc}")

    key = str(data.get("key", "numlock")).lower()
    if key not in VK_CODES:
        sys.exit(
            f"{now()} - Unsupported key '{key}'. "
            f"Choose one of: {', '.join(sorted(VK_CODES))}"
        )

    interval = data.get("press_interval", {})
    interval_min = int(interval.get("min", 15))
    interval_max = int(interval.get("max", 90))
    if interval_min > interval_max:
        sys.exit(
            f"{now()} - press_interval.min ({interval_min}) "
            f"cannot be greater than max ({interval_max})"
        )

    process_name = str(data.get("process_name", "discord.exe")).strip()
    check_interval = max(int(data.get("process_check_interval", 15)), 1)

    mode = cli_mode or str(data.get("mode", "auto")).lower()
    if mode not in MODES:
        sys.exit(f"{now()} - Unsupported mode '{mode}'. Choose one of: {', '.join(MODES)}")
    if mode == "auto" and not process_name:
        sys.exit(f"{now()} - Mode 'auto' needs a non-empty process_name")

    return {
        "mode": mode,
        "key": key,
        "vk_code": VK_CODES[key],
        "process_name": process_name,
        "process_check_interval": check_interval,
        "interval_min": interval_min,
        "interval_max": interval_max,
    }


def prevent_sleep() -> None:
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )


def allow_sleep() -> None:
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)


def _install_console_handler() -> None:
    # Globals
    global _console_handler_ref

    # Define the handler routine type
    HANDLER_ROUTINE = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong)

    def handler(ctrl_type: int) -> bool:
        if ctrl_type in (
            CTRL_CLOSE_EVENT,
            CTRL_LOGOFF_EVENT,
            CTRL_SHUTDOWN_EVENT,
        ):
            allow_sleep()
        # Return False so default handling still runs (process exits).
        return False

    # Restore normal power state when the console window is closed
    _console_handler_ref = HANDLER_ROUTINE(handler)
    ctypes.windll.kernel32.SetConsoleCtrlHandler(_console_handler_ref, True)


def is_process_running(process_name: str) -> bool:
    # tasklist writes in the console's OEM codepage
    output = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {process_name}", "/NH"],
        capture_output=True,
        text=True,
        encoding="oem",
        errors="replace",
    ).stdout
    return process_name.lower() in output.lower()


def press_key_twice(vk_code: int) -> None:
    for _ in range(2):
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


def should_press(settings: dict) -> bool:
    # In "always" mode no process is ever looked up
    if settings["mode"] == "always":
        return True
    name = settings["process_name"]
    if is_process_running(name):
        print(f"{now()} - Process {name} is running.")
        return True
    print(f"{now()} - Process {name} is not running.")
    return False


def run(settings: dict) -> None:
    if settings["mode"] == "awake":
        # No key presses and no process lookups: the execution state set in
        # prevent_sleep() is all that is needed, so just wait.
        print(f"{now()} - No key will be pressed and only sleep is blocked. Press Ctrl+C to exit.")
        while True:
            time.sleep(3600)
    while True:
        if should_press(settings):
            press_key_twice(settings["vk_code"])
            print(f"{now()} - Pressed {settings['key'].upper()} twice")
            delay = random.randint(settings["interval_min"], settings["interval_max"])
        else:
            delay = settings["process_check_interval"]
        print(f"{now()} - Sleeping for {delay} seconds...")
        time.sleep(delay)


# Main handler
if __name__ == "__main__":
    settings = load_settings(parse_args().mode)
    _install_console_handler()
    prevent_sleep()
    print(f"{now()} - Sleep prevention enabled")
    print(f"{now()} - Mode: {settings['mode']}")
    if settings["mode"] != "awake":
        print(f"{now()} - Using key '{settings['key']}'")
    try:
        run(settings)
    except KeyboardInterrupt:
        print(f"\n{now()} - Interrupted by user, exiting...")
    finally:
        allow_sleep()
        print(f"{now()} - Sleep prevention disabled, system back to normal")
