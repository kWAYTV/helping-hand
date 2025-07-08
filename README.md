# Chess Bot for Lichess

An automated chess bot that plays on Lichess using Stockfish engine and Selenium WebDriver.

## Setup

### 1. Install Dependencies

```bash
py -m pip install --upgrade -r requirements.txt
```

### 2. Configure Binaries

Download and place the following binaries in their respective folders:

**Stockfish Engine:**

- Download from [stockfishchess.org](https://stockfishchess.org/download/)
- Place in `deps/stockfish/`
- Windows: `stockfish.exe`
- Linux/Mac: `stockfish`

**GeckoDriver (Firefox WebDriver):**

- Download from [GitHub Releases](https://github.com/mozilla/geckodriver/releases)
- Place in `deps/geckodriver/`
- Windows: `geckodriver.exe`
- Linux/Mac: `geckodriver`

### 3. Configuration

```bash
cp config.example.ini config.ini
```

Edit `config.ini` with your Lichess credentials and preferences.

#### Configuration Options

**[engine]**

- `path`: Path to Stockfish executable (auto-detected based on OS)
- `depth`: Search depth for move calculation (higher = stronger but slower)
- `hash`: Memory allocation for engine in MB
- `skill-level`: Engine skill level (0-20, where 20 is strongest)

**[lichess]**

- `username`: Your Lichess username
- `password`: Your Lichess password
- `totp-secret`: Optional TOTP secret for 2FA (base32 encoded from your authenticator app)

**[general]**

- `move-key`: Key to press for executing suggested moves (default: 'end')
- `arrow`: Show visual arrows for suggested moves (true/false)
- `auto-play`: Automatically play moves vs manual confirmation (true/false)

**[humanization]**

- `min-delay` / `max-delay`: Base delay range for actions (seconds)
- `moving-min-delay` / `moving-max-delay`: Delay range for move execution
- `thinking-min-delay` / `thinking-max-delay`: Delay range for engine thinking

The bot adds additional jitter (0-1s) and micro-variations to all delays for natural behavior.

#### TOTP Setup (Optional)

If you have 2FA enabled on Lichess:

1. In your authenticator app, reveal the secret key (usually base32 encoded)
2. Add it to `totp-secret` in your config
3. The bot will automatically generate and input TOTP codes when required

If no `totp-secret` is provided, the bot will wait for manual TOTP input.

## Usage

```bash
python main.py
```

**Modes:**

- **AutoPlay**: Bot makes moves automatically
- **Suggestion**: Bot suggests moves, press configured key to execute

## Requirements

- Python 3.7+
- Firefox browser
- Lichess account
