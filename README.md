# Lazy Helper

A small Windows script that keeps Microsoft Teams from showing you as "away" while it's open.

## What it does

- Checks whether `ms-teams.exe` is running.
- If it is, it simulates pressing a key (default: `NumLock`) at random intervals to keep your status "active".
- It also prevents the computer from going to sleep or turning off the display while the script is running.
- If Teams isn't open, it just waits and checks again later. 
- When the script stops (Ctrl+C, closing the console, logging off, or shutting down), it restores the system's normal power behavior.

## Requirements

- Windows
- Python 3.11

## Installation

```bash
git clone https://github.com/blue-person/lazy-helper.git
cd lazy-helper
```

No external dependencies required.

## Configuration

Edit `settings.toml` to adjust the behavior:

```toml
key = "numlock"          # key to press: numlock, scrolllock, capslock, f13, f14, f15, shift, ctrl, alt
teams_open_delay = 15     # seconds to wait if Teams isn't open

[press_interval]
min = 15                  # minimum interval between key presses (seconds)
max = 90                  # maximum interval between key presses (seconds)
```

## Usage

```bash
python main.py
```

The script keeps running in the console, printing logs of what it's doing. Press `Ctrl+C` to stop it.

## License

Apache-2.0
