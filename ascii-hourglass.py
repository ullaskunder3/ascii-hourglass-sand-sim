import random, sys, time, os

# Enable ANSI escape sequences on Windows
if os.name == 'nt':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

PAUSE_LENGTH = 0.2
WIDE_FALL_CHANCE = 50

SCREEN_WIDTH = 79
SCREEN_HEIGHT = 25
X, Y = 0, 1
SAND = chr(9617)
WALL = chr(9608)

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

def main():
    total_time = get_user_time()

    clear_screen()
    move_cursor(0, 0)
    print("Ctrl-C to quit.", end='')

    for wall in HOURGLASS:
        move_cursor(wall[X], wall[Y])
        print(WALL, end='')

    all_sand = list(INITIAL_SAND)
    for sand in all_sand:
        move_cursor(sand[X], sand[Y])
        print(SAND, end='')

    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed >= total_time:
            break
        run_simulation_step(all_sand)

    move_cursor(0, SCREEN_HEIGHT)
    print("\nTime's up! Exiting...")

def run_simulation_step(all_sand):
    random.shuffle(all_sand)
    sand_moved = False

    for i, sand in enumerate(all_sand):
        below = (sand[X], sand[Y] + 1)

        if below in HOURGLASS or sand[Y] >= SCREEN_HEIGHT - 2:
            continue

        if below not in all_sand and below not in HOURGLASS:
            if sand not in HOURGLASS:
                move_cursor(*sand)
                print(' ', end='')
            move_cursor(*below)
            print(SAND, end='')
            all_sand[i] = below
            sand_moved = True
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
                print(SAND, end='')
                all_sand[i] = new_pos
                sand_moved = True

    sys.stdout.flush()
    time.sleep(PAUSE_LENGTH)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        move_cursor(0, SCREEN_HEIGHT)
        print('\nExiting...')
