"""Game Result Popup - Simple messagebox for game results"""

from tkinter import messagebox


def show_game_result(result_data: dict):
    """Show game result using simple messagebox"""
    score = result_data.get("score", "Score not available")
    reason = result_data.get("reason", "Result details not available")
    our_color = result_data.get("our_color", "unknown")
    move_count = result_data.get("move_count", 0)

    # Build the message
    title = "🏁 Game Finished"

    # Add move count if available
    stats = f"\nTotal moves: {move_count}" if move_count > 0 else ""

    message = f"{score}\n\n{reason}{stats}"

    # Determine message type based on result
    if any(word in score.lower() for word in ["won", "victory", "1-0", "0-1"]):
        if ("1-0" in score and our_color.lower() == "white") or (
            "0-1" in score and our_color.lower() == "black"
        ):
            # We won
            messagebox.showinfo(title, message)
        else:
            # We lost
            messagebox.showwarning(title, message)
    elif "1/2-1/2" in score or "draw" in score.lower():
        # Draw
        messagebox.showinfo(title, message)
    else:
        # Unknown result
        messagebox.showinfo(title, message)
