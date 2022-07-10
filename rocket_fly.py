import asyncio
import curses
from itertools import cycle
import os
import random
import time

from curses_tools import draw_frame, read_controls, get_frame_size
from game_scenario import PHRASES, get_garbage_delay_tics 
from explosion import explode
from obstacles import Obstacle


coroutines = []
obstacles = []
obstacles_in_last_collision = []
year = 1957
is_gameover = False


def read_from_file(filename):
    with open(filename) as file:
        return file.read()


def create_frames_from_files_in_dir(directory=""):
    try:
        files = os.listdir(directory)
        frames = [read_from_file(os.path.join(directory, file)) for file in files]
        if not frames:
            raise FileNotFoundError("Directory is empty.")
        return frames
    except FileNotFoundError as e:
        print(e.strerror)
        exit(1)


async def sleep_coroutine(sleep_time):
    for _ in range(sleep_time):
        await asyncio.sleep(0)


async def increment_year(canvas):
    global year
    start_time = time.time()
    canvas.addstr(0, 1, str(year))
    while True:
        if is_gameover:
            return
        if time.time() - start_time >= 1.5:
            year += 1
            start_time = time.time()
            canvas.addstr(0, 1, " "*4)
            await sleep_coroutine(1)
            canvas.addstr(0, 1, str(year))
        else:
            await sleep_coroutine(1)


async def show_text(canvas):
    global year, is_gameover
    center_row, center_column = (value//2 for value in canvas.getmaxyx())
    while True:
        if is_gameover:
            return
        if year in PHRASES:
            event_text = PHRASES.get(year)
            text_column = center_column - len(event_text)//2
            canvas.addstr(center_row, text_column, event_text, curses.A_BOLD)
            time.sleep(0.3)
            await sleep_coroutine(4) 
            canvas.addstr(center_row, text_column, " "*len(event_text))
        else:
            await sleep_coroutine(1)


async def show_gameover(canvas):
    global is_gameover
    center_row, center_column = (max_coord//2 for max_coord in canvas.getmaxyx())
    gameover_frame = read_from_file("game_over.txt")
    gameover_frame_size = get_frame_size(gameover_frame)
    gameover_row, gameover_column = center_row - gameover_frame_size[0]//2, center_column - gameover_frame_size[1]//2
    is_gameover = True
    while True:
        draw_frame(canvas, gameover_row, gameover_column, gameover_frame)
        await sleep_coroutine(3)


async def fly_garbage(canvas, column, garbage_frame, frame_size_row, frame_size_column, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay
    same, as specified on start."""
    global coroutines, obstacles, obstacles_in_last_collision
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    obstacle = Obstacle(row, column, frame_size_row, frame_size_column)
    obstacles.append(obstacle)

    while row < rows_number:
        if obstacle in obstacles_in_last_collision:
            obstacles_in_last_collision.remove(obstacle)
            obstacles.remove(obstacle)
            coroutines.append(explode(canvas, row, column))
            return
        draw_frame(canvas, row, column, garbage_frame)
        await sleep_coroutine(2)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacle.row = row
    obstacles.remove(obstacle)


# TODO: change behaviour of press space and arrows. They must be not required
async def animate_spaceship(canvas, row, column, frames: list):
    """
    Animate spaceship that flying in stars sky.
    """
    global coroutines, obstacles, year
    if isinstance(frames, list):
        frames_iter = cycle(frames)
        max_row, max_col = canvas.getmaxyx()
        for frame in frames_iter:
            row_area, col_area = get_frame_size(frame)
            for obstacle in obstacles:
                if obstacle.has_collision(row, column, row_area, col_area):
                    coroutines.append(show_gameover(canvas))
                    return
            row_direction, col_direction, is_space_press = read_controls(canvas)
            row += row_direction
            column += col_direction
            if is_space_press and year >= 2020:
                column_of_ships_bow = column+2
                fire_coro = fire(canvas, row, column_of_ships_bow)
                coroutines.append(fire_coro)
            if (row <= 0 and (0 <= column + col_area <= max_col or 0 <= column - col_area <= max_col)):
                row = 0
            elif (row+row_area > max_row and (0 <= column + col_area <= max_col or 0 <= column - col_area <= max_col)):
                row = max_row-row_area
            elif (column <= 0 and (0 <= row + row_area <= max_row or 0 <= row - row_area <= max_row)):
                column = 0
            elif (column + col_area > max_col and (0 <= row + row_area <= max_row or 0 <= row - row_area <= max_row)):
                column = max_col-col_area
            draw_frame(canvas, row, column, frame)
            await sleep_coroutine(4)
            draw_frame(canvas, row, column, frame, negative=True)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""
    global obstacles_in_last_collision

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep_coroutine(3)

    canvas.addstr(round(row), round(column), 'O')
    await sleep_coroutine(3)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collision.append(obstacle)
                return
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*', wait_before_repeat=15):
    while True:
        await sleep_coroutine(wait_before_repeat)
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep_coroutine(20)

        canvas.addstr(row, column, symbol)
        await sleep_coroutine(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep_coroutine(5)

        canvas.addstr(row, column, symbol)
        await sleep_coroutine(3)


async def fill_orbit_with_garbage(canvas, max_column):
    global year
    garbage_frames = create_frames_from_files_in_dir("garbage_frame")
    while True:
        delay_tics = get_garbage_delay_tics(year)
        if not delay_tics:
            await sleep_coroutine(1)
            continue
        game_pace, speed = delay_tics
        garbage_frame = random.choice(garbage_frames)
        frame_size_row, frame_size_column = get_frame_size(garbage_frame)
        random_column = random.randint(0+frame_size_column, max_column - frame_size_column)
        coroutines.append(fly_garbage(canvas, random_column, garbage_frame, frame_size_row, frame_size_column, speed=speed))
        await sleep_coroutine(game_pace)


def draw(canvas):
    global coroutines, obstacles
    max_row, max_column = curses.window.getmaxyx(canvas)
    derwin_row, derwin_column = max_row - 2, max_column - 8
    year_win = canvas.derwin(0, 7, derwin_row, derwin_column)
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)

    count_of_coroutines = 200
    start_generated_row = 2
    end_generated_row = max_row-2
    start_generated_column = 3
    end_generated_column = max_column-2
    stars = {}

    rocket_frames = create_frames_from_files_in_dir("rocket_frame")
    spaceship_coro = animate_spaceship(canvas, max_row/2, max_column/2, rocket_frames)
    fill_orbit = fill_orbit_with_garbage(canvas=canvas, max_column=max_column)
    year_coro = increment_year(year_win)
    event_text_coro = show_text(canvas)
    while count_of_coroutines:
        row, column = (
            random.randint(start_generated_row, end_generated_row),
            random.randint(start_generated_column, end_generated_column)
        )
        star_symb = random.choice('+*.:')
        if (row, column) in stars:
            continue
        else:
            stars[(row, column)] = star_symb
            count_of_coroutines -= 1
        wait_before_repeat = random.randint(0, 30)
        coroutines.append(blink(canvas, row, column, star_symb, wait_before_repeat))

    coroutines.append(spaceship_coro)
    coroutines.append(fill_orbit)
    coroutines.append(year_coro)
    coroutines.append(event_text_coro)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        year_win.refresh()
        time.sleep(0.05)
        if not coroutines:
            break


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)

