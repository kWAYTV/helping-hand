# Lichess Chess Bot

Professional automated chess bot for Lichess.org with Stockfish engine integration and advanced humanization.

## 📦 Releases

Pre-built executables are available in [GitHub Releases](https://github.com/kWAYTV/helping-hand/releases).

## 🚀 Quick Start

### From Release (Recommended)

1. Download the latest release zip file
2. Extract the zip file to your desired location
3. Configure `config.ini` (copy from `config.example.ini`)
4. Run `helping-hand.exe`

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

## 🖥️ GUI Interface

The bot includes a modern GUI with console output:

- **Real-time chess board** with piece positions and move visualization
- **Engine suggestions** with arrows and move notation
- **Live game information** (color, turn, move number)
- **Activity log** with color-coded messages and auto-scroll
- **Control panel** for starting/stopping the bot and manual move execution
- **Clean, dark theme** designed for extended use

## 🎮 Operation Modes

- **AutoPlay**: Fully automated gameplay
- **Suggestion**: Manual confirmation required (press configured key or GUI button)

## 📝 License

Educational purposes only. Users responsible for compliance with Lichess ToS.
