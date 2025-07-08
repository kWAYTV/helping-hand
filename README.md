# Chess Bot for Lichess

An automated chess bot that plays on Lichess using Stockfish engine and Selenium WebDriver.

## Requirements

- Python 3.7+
- Firefox browser
- Lichess account

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

Edit `config.ini` with your settings:

#### **[engine] - Chess Engine Settings**

- **`path`** - Path to Stockfish executable

  - Windows: `deps/stockfish/stockfish.exe`
  - Linux/Mac: `deps/stockfish/stockfish`

- **`depth`** - Engine search depth (1-20)

  - Higher = stronger but slower
  - Recommended: 5-15
  - Default: `5`

- **`hash`** - Memory allocation in MB (64-8192)

  - Higher = better performance
  - Default: `2048`

- **`skill-level`** - Engine strength (0-20)
  - 0 = weakest, 20 = strongest
  - Default: `14`

#### **[lichess] - Lichess Account Settings**

- **`username`** - Your Lichess username

  - Required for login

- **`password`** - Your Lichess password

  - Required for login

- **`totp-secret`** - Base32 TOTP secret for 2FA (optional)
  - If set: Automatic 2FA code generation
  - If empty: Manual 2FA input required
  - Format: Base32 string (e.g., `JBSWY3DPEHPK3PXP`)

#### **[general] - Bot Behavior Settings**

- **`move-key`** - Key to execute suggested moves in manual mode

  - Options: `a-z`, `space`, `end`, `home`, etc.
  - Default: `end`

- **`arrow`** - Show move suggestion arrows on board

  - `true` = Show green arrows indicating suggested moves
  - `false` = No visual indicators
  - Default: `true`

- **`auto-play`** - Bot operation mode
  - `true` = **AutoPlay Mode**: Bot makes moves automatically
  - `false` = **Suggestion Mode**: Bot suggests moves, wait for key press
  - Default: `true`

#### **[humanization] - Delay Settings (seconds)**

All delays use cryptographically secure randomization to simulate human behavior.

**General Actions:**

- **`min-delay`** - Minimum delay for general actions (0.1-10.0)
  - Default: `0.3`
- **`max-delay`** - Maximum delay for general actions (0.1-10.0)
  - Default: `1.8`

**Move Execution:**

- **`moving-min-delay`** - Minimum delay before making moves (0.1-10.0)
  - Default: `0.5`
- **`moving-max-delay`** - Maximum delay before making moves (0.1-10.0)
  - Default: `2.5`

**Engine Thinking:**

- **`thinking-min-delay`** - Minimum delay for engine calculation simulation (0.1-10.0)
  - Default: `0.8`
- **`thinking-max-delay`** - Maximum delay for engine calculation simulation (0.1-10.0)
  - Default: `3.0`

### 4. Usage

```bash
python main.py
```

#### **Operating Modes:**

**🤖 AutoPlay Mode** (`auto-play = true`)

- Bot automatically makes the best moves
- Shows brief arrow indicators (if enabled)
- Fully automated gameplay

**💭 Suggestion Mode** (`auto-play = false`)

- Bot calculates and displays suggested moves with arrows
- Press configured key (default: `End`) to execute suggested move
- Allows manual move selection and override

#### **2FA Setup (Optional)**

For automatic 2FA handling, add your TOTP secret to config:

1. Enable 2FA on your Lichess account
2. During setup, save the Base32 secret key
3. Add to config: `totp-secret = YOUR_BASE32_SECRET`
4. Bot will automatically generate and input 2FA codes

If not configured, bot will wait up to 5 minutes for manual 2FA input.
