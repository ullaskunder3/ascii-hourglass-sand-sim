import random, sys, time, os
import threading
import glob
import json
import itertools
import textwrap

# Enable ANSI escape sequences on Windows
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

# Try to import pygame for audio playback
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame not found. Music playback will be disabled.")
    print("To install: pip install pygame")
    time.sleep(2)

# Add to the top of the imports
try:
    from hourglass_stats import HourglassStats
    STATS_AVAILABLE = True
except ImportError:
    STATS_AVAILABLE = False
    print("Statistics module not found. Usage tracking disabled.")
    print("Make sure hourglass_stats.py is in the same directory.")
    time.sleep(2)

PAUSE_LENGTH = 0.2
WIDE_FALL_CHANCE = 50

SCREEN_WIDTH = 79
SCREEN_HEIGHT = 25
X, Y = 0, 1
SAND = chr(9617)  # Sand character
WALL = chr(9608)  # Wall character

# ANSI color codes
SAND_COLOR = "\033[38;5;222m"  # Light sand color
WALL_COLOR = "\033[38;5;250m"   # Light grey for the hourglass frame
RESET_COLOR = "\033[0m"         # Reset to default color

# Color the sand and wall characters
COLORED_SAND = f"{SAND_COLOR}{SAND}{RESET_COLOR}"
COLORED_WALL = f"{WALL_COLOR}{WALL}{RESET_COLOR}"

# File to save progress
PROGRESS_FILE = "hourglass_progress.json"

# Time tracking functions
def load_progress():
    """Load saved progress from file"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                # Return elapsed time, timestamp, music track, and music position
                return (
                    data.get('elapsed', 0), 
                    data.get('timestamp', 0),
                    data.get('music_track', 0),
                    data.get('music_position', 0)
                )
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or can't be read, start fresh
            return 0, 0, 0, 0
    return 0, 0, 0, 0

def save_progress(elapsed, music_track=0, music_position=0):
    """Save current progress to file"""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            data = {
                'elapsed': elapsed,
                'timestamp': time.time(),
                'music_track': music_track,
                'music_position': music_position
            }
            json.dump(data, f)
    except IOError:
        print("Warning: Could not save progress")

def clear_progress():
    """Clear saved progress (e.g., when timer completes)"""
    if os.path.exists(PROGRESS_FILE):
        try:
            os.remove(PROGRESS_FILE)
        except IOError:
            print("Warning: Could not clear progress file")

# Music player class using pygame
class MusicPlayer:
    def __init__(self, music_folder="music"):
        self.music_folder = music_folder
        self.playlist = []
        self.current_track = 0
        self.playing = False
        self.thread = None
        self.start_pos = 0  # Position to start playback from (in seconds)
        
        if PYGAME_AVAILABLE:
            pygame.mixer.init()
            self.load_playlist()
    
    def load_playlist(self):
        # Get all audio files from the music folder
        extensions = ['.mp3', '.wav', '.ogg']
        for ext in extensions:
            self.playlist.extend(glob.glob(os.path.join(self.music_folder, f'*{ext}')))
        
        if not self.playlist:
            print(f"No music files found in '{self.music_folder}' folder.")
            print(f"Place MP3, WAV, or OGG files in a folder called '{self.music_folder}'.")
            time.sleep(2)
    
    def set_position(self, track_index, position_seconds):
        """Set which track and position to start from"""
        if track_index < len(self.playlist):
            self.current_track = track_index
        else:
            self.current_track = 0
            
        self.start_pos = position_seconds
    
    def get_position(self):
        """Get current track index and position in seconds"""
        if not PYGAME_AVAILABLE or not self.playlist:
            return 0, 0
            
        position = 0
        if pygame.mixer.music.get_busy():
            # This is an approximation since pygame doesn't expose exact position
            position = pygame.mixer.music.get_pos() / 1000.0  # Convert ms to seconds
            
        return self.current_track, position
    
    def play_next(self):
        if not PYGAME_AVAILABLE or not self.playlist:
            return
            
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            
        if self.current_track >= len(self.playlist):
            self.current_track = 0
            
        try:
            pygame.mixer.music.load(self.playlist[self.current_track])
            
            # Start from specified position if needed
            if self.start_pos > 0:
                pygame.mixer.music.play(start=self.start_pos)
                self.start_pos = 0  # Reset for next track
            else:
                pygame.mixer.music.play()
                
            self.current_track += 1
        except Exception as e:
            print(f"Error playing track: {e}")
            time.sleep(1)
            self.current_track += 1
            self.play_next()
    
    def player_loop(self):
        while self.playing:
            if not pygame.mixer.music.get_busy() and self.playing:
                self.play_next()
            time.sleep(0.5)
    
    def start(self):
        if not PYGAME_AVAILABLE or not self.playlist:
            return
            
        self.playing = True
        self.play_next()
        self.thread = threading.Thread(target=self.player_loop)
        self.thread.daemon = True  # Thread will exit when main program exits
        self.thread.start()
    
    def stop(self):
        if not PYGAME_AVAILABLE:
            return
            
        self.playing = False
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

# Clear screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Move cursor
def move_cursor(x, y):
    print(f'\033[{y+1};{x+1}H', end='')

# Draw hourglass
HOURGLASS = set()
for i in range(18, 37):
    HOURGLASS.add((i, 1))
    HOURGLASS.add((i, 23))
for i in range(1, 5):
    HOURGLASS.add((18, i))
    HOURGLASS.add((36, i))
    HOURGLASS.add((18, i + 19))
    HOURGLASS.add((36, i + 19))
for i in range(8):
    HOURGLASS.add((19 + i, 5 + i))
    HOURGLASS.add((35 - i, 5 + i))
    HOURGLASS.add((25 - i, 13 + i))
    HOURGLASS.add((29 + i, 13 + i))

# Initial sand
INITIAL_SAND = set()
for y in range(8):
    for x in range(19 + y, 36 - y):
        INITIAL_SAND.add((x, y + 4))

def get_user_time():
    while True:
        try:
            h = int(input("Enter hours (0 or more): "))
            m = int(input("Enter minutes (0-59): "))
            s = int(input("Enter seconds (0-59): "))
            if h < 0 or m < 0 or m > 59 or s < 0 or s > 59:
                print("Please enter valid time values.")
                continue
            total_seconds = h * 3600 + m * 60 + s
            if total_seconds == 0:
                print("Time must be greater than zero.")
                continue
            return total_seconds
        except ValueError:
            print("Please enter integer values.")

# Add these constants near the other constants
MARQUEE_Y = 20  # Y position for the marquee
MARQUEE_WIDTH = 30  # Width of the marquee text area
QUOTES_FILE = "hourglass_quotes.json"  # File containing quotes
MARQUEE_SPEED = 0.2  # How many seconds between marquee updates

# Add this function to load quotes from the file
def load_quotes():
    """Load quotes from the quotes file."""
    default_quotes = ["Focus on the present moment... Breathe... Be mindful..."]
    
    if not os.path.exists(QUOTES_FILE):
        # Create a default quotes file if it doesn't exist
        try:
            with open(QUOTES_FILE, 'w') as f:
                json.dump({"quotes": default_quotes}, f, indent=2)
        except IOError:
            print(f"Warning: Could not create quotes file")
        return default_quotes
        
    try:
        with open(QUOTES_FILE, 'r') as f:
            data = json.load(f)
            quotes = data.get('quotes', [])
            if not quotes:  # If quotes list is empty
                return default_quotes
            return quotes
    except (json.JSONDecodeError, IOError):
        print(f"Warning: Could not read quotes file")
        return default_quotes

# Add this function to handle the marquee display
def update_marquee(text, position, width):
    """Update the marquee text at the bottom of the hourglass."""
    # Create a circular text buffer by doubling the text
    circular_text = text + " " + text
    
    # Extract the visible portion based on current position
    visible_text = circular_text[position:position+width]
    
    # If the visible portion is too short, wrap around
    if len(visible_text) < width:
        visible_text += circular_text[:width-len(visible_text)]
    
    # Center the text in the bottom of the hourglass
    x_start = 27 - width//2  # Center position (adjust based on your hourglass)
    
    # Clear the marquee area
    for x in range(x_start, x_start + width):
        move_cursor(x, MARQUEE_Y)
        print(' ', end='')
    
    # Print the visible text
    move_cursor(x_start, MARQUEE_Y)
    print(visible_text, end='')
    
    # Return the next position
    return (position + 1) % len(text)

def main():
    # Create and start the music player
    music_player = MusicPlayer()
    
    # Set a fixed time of 1 hour (3600 seconds)
    total_time = 3600
    
    # Load saved progress
    saved_elapsed, saved_timestamp, saved_track, saved_position = load_progress()
    
    # Make sure saved time is valid
    if saved_elapsed >= total_time:
        saved_elapsed = 0  # Reset if we've completed a full hour already
    
    # Set music position if we have saved data
    if saved_track > 0 or saved_position > 0:
        music_player.set_position(saved_track, saved_position)
    
    # Start the music player after setting the position
    music_player.start()
    
    # Display saved progress if any
    if saved_elapsed > 0:
        minutes_left = int((total_time - saved_elapsed) / 60)
        print(f"Resuming from previous session with {minutes_left} minutes remaining.")
        time.sleep(2)
    
    clear_screen()
    
    # Draw the hourglass frame
    for wall in HOURGLASS:
        move_cursor(wall[X], wall[Y])
        print(COLORED_WALL, end='')

    # Draw initial sand
    all_sand = list(INITIAL_SAND)
    for sand in all_sand:
        move_cursor(sand[X], sand[Y])
        print(COLORED_SAND, end='')

    start_time = time.time() - saved_elapsed  # Adjust start time based on saved progress
    
    # Count the total number of sand particles
    total_sand_count = len(all_sand)
    
    # Track sand that has passed the narrow passage
    falling_sand = set()
    
    # Load quotes and select one randomly
    quotes = load_quotes()
    current_quote = random.choice(quotes)
    
    # Add marquee variables
    marquee_position = 0
    last_marquee_update = time.time()
    marquee_change_time = time.time() + 30  # Change quote every 30 seconds
    
    try:
        while True:
            elapsed = time.time() - start_time
            remaining = total_time - elapsed
            
            current_time = time.time()
            
            # Change quote periodically
            if current_time >= marquee_change_time:
                current_quote = random.choice(quotes)
                marquee_position = 0  # Reset position for new quote
                marquee_change_time = current_time + 30  # Next change in 30 seconds
            
            # Update marquee when enough time has passed
            if current_time - last_marquee_update >= MARQUEE_SPEED:
                marquee_position = update_marquee(current_quote, marquee_position, MARQUEE_WIDTH)
                last_marquee_update = current_time
            
            # Count sand in different sections
            sand_in_top = 0
            sand_in_middle = 0
            sand_in_bottom = 0
            
            for sand in all_sand:
                if sand[Y] <= 11:  # Top half
                    sand_in_top += 1
                elif 12 <= sand[Y] <= 13:  # Middle neck
                    sand_in_middle += 1
                else:  # Bottom half
                    sand_in_bottom += 1
                    
            # Calculate how many sand particles should have fallen by now
            elapsed_fraction = elapsed / total_time
            target_sand_in_bottom = int(total_sand_count * elapsed_fraction)
            
            # Update the set of sand that should keep falling
            for i, sand in enumerate(all_sand):
                if sand[Y] > 11 and sand[Y] < 16:  # Sand in or just past the neck
                    falling_sand.add(i)
                    
            # Decide whether to allow sand to flow from top
            allow_top_flow = sand_in_bottom < target_sand_in_bottom
            
            # Always run simulation for falling sand and optionally for top sand
            run_simulation_step(all_sand, falling_sand, allow_top_flow)
            
            # If we're way behind schedule, let more sand through
            if sand_in_bottom < target_sand_in_bottom - 5:
                time.sleep(0.05)  # Less delay to catch up
            elif sand_in_bottom > target_sand_in_bottom + 5:
                time.sleep(0.3)  # More delay to slow down
            else:
                time.sleep(0.1)  # Normal delay
            
            if elapsed >= total_time:
                # Timer completed, clear progress file
                clear_progress()
                break
    except KeyboardInterrupt:
        # Get current music position before saving
        current_track, current_position = music_player.get_position()
        
        # Save progress when the user interrupts with Ctrl-C
        save_progress(elapsed, current_track, current_position)
        
        # Update statistics
        if STATS_AVAILABLE:
            stats = HourglassStats()
            stats.update_stats(elapsed)
            
        move_cursor(0, SCREEN_HEIGHT)
        print("\nProgress saved. Run again to resume.")
        sys.exit(0)
    finally:
        # Track statistics if the module is available
        if STATS_AVAILABLE:
            stats = HourglassStats()
            stats.update_stats(elapsed)
            
        # Clean up when done
        music_player.stop()
        move_cursor(0, SCREEN_HEIGHT)
        print("\nTime's up! Exiting...")

def run_simulation_step(all_sand, falling_sand, allow_top_flow):
    # Process sand indices in random order
    indices = list(range(len(all_sand)))
    random.shuffle(indices)
    
    sand_moved = False

    for i in indices:
        sand = all_sand[i]
        
        # Determine if this sand grain is allowed to move
        # Always allow sand that's already falling or in bottom half
        # Only allow top sand to flow if we're behind schedule
        is_falling = i in falling_sand
        is_in_top = sand[Y] <= 11
        
        if is_in_top and not allow_top_flow and not is_falling:
            continue
            
        below = (sand[X], sand[Y] + 1)

        if below in HOURGLASS or sand[Y] >= SCREEN_HEIGHT - 2:
            continue

        if below not in all_sand and below not in HOURGLASS:
            if sand not in HOURGLASS:
                move_cursor(*sand)
                print(' ', end='')
            move_cursor(*below)
            print(COLORED_SAND, end='')
            all_sand[i] = below
            sand_moved = True
            
            # If this was top sand and it just moved past Y=11, mark it as falling
            if is_in_top and below[Y] > 11:
                falling_sand.add(i)
                
            continue

        left, right = (sand[X] - 1, sand[Y]), (sand[X] + 1, sand[Y])
        below_left = (sand[X] - 1, sand[Y] + 1)
        below_right = (sand[X] + 1, sand[Y] + 1)

        can_left = (
            sand[X] > 0 and
            below_left not in all_sand and
            below_left not in HOURGLASS and
            left not in HOURGLASS
        )
        can_right = (
            sand[X] < SCREEN_WIDTH - 1 and
            below_right not in all_sand and
            below_right not in HOURGLASS and
            right not in HOURGLASS
        )

        fall_dir = None
        if can_left and not can_right:
            fall_dir = -1
        elif not can_left and can_right:
            fall_dir = 1
        elif can_left and can_right:
            fall_dir = random.choice([-1, 1])

        if random.randint(0, 100) < WIDE_FALL_CHANCE:
            two_left = (sand[X] - 2, sand[Y] + 1)
            two_right = (sand[X] + 2, sand[Y] + 1)

            if fall_dir == -1 and two_left not in all_sand and two_left not in HOURGLASS:
                fall_dir = -2
            elif fall_dir == 1 and two_right not in all_sand and two_right not in HOURGLASS:
                fall_dir = 2

        if fall_dir is not None:
            new_x = sand[X] + fall_dir
            new_y = sand[Y] + 1
            new_pos = (new_x, new_y)

            if new_pos not in HOURGLASS and new_y < SCREEN_HEIGHT - 1:
                if sand not in HOURGLASS:
                    move_cursor(*sand)
                    print(' ', end='')
                move_cursor(new_x, new_y)
                print(COLORED_SAND, end='')
                all_sand[i] = new_pos
                sand_moved = True
                
                # If this was top sand and it just moved past Y=11, mark it as falling
                if is_in_top and new_y > 11:
                    falling_sand.add(i)

    sys.stdout.flush()
    
    # Always have a small delay for visual smoothness
    if sand_moved:
        time.sleep(PAUSE_LENGTH)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # This should not be reached as we catch KeyboardInterrupt in main()
        # But it's here as a fallback
        move_cursor(0, SCREEN_HEIGHT)
        print('\nExiting...')
