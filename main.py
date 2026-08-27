# Libraries
import ctypes
import subprocess
import sys
import time
import random
import tomllib
from datetime import datetime
from pathlib import Path

# Constants
PROCESS_NAME = "ms-teams.exe"
SETTINGS_PATH = Path(__file__).with_name("settings.toml")

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


def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        sys.exit(f"{now()} - Settings file not found: {SETTINGS_PATH}")
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

    return {
        "key": key,
        "vk_code": VK_CODES[key],
        "teams_open_delay": int(data.get("teams_open_delay", 15)),
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


def is_teams_running() -> bool:
    output = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {PROCESS_NAME}", "/NH"],
        capture_output=True,
        text=True,
    ).stdout
    return PROCESS_NAME.lower() in output.lower()


def press_key_twice(vk_code: int) -> None:
    for _ in range(2):
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


# Main handler
if __name__ == "__main__":
    settings = load_settings()
    _install_console_handler()
    prevent_sleep()
    print(f"{now()} - Sleep prevention enabled")
    print(f"{now()} - Using key '{settings['key']}'")
    try:
        while True:
            if is_teams_running():
                print(f"{now()} - Microsoft Teams is running!")
                press_key_twice(settings["vk_code"])
                print(f"{now()} - Pressed {settings['key'].upper()} twice")
                delay = random.randint(
                    settings["interval_min"], settings["interval_max"]
                )
                print(f"{now()} - Sleeping for {delay} seconds...")
                time.sleep(delay)
            else:
                delay = settings["teams_open_delay"]
                print(f"{now()} - Microsoft Teams is not running!")
                print(f"{now()} - Sleeping for {delay} seconds...")
                time.sleep(delay)
    except KeyboardInterrupt:
        print(f"\n{now()} - Interrupted by user, exiting...")
    finally:
        allow_sleep()
        print(f"{now()} - Sleep prevention disabled, system back to normal")