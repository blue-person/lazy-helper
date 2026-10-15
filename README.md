# Lazy Helper

A small Windows script that keeps Microsoft Teams from showing you as "away" while it's open.

## What it does

- Checks whether `ms-teams.exe` is running.
- If it is, it simulates pressing a key (default: `NumLock`) at random intervals to keep your status "active".
- It also prevents the computer from going to sleep or turning off the display while the script is running.
- If Teams isn't open, it just waits and checks again later.
- When the script stops, it restores the system's normal power behavior.

## Requirements

- Windows
- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) (only needed to build the executable)

## Installation

```bash
git clone https://github.com/blue-person/lazy-helper.git
cd lazy-helper
```

## Configuration

Edit `settings.toml` to adjust the behavior:

```toml
key = "numlock"             # key to press: numlock, scrolllock, capslock, f13, f14, f15, shift, ctrl, alt
teams_open_delay = 15       # seconds to wait if Teams isn't open

[press_interval]
min = 15                    # minimum interval between key presses (seconds)
max = 90                    # maximum interval between key presses (seconds)
```

## Usage

```bash
python main.py
```

The script keeps running in the console, printing logs of what it's doing. Press `Ctrl+C` to stop it.

If `settings.toml` doesn't exist, it is created with default values on the first run.

## Building the executable

The project is compiled into a single `.exe` with [Nuitka](https://nuitka.net/). You need `uv` and a C compiler. If none is installed, Nuitka offers to download one automatically.

```bash
uv sync
uv run nuitka --onefile --windows-icon-from-ico=assets/icon.ico --output-dir=dist --output-filename=lazy-helper.exe main.py
```

The result is `dist/lazy-helper.exe`. Place `settings.toml` next to it to customize the behavior.
