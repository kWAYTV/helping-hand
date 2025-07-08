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
