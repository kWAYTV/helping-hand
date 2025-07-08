import configparser
import glob
import os
import os.path
import platform
import random
import re
import time
from math import ceil
from time import sleep

import chess
import chess.engine
from loguru import logger
from pynput import keyboard
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

"""
Required: Input moves with keyboard [lichess preferences]
"""


# Declare globals
def get_geckodriver_path():
    system = platform.system().lower()
    if system == "windows":
        return os.path.join("deps", "geckodriver", "geckodriver.exe")
    else:
        return os.path.join("deps", "geckodriver", "geckodriver")


def get_stockfish_path():
    system = platform.system().lower()
    if system == "windows":
        return os.path.join("deps", "stockfish", "stockfish.exe")
    else:
        return os.path.join("deps", "stockfish", "stockfish")


webdriver_options = webdriver.FirefoxOptions()
webdriver_options.add_argument(
    f'--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"'
)
firefox_service = webdriver.firefox.service.Service(
    executable_path=get_geckodriver_path()
)
driver = webdriver.Firefox(service=firefox_service, options=webdriver_options)
config = configparser.ConfigParser()
make_move = False


def check_exists_by_xpath(xpath):
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element
    except NoSuchElementException:
        return False


def check_exists_by_class(classname):
    try:
        element = driver.find_element(By.CLASS_NAME, classname)
        return element
    except NoSuchElementException:
        return False


def find_color(board):
    logger.info("Starting find_color - looking for game setup")

    while check_exists_by_class("follow-up"):
        logger.debug("Found follow-up element, waiting...")
        sleep(1)

    logger.info("No follow-up found, waiting for move input box")

    # wait for move input box
    try:
        WebDriverWait(driver, 600).until(
            ec.presence_of_element_located(
                (By.XPATH, "/html/body/div[2]/main/div[1]/div[10]/input")
            )
        )
        logger.info("Move input box found")
    except Exception as e:
        logger.error(f"Failed to find move input box: {e}")
        return

    # wait for board
    try:
        WebDriverWait(driver, 600).until(
            ec.presence_of_element_located((By.CLASS_NAME, "cg-wrap"))
        )
        logger.info("Board found")
    except Exception as e:
        logger.error(f"Failed to find board: {e}")
        return

    board_set_for_white = check_exists_by_class("orientation-white")

    if board_set_for_white:
        our_color = "W"
        logger.info("Playing as WHITE")
        play_game(board, our_color)
    else:
        our_color = "B"
        logger.info("Playing as BLACK")
        play_game(board, our_color)


def new_game(board):
    logger.info("Starting new game - resetting board")
    board.reset()
    find_color(board)


def find_move_by_alternatives(move_number):
    """Try alternative selectors to find moves"""

    # Try finding all moves and get by index (most reliable)
    try:
        elements = driver.find_elements(By.CLASS_NAME, "kwdb")
        if len(elements) >= move_number:
            element = elements[move_number - 1]  # 0-based indexing
            move_text = element.text.strip()
            if move_text:  # Only return if there's actual text
                logger.info(f"Found move {move_number}: '{move_text}' by class index")
                return element
    except:
        pass

    # Alternative selectors to try (only if class method fails)
    selectors = [
        f"//kwdb[{move_number}]",  # Shortest XPath
        f"//rm6/l4x/kwdb[{move_number}]",  # Medium XPath
        f"/html/body/div[2]/main/div[1]/rm6/l4x/kwdb[{move_number}]",  # Original
    ]

    for selector in selectors:
        try:
            element = driver.find_element(By.XPATH, selector)
            move_text = element.text.strip()
            if move_text:  # Only return if there's actual text
                logger.info(f"Found move {move_number}: '{move_text}' using {selector}")
                return element
        except:
            continue

    return None


def debug_move_list_structure():
    """Debug function to inspect the actual HTML structure of moves"""
    logger.info("=== DEBUGGING MOVE LIST STRUCTURE ===")

    # Try different possible selectors
    selectors_to_try = [
        "rm6",
        "l4x",
        "kwdb",
        ".move-list",
        ".moves",
        "[data-testid*='move']",
        ".move",
        "moveOn",
        "san",
    ]

    for selector in selectors_to_try:
        try:
            if selector.startswith("."):
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            elif selector.startswith("["):
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            else:
                elements = driver.find_elements(By.CLASS_NAME, selector)

            logger.info(f"Selector '{selector}': Found {len(elements)} elements")
            for i, elem in enumerate(elements[:5]):  # Show first 5
                try:
                    text = elem.text.strip()
                    tag = elem.tag_name
                    classes = elem.get_attribute("class")
                    logger.info(
                        f"  [{i}] Tag: {tag}, Classes: {classes}, Text: '{text}'"
                    )
                except:
                    logger.debug(f"  [{i}] Could not get element info")
        except Exception as e:
            logger.debug(f"Selector '{selector}' failed: {e}")

    # Try to find the move list container
    try:
        page_source = driver.page_source
        import re

        # Look for move-related patterns in HTML
        patterns = ["kwdb", "l4x", "rm6", "move-list", "san", "moveOn"]
        for pattern in patterns:
            matches = re.findall(f".*{pattern}.*", page_source, re.IGNORECASE)
            if matches:
                logger.info(f"Pattern '{pattern}' found in HTML:")
                for match in matches[:3]:  # Show first 3 matches
                    logger.info(f"  {match[:200]}")  # Truncate long lines
    except Exception as e:
        logger.error(f"Could not analyze page source: {e}")


def get_previous_moves(board):
    logger.info("Getting previous moves from board")
    temp_move_number = 1

    # reset every move
    # board.reset()

    while temp_move_number < 999:  # just in-case, lol
        move_xpath = (
            "/html/body/div[2]/main/div[1]/rm6/l4x/kwdb[" + str(temp_move_number) + "]"
        )
        move_element = check_exists_by_xpath(move_xpath)
        if not move_element:
            # Try alternative selectors
            move_element = find_move_by_alternatives(temp_move_number)

        if move_element:
            move_text = move_element.text.strip()
            logger.debug(f"Found previous move {temp_move_number}: {move_text}")
            board.push_san(move_text)
            temp_move_number += 1
        else:
            logger.info(
                f"No more previous moves found. Total moves processed: {temp_move_number - 1}"
            )
            # Save debug info if we expected more moves but couldn't find them
            if temp_move_number <= 3:  # If we can't even find the first few moves
                logger.warning("Could not find expected moves, saving debug info")
                debug_move_list_structure()  # Run detailed analysis when stuck
                save_debug_info(temp_move_number, board)
            return temp_move_number


def get_seconds(time_str):
    semicolons = time_str.count(":")

    if semicolons == 2:
        # hh, mm, ss
        hh, mm, ss = time_str.split(":")
        return int(hh) * 3600 + int(mm) * 60 + int(ss)
    elif semicolons == 1:
        fixed = time_str.partition(".")
        # mm, ss
        mm, ss = fixed.split(":")
        return int(mm) * 60 + int(ss)

    return 0


def on_press(key):
    global make_move

    key_string = str(key)
    move_key = config["general"].get("movekey", config["general"].get("MoveKey", ""))
    if key_string == move_key or key_string == "Key." + move_key:
        make_move = True


def on_release(key):
    global make_move

    key_string = str(key)
    move_key = config["general"].get("movekey", config["general"].get("MoveKey", ""))
    if key_string == move_key or key_string == "Key." + move_key:
        make_move = False


def clear_arrow():
    driver.execute_script(
        """
                   g = document.getElementsByTagName("g")[0];
                   g.textContent = "";
                   """
    )


def draw_arrow(result, our_color):
    transform = get_piece_transform(result.move, our_color)

    move_str = str(result.move)
    src = str(move_str[:2])
    dst = str(move_str[2:])

    board_style = driver.find_element(
        By.XPATH, "/html/body/div[2]/main/div[1]/div[1]/div/cg-container"
    ).get_attribute("style")
    board_size = re.search(r"\d+", board_style).group()

    driver.execute_script(
        """
                                            var x1 = arguments[0];
                                            var y1 = arguments[1];
                                            var x2 = arguments[2];
                                            var y2 = arguments[3];
                                            var size = arguments[4];
                                            var src = arguments[5];
                                            var dst = arguments[6];

                                            defs = document.getElementsByTagName("defs")[0];

                                            child_defs = document.getElementsByTagName("marker")[0];

                                            if (child_defs == null)
                                            {
                                                child_defs = document.createElementNS("http://www.w3.org/2000/svg", "marker");
                                                child_defs.setAttribute("id", "arrowhead-g");
                                                child_defs.setAttribute("orient", "auto");
                                                child_defs.setAttribute("markerWidth", "4");
                                                child_defs.setAttribute("markerHeight", "8");
                                                child_defs.setAttribute("refX", "2.05");
                                                child_defs.setAttribute("refY", "2.01");
                                                child_defs.setAttribute("cgKey", "g");

                                                path = document.createElement('path')
                                                path.setAttribute("d", "M0,0 V4 L3,2 Z");
                                                path.setAttribute("fill", "#15781B");  
                                                child_defs.appendChild(path);

                                                defs.appendChild(child_defs);
                                            }

                                            g = document.getElementsByTagName("g")[0];

                                            var child_g = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                                            child_g.setAttribute("stroke","#15781B");
                                            child_g.setAttribute("stroke-width","0.15625");
                                            child_g.setAttribute("stroke-linecap","round");
                                            child_g.setAttribute("marker-end","url(#arrowhead-g)");
                                            child_g.setAttribute("opacity","1");
                                            child_g.setAttribute("x1", x1);
                                            child_g.setAttribute("y1", y1);
                                            child_g.setAttribute("x2", x2);
                                            child_g.setAttribute("y2", y2);
                                            child_g.setAttribute("cgHash", `${size}, ${size},` + src + `,` + dst + `,green`);

                                            g.appendChild(child_g);

                                            """,
        transform[0],
        transform[1],
        transform[2],
        transform[3],
        board_size,
        src,
        dst,
    )


# theres 2 approaches
# 1. recreate board and moves every time a new move is made
# 2. just update board with each move as it happens
# recreating every time can maybe account for takebacks/etc or some other bugs, but not sure if its necessary


def play_game(board, our_color):
    global make_move

    logger.info(f"Starting play_game as {our_color}")

    try:
        WebDriverWait(driver, 600).until(
            ec.presence_of_element_located((By.CLASS_NAME, "ready"))
        )
        move_handle = driver.find_element(By.CLASS_NAME, "ready")
        logger.info("Found move input handle")
    except Exception as e:
        logger.error(f"Failed to find move input handle: {e}")
        return

    try:
        _engine = chess.engine.SimpleEngine.popen_uci(config["engine"]["Path"])
        logger.info(f"Started chess engine: {config['engine']['Path']}")
    except Exception as e:
        logger.error(f"Failed to start chess engine: {e}")
        return

    # add any additional UCI options
    _engine.configure(
        {
            "Skill Level": int(config["engine"]["Skill Level"]),
            "Hash": int(config["engine"]["Hash"]),
        }
    )
    logger.info(
        f"Engine configured - Skill: {config['engine']['Skill Level']}, Hash: {config['engine']['Hash']}"
    )

    logger.info("Setting up initial position")
    move_number = get_previous_moves(board)
    logger.info(f"Ready to play. Starting at move number: {move_number}")

    # while game is in progress (no rematch/analysis button, etc)
    while not check_exists_by_class("follow-up"):
        our_turn = False

        if board.turn and our_color == "W":
            our_turn = True
        elif not board.turn and our_color == "B":
            our_turn = True

        previous_move_number = move_number

        need_draw_arrow = True

        # only get best move once
        if our_turn:
            logger.info(
                f"Our turn - calculating best move (depth: {config['engine']['Depth']})"
            )

            # Small delay before engine starts thinking (more natural)
            humanized_delay(0.3, 1.0, "engine thinking")

            result = _engine.play(
                board,
                chess.engine.Limit(depth=int(config["engine"]["Depth"])),
                game=object,
                info=chess.engine.INFO_NONE,
            )
            logger.info(f"Engine suggests: {result.move}")

        while our_turn:
            if previous_move_number != move_number:
                logger.debug("Move number changed, breaking from our turn loop")
                break

            # check for made move
            move_xpath = (
                "/html/body/div[2]/main/div[1]/rm6/l4x/kwdb[" + str(move_number) + "]"
            )
            move = check_exists_by_xpath(move_xpath)
            if not move:
                # Try alternative selectors
                move = find_move_by_alternatives(move_number)

            if move:
                logger.info(f"Our move detected on board at position {move_number}")
                clear_arrow()

                move_text = move.text.strip()

                # Validate move before trying to parse it
                try:
                    # Check if move is legal in current position
                    test_move = board.parse_san(move_text)
                    if test_move in board.legal_moves:
                        uci = board.push_san(move_text)
                        logger.info(f"Move {ceil(move_number / 2)}: {uci.uci()} [us]")
                        print(
                            str(ceil(move_number / 2)) + ". " + str(uci.uci()) + " [us]"
                        )
                        move_number += 1
                    else:
                        logger.warning(
                            f"Our move '{move_text}' is not legal in current position"
                        )
                        save_debug_info(move_number, board)
                        return
                except Exception as e:
                    logger.error(f"Invalid our move notation '{move_text}': {e}")
                    save_debug_info(move_number, board)
                    return

            else:
                # Show arrow if enabled
                if config["general"]["arrow"] == "true" and need_draw_arrow:
                    logger.debug("Showing move suggestion arrow")
                    draw_arrow(result, our_color)
                    need_draw_arrow = False

                # Check AutoPlay setting
                autoplay = config["general"].get("AutoPlay", "false").lower() == "true"

                if autoplay:
                    # Automatic play mode
                    logger.info(f"AutoPlay enabled - making move: {result.move}")

                    # Humanized delay before making the move
                    humanized_delay(1.0, 3.0, "move execution")

                    clear_arrow()
                    make_move = False

                    logger.info(f"Move {ceil(move_number / 2)}: {result.move} [us]")
                    print(
                        str(ceil(move_number / 2)) + ". " + str(result.move) + " [us]"
                    )

                    board.push(result.move)

                    # Humanized typing delay
                    humanized_delay(0.3, 0.8, "move input")

                    move_handle.send_keys(Keys.RETURN)
                    move_handle.clear()

                    # Type move with slight delay
                    humanized_delay(0.2, 0.5, "typing move")
                    move_handle.send_keys(str(result.move))

                    move_number += 1
                else:
                    # Manual/suggestion mode - check for key press
                    move_key = config["general"].get(
                        "movekey", config["general"].get("MoveKey", "")
                    )
                    if make_move:
                        logger.info(
                            f"Manual key press detected - making move: {result.move}"
                        )

                        # Humanized delay for manual move
                        humanized_delay(0.5, 1.5, "manual move execution")

                        clear_arrow()
                        make_move = False

                        logger.info(f"Move {ceil(move_number / 2)}: {result.move} [us]")
                        print(
                            str(ceil(move_number / 2))
                            + ". "
                            + str(result.move)
                            + " [us]"
                        )

                        board.push(result.move)

                        humanized_delay(0.3, 0.8, "move input")
                        move_handle.send_keys(Keys.RETURN)
                        move_handle.clear()

                        humanized_delay(0.2, 0.5, "typing move")
                        move_handle.send_keys(str(result.move))

                        move_number += 1
                    else:
                        # Just suggesting - show the move and wait
                        logger.debug(
                            f"Suggesting move: {result.move} (press {move_key} to execute)"
                        )
                        print(
                            f"💡 Suggested move: {result.move} (press {move_key} to execute)"
                        )
                        sleep(0.1)  # Small delay to avoid spam
            # sleep(0.1)  # if you want to see the board update
        else:
            clear_arrow()
            opp_move_xpath = (
                "/html/body/div[2]/main/div[1]/rm6/l4x/kwdb[" + str(move_number) + "]"
            )
            opp_moved = check_exists_by_xpath(opp_move_xpath)
            if not opp_moved:
                # Try alternative selectors
                opp_moved = find_move_by_alternatives(move_number)

            if opp_moved:
                opp_move_text = opp_moved.text.strip()

                # Validate move before trying to parse it
                try:
                    # Check if move is legal in current position
                    test_move = board.parse_san(opp_move_text)
                    if test_move in board.legal_moves:
                        uci = board.push_san(opp_move_text)
                        logger.info(
                            f"Opponent move {ceil(move_number / 2)}: {uci.uci()}"
                        )
                        print(str(ceil(move_number / 2)) + ". " + uci.uci())
                        move_number += 1
                    else:
                        logger.warning(
                            f"Move '{opp_move_text}' is not legal in current position"
                        )
                        save_debug_info(move_number, board)
                        return
                except Exception as e:
                    logger.error(f"Invalid move notation '{opp_move_text}': {e}")
                    save_debug_info(move_number, board)
                    return

    # sleep(0.1)  # if you want to see the board update

    # Game complete
    logger.info("Game completed - follow-up element detected")
    _engine.quit()
    logger.info("Chess engine stopped")
    print("[INFO] :: Game complete. Waiting for new game to start.")
    new_game(board)


def get_board_square_size():
    board_style = driver.find_element(
        By.XPATH, "/html/body/div[2]/main/div[1]/div[1]/div/cg-container"
    ).get_attribute("style")
    board_size = re.search(r"\d+", board_style).group()
    piece_size = int(board_size) * 0.125  # / 8
    return piece_size


def get_piece_transform(move, our_color):
    files = ["1", "2", "3", "4", "5", "6", "7", "8"]
    ranks = ["a", "b", "c", "d", "e", "f", "g", "h"]

    rank_values_w = [
        ("a", -3.5),
        ("b", -2.5),
        ("c", -1.5),
        ("d", -0.5),
        ("e", 0.5),
        ("f", 1.5),
        ("g", 2.5),
        ("h", 3.5),
    ]
    file_values_w = [
        (1, 3.5),
        (2, 2.5),
        (3, 1.5),
        (4, 0.5),
        (5, -0.5),
        (6, -1.5),
        (7, -2.5),
        (8, -3.5),
    ]

    rank_values_b = [
        ("a", 3.5),
        ("b", 2.5),
        ("c", 1.5),
        ("d", 0.5),
        ("e", -0.5),
        ("f", -1.5),
        ("g", -2.5),
        ("h", -3.5),
    ]
    file_values_b = [
        (1, -3.5),
        (2, -2.5),
        (3, -1.5),
        (4, -0.5),
        (5, 0.5),
        (6, 1.5),
        (7, 2.5),
        (8, 3.5),
    ]

    move_str = str(move)
    _from = str(move_str[:2])
    _to = str(move_str[2:])

    a1 = 0
    a2 = 0

    for i, pair in enumerate(rank_values_w if our_color == "W" else rank_values_b):
        if pair[0] == _from[0]:
            a1 = i
            break

    for i, pair in enumerate(file_values_w if our_color == "W" else file_values_b):
        if pair[0] == int(_from[1]):
            a2 = i
            break

    src_x = rank_values_w[a1][1] if our_color == "W" else rank_values_b[a1][1]
    src_y = file_values_w[a2][1] if our_color == "W" else file_values_b[a2][1]

    b1 = 0
    b2 = 0

    for i, pair in enumerate(rank_values_w if our_color == "W" else rank_values_b):
        if pair[0] == _to[0]:
            b1 = i
            break

    for i, pair in enumerate(file_values_w if our_color == "W" else file_values_b):
        if pair[0] == int(_to[1]):
            b2 = i
            break

    dst_x = rank_values_w[b1][1] if our_color == "W" else rank_values_b[b1][1]
    dst_y = file_values_w[b2][1] if our_color == "W" else file_values_b[b2][1]

    return [src_x, src_y, dst_x, dst_y]


def sign_in():
    logger.info("Starting sign-in process")

    # Signing in
    try:
        signin_button = driver.find_element(
            by=By.XPATH, value="/html/body/header/div[2]/a"
        )
        signin_button.click()
        logger.info("Clicked sign-in button")
    except Exception as e:
        logger.error(f"Failed to find/click sign-in button: {e}")
        return

    try:
        username = driver.find_element(By.ID, "form3-username")
        password = driver.find_element(By.ID, "form3-password")
        logger.info("Found username and password fields")

        username.send_keys(config["lichess"]["Username"])
        password.send_keys(config["lichess"]["Password"])
        logger.info(f"Entered credentials for user: {config['lichess']['Username']}")

        driver.find_element(By.XPATH, "/html/body/div/main/form/div[1]/button").click()
        logger.info("Submitted login form")
    except Exception as e:
        logger.error(f"Failed during login form submission: {e}")
        return


def create_config():
    config["engine"] = {
        "Path": get_stockfish_path(),
        "Depth": "5",
        "Hash": "2048",
        "Skill Level": "14",
    }
    config["lichess"] = {"Username": "user", "Password": "pass"}
    config["general"] = {
        "MoveKey": "end",
        "arrow": "true",
        "AutoPlay": "true",
    }

    with open("config.ini", "w") as configfile:
        config.write(configfile)


def humanized_delay(min_seconds=0.5, max_seconds=2.0, action="action"):
    """Add a humanized delay between actions"""
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Humanized delay for {action}: {delay:.2f}s")
    sleep(delay)


def clear_screen():
    """Clear the terminal screen on both Windows and Unix-like systems"""
    os.system("cls" if os.name == "nt" else "clear")


def setup_debug_folder():
    """Create debug folder and clean up old files"""
    debug_dir = "debug"

    # Create debug folder if it doesn't exist
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)
        logger.info(f"Created debug folder: {debug_dir}")

    # Clean up old debug files
    try:
        debug_files = glob.glob(os.path.join(debug_dir, "*"))
        if debug_files:
            for file_path in debug_files:
                os.remove(file_path)
            logger.info(f"Cleaned up {len(debug_files)} old debug files")
        else:
            logger.info("No old debug files to clean up")
    except Exception as e:
        logger.warning(f"Failed to clean up debug files: {e}")


def save_debug_info(move_number, board=None):
    """Save debugging information when stuck"""
    try:
        debug_dir = "debug"
        timestamp = int(time.time())

        # Save screenshot
        screenshot_path = os.path.join(
            debug_dir, f"screenshot_move{move_number}_{timestamp}.png"
        )
        driver.save_screenshot(screenshot_path)
        logger.info(f"Saved screenshot to {screenshot_path}")

        # Save page source
        html_path = os.path.join(debug_dir, f"page_move{move_number}_{timestamp}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info(f"Saved page HTML to {html_path}")

        # Save board state if available
        if board:
            board_path = os.path.join(
                debug_dir, f"board_move{move_number}_{timestamp}.txt"
            )
            with open(board_path, "w") as f:
                f.write(f"Current board FEN: {board.fen()}\n")
                f.write(f"Board state:\n{board}\n")
                f.write(f"Legal moves: {[str(move) for move in board.legal_moves]}\n")
                f.write(f"Turn: {'White' if board.turn else 'Black'}\n")
                f.write(f"Move number: {move_number}\n")
            logger.info(f"Saved board state to {board_path}")

        # Log current URL
        logger.info(f"Current URL: {driver.current_url}")

    except Exception as e:
        logger.error(f"Failed to save debug info: {e}")


def main():
    clear_screen()
    setup_debug_folder()
    logger.info("Starting chess bot application")

    config_exists = os.path.isfile("./config.ini")

    if config_exists:
        config.read("config.ini")
        logger.info("Loaded existing config.ini")
    else:
        logger.info("No config.ini found, creating default config")
        create_config()
        config.read("config.ini")

    # Log current configuration
    autoplay = config["general"].get("AutoPlay", "false").lower() == "true"
    move_key = config["general"].get("movekey", config["general"].get("MoveKey", "end"))

    if autoplay:
        logger.info("🤖 AutoPlay MODE: Bot will make moves automatically")
    else:
        logger.info(
            f"💭 Suggestion MODE: Bot will suggest moves (press '{move_key}' to execute)"
        )

    logger.info("Starting keyboard listener")
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    logger.info("Initializing chess board")
    board = chess.Board()

    logger.info("Navigating to lichess.org")
    driver.get("https://www.lichess.org")

    sign_in()

    logger.info("Waiting for game to start")
    new_game(board)


if __name__ == "__main__":
    main()
