# Lichess Chess Bot

> Professional automated chess bot for Lichess.org featuring Stockfish engine integration, advanced humanization, and intelligent move execution.

## 🎯 Features

- **Stockfish Integration** - Configurable engine strength and depth
- **Dual Operation Modes** - Automatic play or manual confirmation
- **Advanced Humanization** - Multi-layer timing randomization with jitter
- **2FA Support** - Automatic TOTP code generation
- **Visual Feedback** - Move suggestion arrows and comprehensive logging
- **Cross-Platform** - Windows, Linux, and macOS support

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Firefox browser
- Lichess account

### Installation

1. **Clone and install dependencies**

   ```bash
   git clone <repository-url>
   cd helping-hand
   pip install -r requirements.txt
   ```

2. **Download required binaries**

   **Stockfish Engine:**

   - Download from [stockfishchess.org](https://stockfishchess.org/download/)
   - Place in `deps/stockfish/` (auto-detected by OS)

   **GeckoDriver:**

   - Download from [GitHub releases](https://github.com/mozilla/geckodriver/releases)
   - Place in `deps/geckodriver/` (auto-detected by OS)

3. **Configure the bot**

   ```bash
   cp config.example.ini config.ini
   # Edit config.ini with your credentials
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Engine Settings

| Key           | Description                             | Default       |
| ------------- | --------------------------------------- | ------------- |
| `path`        | Stockfish executable path               | Auto-detected |
| `depth`       | Search depth (higher = stronger/slower) | 5             |
| `hash`        | Memory allocation (MB)                  | 2048          |
| `skill-level` | Engine strength (0-20)                  | 14            |

### Lichess Authentication

| Key           | Description         | Required |
| ------------- | ------------------- | -------- |
| `username`    | Lichess username    | Yes      |
| `password`    | Lichess password    | Yes      |
| `totp-secret` | 2FA secret (base32) | Optional |

### Bot Behavior

| Key         | Description              | Default |
| ----------- | ------------------------ | ------- |
| `move-key`  | Manual execution key     | `end`   |
| `arrow`     | Show move suggestions    | `true`  |
| `auto-play` | Automatic vs manual play | `true`  |

### Humanization

| Key                                         | Description            | Range    |
| ------------------------------------------- | ---------------------- | -------- |
| `min-delay` / `max-delay`                   | Base action delays     | 0.3-1.8s |
| `moving-min-delay` / `moving-max-delay`     | Move execution delays  | 0.5-2.5s |
| `thinking-min-delay` / `thinking-max-delay` | Engine thinking delays | 0.8-3.0s |

> **Note:** The bot automatically adds 0-1s jitter and micro-variations to all delays for natural behavior.

## 🔐 Two-Factor Authentication

For accounts with 2FA enabled:

1. **Obtain your TOTP secret**

   - Open your authenticator app
   - Reveal the secret key (base32 encoded string)

2. **Add to configuration**

   ```ini
   [lichess]
   totp-secret = YOUR_BASE32_SECRET_HERE
   ```

3. **Automatic handling**
   - Bot detects 2FA prompts automatically
   - Generates and inputs TOTP codes
   - Falls back to manual input if no secret provided

## 🎮 Operation Modes

### AutoPlay Mode

- Bot plays moves automatically
- Configurable delays and humanization
- Suitable for unattended operation

### Suggestion Mode

- Bot suggests optimal moves
- Press configured key to execute
- Ideal for learning and analysis

## 📝 License

This project is for educational purposes only. Users are responsible for compliance with Lichess terms of service and applicable laws.

## 🤝 Contributing

Contributions are welcome! Please ensure all changes maintain the project's focus on reliability and anti-detection measures.
