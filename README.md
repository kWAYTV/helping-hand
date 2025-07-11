# Lichess Chess Bot

Professional automated chess bot for Lichess.org with Stockfish engine integration and advanced humanization.

## 📦 Releases

Pre-built executables are available in [GitHub Releases](https://github.com/kWAYTV/helping-hand/releases).

**Important:** Download the executable and place the entire `deps/` folder in the same directory as the `.exe` file.

## 🚀 Quick Start

### From Release (Recommended)

1. Download the latest release executable
2. Download and place the `deps/` folder alongside the `.exe`
3. Configure `config.ini` (copy from `config.example.ini`)
4. Run the executable

### From Source

1. Clone repository and install dependencies:

   ```bash
   git clone https://github.com/kWAYTV/helping-hand.git
   cd helping-hand
   pip install -r requirements.txt
   ```

2. Download required binaries to `deps/`:

   - **Stockfish**: [stockfishchess.org](https://stockfishchess.org/download/)
   - **GeckoDriver**: [GitHub releases](https://github.com/mozilla/geckodriver/releases)
   - **xPath Finder**: [Firefox addon](https://addons.mozilla.org/en-US/firefox/addon/xpath_finder/) (download `.xpi` file)

3. Configure and run:
   ```bash
   cp config.example.ini config.ini
   # Edit config.ini with your credentials
   python main.py
   ```

## ⚙️ Configuration

### Essential Settings

```ini
[lichess]
username = your_username
password = your_password
totp-secret = your_2fa_secret  # Optional

[engine]
depth = 5          # Higher = stronger/slower
skill-level = 14   # 0-20 engine strength

[bot]
auto-play = true   # false for manual confirmation
move-key = end     # Key to execute moves manually
log-level = INFO   # TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR
```

### Humanization

Built-in timing randomization with configurable delays:

- Base actions: 0.3-1.8s
- Move execution: 0.5-2.5s
- Engine thinking: 0.8-3.0s

## 🎮 Operation Modes

- **AutoPlay**: Fully automated gameplay
- **Suggestion**: Manual confirmation required (press configured key)

## 📝 License

Educational purposes only. Users responsible for compliance with Lichess ToS.
