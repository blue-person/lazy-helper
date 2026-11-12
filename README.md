# Lazy Helper

A small Windows script that keeps the computer awake and simulates a key press at random intervals.

## What it does

- It prevents the computer from going to sleep or turning off the display while it runs.
- It simulates a key press (by default, `NumLock`) at random intervals, so the session does not look inactive.
- When it stops, it restores the normal power behavior of the system.

It has three modes.

- `auto` (default) presses the key only while the process set in `process_name` is running, and checks again later when it is not.
- `always` presses the key continuously.
- `awake` never presses a key and only prevents the computer from sleeping.

## Requirements

- Windows
- Python 3.11 or newer

## Installation

```bash
git clone https://github.com/blue-person/lazy-helper.git
cd lazy-helper
```

## Configuration

Edit `settings.toml` to change the behavior. Any missing option uses its default value. If the file does not exist, the program creates it with the default values on the first run.

```toml
# always, auto or awake
mode = "auto"

# numlock, scrolllock, capslock, f13, f14, f15, shift, ctrl or alt
key = "numlock"

# Process to look for, used only in auto mode
process_name = "discord.exe"

# Seconds between process checks, used only in auto mode
process_check_interval = 15

# Minimum and maximum seconds between key presses
[press_interval]
min = 15
max = 90
```

## Usage

```bash
python main.py                 # uses the mode from settings.toml
python main.py --mode auto     # presses the key only while the configured process is running
python main.py --mode always   # presses the key continuously
python main.py --mode awake    # never presses a key, only prevents sleep
```

The `--mode` option overrides the value in `settings.toml`. The script keeps running in the console and prints a log of its actions. Press `Ctrl+C` to stop it.

## Building the executable

The project is compiled into a single `.exe` with [Nuitka](https://nuitka.net/), which requires `uv` and a C compiler. If no compiler is installed, Nuitka offers to download one.

```bat
uv sync --frozen

uv run --frozen nuitka ^
    --onefile ^
    --assume-yes-for-downloads ^
    --remove-output ^
    --windows-icon-from-ico=assets/icon.ico ^
    --include-data-files=assets/icon.ico=icon.ico ^
    --include-data-files=settings.toml=settings.toml ^
    --include-data-files-external=icon.ico ^
    --include-data-files-external=settings.toml ^
    --product-version=1.0.0 ^
    --file-version=1.0.0 ^
    --product-name="lazy-helper" ^
    --file-description="Keeps your computer awake while you are away." ^
    --output-dir=dist ^
    --output-filename=lazy-helper.exe ^
    main.py
```
