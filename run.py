# coding: utf-8

import time
import random

import cv2
import keyboard
import win32api, win32con, win32gui
from PIL import ImageGrab
import numpy as np

from pprint import pprint
from skimage.metrics import structural_similarity as ssim

# Constants
first_cell_ratio = (0.234, 0.132)
first_cell_cd_ratio = (0.229, 0.071)
between_cells_ratio = (0.062, 0.13)
donate_cell_ratio = (0.168, 0.265)
donate_cell_cd_ratio = (0.166, 0.205)
altar_cell_ratio = (0.096, 0,308)

battle_button_ratio = (0.931, 0.922)
wave_skip_close_ratio = (0.695, 0.323)

castle_ratio = {'lightning_castle': (0.803, 0.435), 'minigun': (0.803, 0.214), 'ballista': (0.803, 0.576)}
castle_menu_close_ratio = (0.954, 0.105)
castle_level_up_ratio = (0.702, 0.66)
castle_close_level_up_ratio = (0.777, 0.222)
crystals_rect_ratio = (0.225, 0.004, 0.257, 0.051)

left_border_shift = 2
upper_border_shift = 42
lower_border_shift = -2
right_border_shift = -2
right_border_sidebar_shift = -62

cooldown_rgb = (84, 188, 255) # (83, 186, 252)
battle_button_rgb = (191, 185, 172)
crystals_max = np.load('60_crystals.npy')

# User configs
sidebar_used = False
active_hero_cells = [1, 3, 5, 6, 9, 10, 11]
donate_cell = True
use_altar = False
invest_crystals = 20
invest_towers = {0: 'lightning_castle', 1: 'minigun', 2: 'ballista'}
interval_between_clicks = 0.4
# feature: spell_usages = [True, True, True, True, False, False, False, False] # activate skill only once at the begging or by cd

def get_window_handle(window_title='BlueStacks'):
    hwnd = win32gui.FindWindow(None, window_title)
    return hwnd

def get_game_field_coords(hwnd, left_border_shift, upper_border_shift, lower_border_shift, right_border_shift):
    x0, y0, x1, y1 = win32gui.GetWindowRect(hwnd)
    x0 += left_border_shift
    y0 += upper_border_shift
    x1 += right_border_shift
    y1 += lower_border_shift
    return (x0, y0, x1, y1)

def change_screen(hwnd, x_pos, y_pos, width, height):
    # x_pos, y_pos - upper left corner
    # width, height - desired window size

    # win32gui.SetForegroundWindow(hwnd)
    win32gui.MoveWindow(hwnd, x_pos, y_pos, x_pos + width, y_pos + height, True)

def prepare_positions(coords):
    width = coords[2] - coords[0]
    height = coords[3] - coords[1]

    heroes = []
    for cell in active_hero_cells:
        cell_pos = cell % 3, cell // 3 # Column and row
        click_pos = round((first_cell_ratio[0] + cell_pos[0] * between_cells_ratio[0]) * width) + coords[0], \
            round((first_cell_ratio[1] + cell_pos[1] * between_cells_ratio[1]) * height) + coords[1]
        cd_bar_loc = [round((first_cell_cd_ratio[0] + cell_pos[0] * between_cells_ratio[0]) * width) + coords[0],
            round((first_cell_cd_ratio[1] + cell_pos[1] * between_cells_ratio[1]) * height) + coords[1]]
        heroes.append((click_pos, cd_bar_loc))

    if donate_cell:
        donate_click_pos = round(donate_cell_ratio[0] * width) + coords[0], round(donate_cell_ratio[1] * height) + coords[1]
        donate_cd_bar_loc = [round(donate_cell_cd_ratio[0] * width) + coords[0], round(donate_cell_cd_ratio[1] * height) + coords[1]]
        heroes.append((donate_click_pos, donate_cd_bar_loc))

    battle_button_pos = round(battle_button_ratio[0] * width) + coords[0], round(battle_button_ratio[1] * height) + coords[1]
    wave_skip_close_pos = round(wave_skip_close_ratio[0] * width) + coords[0], round(wave_skip_close_ratio[1] * height) + coords[1]

    crystals_rect = round(crystals_rect_ratio[0] * width), round(crystals_rect_ratio[1] * height), \
                    round(crystals_rect_ratio[2] * width), round(crystals_rect_ratio[3] * height)

    towers = []
    for key, val in invest_towers.items():
        tower_pos = 1, key + 1
        click_pos = round((first_cell_ratio[0] + tower_pos[0] * between_cells_ratio[0]) * width) + coords[0], \
            round((first_cell_ratio[1] + tower_pos[1] * between_cells_ratio[1]) * height) + coords[1]
        menu_click_pos = round(castle_ratio[val][0] * width) + coords[0], round(castle_ratio[val][1] * height) + coords[1]
        towers.append((click_pos, menu_click_pos))

    castle_button_pos = round((first_cell_ratio[0] + between_cells_ratio[0]) * width) + coords[0], round((first_cell_ratio[1] + 4 * between_cells_ratio[1]) * height) + coords[1]

    castle_menu_close = round(castle_menu_close_ratio[0] * width) + coords[0], round(castle_menu_close_ratio[1] * height) + coords[1]

    castle_level_up = round(castle_level_up_ratio[0] * width) + coords[0], round(castle_level_up_ratio[1] * height) + coords[1]
    castle_close_level_up = round(castle_close_level_up_ratio[0] * width) + coords[0], round(castle_close_level_up_ratio[1] * height) + coords[1]

    return heroes, battle_button_pos, wave_skip_close_pos, crystals_rect, towers, castle_button_pos, castle_menu_close, castle_level_up, castle_close_level_up

def check_cd_bar_pos(coords, heroes):
    # approxamation errors can exceed correct boundary of cooldown bar
    # grab image once and test, if out of boundary (wrong rgb) then try a few shifts (down and up) and update location
    screen = ImageGrab.grab(bbox=coords)
    screen = np.transpose(np.array(screen), axes=(1, 0, 2))
    for hero in heroes:
        for px in (0, 1, -1, 2, -2, 3, -3, 4, -4):
            if screen[hero[1][0] - coords[0], hero[1][1] - coords[1] + px][0] == cooldown_rgb[0]:
                hero[1][1] += px
                break
            if px == -4:
                raise RuntimeError('Could not locate cooldown bar for hero:', hero)

def mse(a, b):
	# NOTE: the two images must have the same dimension
	error = np.sum((a.astype(np.float32) - b.astype(np.float32)) ** 2)
	error /= (a.shape[0] * b.shape[1])

	return error

def click(x, y):
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

def click_n_wait(x, y, interval=0.4):
    click(x, y)
    time.sleep(interval)

def run_bot(coords, heroes, battle_button_pos, wave_skip_close_pos, crystals_rect, towers, castle_button_pos,
            castle_menu_close, castle_level_up, castle_close_level_up):
    screen = ImageGrab.grab(bbox=coords)
    screen = np.transpose(np.array(screen), axes=(1, 0, 2))
    if screen[battle_button_pos[0] - coords[0], battle_button_pos[1] - coords[1]][0] == battle_button_rgb[0]:
        crystals = screen[crystals_rect[0]:crystals_rect[2], crystals_rect[1]:crystals_rect[3], :]
        crystals = cv2.cvtColor(crystals, cv2.COLOR_BGR2GRAY)
        crystals = cv2.resize(crystals, crystals_max.shape[::-1], interpolation = cv2.INTER_AREA)

        if ssim(crystals, crystals_max) > 0.7:
            print('Crystals at max!')
            print(ssim(crystals, crystals_max))
            tower = random.choice(towers)
            click_n_wait(*castle_button_pos)
            click_n_wait(*(tower[0]))
            click_n_wait(*(tower[1]))
            for _ in range(invest_crystals):
                click_n_wait(*castle_level_up)
            click_n_wait(*castle_close_level_up)
            click_n_wait(*castle_menu_close)
        click_n_wait(*battle_button_pos)
        click_n_wait(*wave_skip_close_pos)

    for hero in heroes:
        if screen[hero[1][0] - coords[0], hero[1][1] - coords[1]][0] == cooldown_rgb[0]:
            click(*(hero[0]))
            time.sleep(0.05)

if __name__ == '__main__':
    hwnd = get_window_handle()
    if sidebar_used:
        right_border_shift = right_border_sidebar_shift
    coords = get_game_field_coords(hwnd, left_border_shift, upper_border_shift, lower_border_shift, right_border_shift)

    heroes, battle_button_pos, wave_skip_close_pos, crystals_rect, towers, castle_button_pos, \
        castle_menu_close, castle_level_up, castle_close_level_up = prepare_positions(coords)
    check_cd_bar_pos(coords, heroes)

    while keyboard.is_pressed('w') == False:
        run_bot(coords, heroes, battle_button_pos, wave_skip_close_pos, crystals_rect, towers, castle_button_pos,
            castle_menu_close, castle_level_up, castle_close_level_up)