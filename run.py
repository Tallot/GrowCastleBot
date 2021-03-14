# coding: utf-8

import random

import cv2
import keyboard
import numpy as np
import win32gui
import win32ui
from skimage.metrics import structural_similarity as ssim

from constants import Indicators, Ratios
from utils import (get_game_screen_hwnd, grab_screen, send_click,
                   send_click_n_wait)

FPS = 30

# User configs
active_hero_cells = [1, 3, 5, 6, 7, 8, 9, 10, 11]
donate_cell = True
use_altar = False
invest_crystals = 20
invest_castles = {0: 'lightning_castle', 1: 'minigun', 2: 'ballista'}
interval_between_clicks = 0.4


def abs_pos(x_rel, y_rel, width, height):
    return round(x_rel * width), round(y_rel * height)


def get_obj_positions(hero_cells, donate_cell, castle_cells, width, height):
    heroes = []
    for cell in hero_cells:
        cell_offset = np.array([cell % 3, cell // 3])  # Column and row

        rel_click_pos = Ratios.FIRST_CELL_CENTER + cell_offset * Ratios.DST_BTWN_CELLS_CENTERS
        click_pos = abs_pos(*rel_click_pos, width, height)

        rel_cd_bar_pos = Ratios.FIRST_CELL_CD_BAR + cell_offset * Ratios.DST_BTWN_CELLS_CENTERS
        cd_bar_pos = abs_pos(*rel_cd_bar_pos, width, height)

        heroes.append((*click_pos, *cd_bar_pos))

    if donate_cell:
        click_pos = abs_pos(*Ratios.DONATE_CELL_CENTER, width, height)
        cd_bar_pos = abs_pos(*Ratios.DONATE_CELL_CD_BAR, width, height)
        heroes.append((*click_pos, *cd_bar_pos))

    altar = abs_pos(*Ratios.ALTAR_CELL_CENTER, width, height)

    castles = []
    for key, val in castle_cells.items():
        tower_offset = np.array([1, 1 + key])

        rel_click_pos = Ratios.FIRST_CELL_CENTER + tower_offset * Ratios.DST_BTWN_CELLS_CENTERS
        click_pos = abs_pos(*rel_click_pos, width, height)

        menu_click_pos = abs_pos(*Ratios.CASTLE_MENU_BUTTONS[val], width, height)

        castles.append((*click_pos, *menu_click_pos))

    castle_level_up_button = abs_pos(*Ratios.CASTLE_LEVEL_UP_BUTTON, width, height)
    castle_level_up_menu_close_button = abs_pos(*Ratios.CASTLE_LEVEL_UP_MENU_CLOSE_BUTTON, width, height)
    castle_menu_button = abs_pos(*(Ratios.FIRST_CELL_CENTER + Ratios.DST_BTWN_CELLS_CENTERS * np.array([1, 4])),
                                 width, height)
    castle_menu_close_button = abs_pos(*Ratios.CASTLE_MENU_CLOSE_BUTTON, width, height)

    battle_button = abs_pos(*Ratios.BATTLE_BUTTON, width, height)
    wave_skip_close_button = abs_pos(*Ratios.WAVE_SKIP_CLOSE_BUTTON, width, height)
    crystals_amount_bbox = abs_pos(*Ratios.CRYSTALS_AMOUNT_BBOX[:2], width, height) \
        + abs_pos(*Ratios.CRYSTALS_AMOUNT_BBOX[2:], width, height)

    game_objects = {
        'heroes': heroes,
        'altar': altar,
        'castles': castles,
        'castle_level_up_button': castle_level_up_button,
        'castle_level_up_menu_close_button': castle_level_up_menu_close_button,
        'castle_menu_button': castle_menu_button,
        'castle_menu_close_button': castle_menu_close_button,
        'battle_button': battle_button,
        'wave_skip_close_button': wave_skip_close_button,
        'crystals_amount_bbox': crystals_amount_bbox
    }

    return game_objects


def get_puzzle_obj_positions(width, height):
    circle_center = np.array(abs_pos(*Ratios.CIRCLE_CENTER, width, height))

    # Counter clockwise
    angles = [
        0., np.pi/4, np.pi/2, 3*np.pi/4,
        np.pi, 5*np.pi/4, 3*np.pi/2, 7*np.pi/4
    ]
    bbox_axes_distances = [Ratios.BBOX_CIRCLE_CENTERS_DST *
                           np.array([np.cos(alpha), np.sin(alpha)]) for alpha in angles]
    bbox_centers = [circle_center +
                    abs_pos(*dist, width, width) for dist in bbox_axes_distances]
    bbox_size = round(Ratios.BBOX_SIZE * width)
    bboxes = [(bbox_center[0]-bbox_size, bbox_center[1]-bbox_size,
               2*bbox_size, 2*bbox_size) for bbox_center in bbox_centers]

    crystal_axes_distances = [Ratios.CRYSTAL_CIRCLE_CENTERS_DST *
                              np.array([np.cos(alpha), np.sin(alpha)]) for alpha in angles]
    crystal_centers = [circle_center +
                       abs_pos(*dist, width, width) for dist in crystal_axes_distances]

    puzzle_start_button = abs_pos(*Ratios.PUZZLE_START_BUTTON, width, height)

    return {'bboxes': bboxes, 'crystal_centers': crystal_centers, 'puzzle_start_button': puzzle_start_button}


def check_cd_bar_pos(screen, heroes):
    # Approxamation errors can exceed correct boundary of cooldown bar
    # Grab image once and test, if out of boundary (wrong rgb)
    # then try a few shifts (down and up) and update location
    for hero in heroes:
        for px in (0, 1, -1, 2, -2, 3, -3, 4, -4):
            if screen[hero[3], hero[2] + px][2] == Indicators.COOLDOWN_BAR_RGB[0]:
                hero[3] += px
                break
            if px == -4:
                raise RuntimeError('Could not locate cooldown bar for hero:',
                                   hero)


def run_bot(hwnd, game_objects, puzzle_objects, invest_crystals=5):
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    save_bitmap = win32ui.CreateBitmap()
    save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(save_bitmap)

    # check_cd_pos(game_objects['heroes'])

    # last_time = time.time()
    while 'Screen capturing':
        # delta =  time.time() - last_time
        # if delta > 1./FPS:
        #     last_time = time.time()
        #     print('fps: {0}'.format(delta))
        #     continue worklfow here

        # Grab game screen
        screen = grab_screen(hwnd, save_dc, save_bitmap)

        # Check if ready to battle
        if screen[game_objects['battle_button'][1], game_objects['battle_button'][0]][2] == Indicators.BATTLE_BUTTON_RGB[0]:
            # Check crystals condition
            crystals = screen[game_objects['crystals_amount_bbox'][1]:game_objects['crystals_amount_bbox'][3],
                              game_objects['crystals_amount_bbox'][0]:game_objects['crystals_amount_bbox'][2]]
            crystals = cv2.cvtColor(crystals, cv2.COLOR_BGR2GRAY)
            crystals = cv2.resize(crystals, Indicators.CRYSTALS_MAX_AMOUNT.shape[::-1],
                                  interpolation=cv2.INTER_AREA)

            if ssim(crystals, Indicators.CRYSTALS_MAX_AMOUNT) > 0.87:
                # if screen[crystals_max[0] - coords[0], crystals_max[1] - coords[1]][0] == crystals_max_rgb[0]:
                print('Crystals at max!')
                castle = random.choice(game_objects['castles'])
                send_click_n_wait(hwnd, *game_objects['castle_menu_button'])
                send_click_n_wait(hwnd, castle[0], castle[1])
                send_click_n_wait(hwnd, castle[2], castle[3])
                for _ in range(invest_crystals):
                    send_click_n_wait(
                        hwnd, *game_objects['castle_level_up_button'], 0.3)
                send_click_n_wait(
                    hwnd, *game_objects['castle_level_up_menu_close_button'])
                send_click_n_wait(
                    hwnd, *game_objects['castle_menu_close_button'])

            # Start battle
            send_click_n_wait(hwnd, *game_objects['battle_button'])

            # Check if puzzle appeard
            screen = grab_screen(hwnd, save_dc, save_bitmap)
            if screen[puzzle_objects['puzzle_start_button'][1], puzzle_objects['puzzle_start_button'][0]][2] == Indicators.PUZZLE_START_BUTTON_RGB[0]:
                # Find crystal
                pos = 0
                for n, crystal_center in enumerate(puzzle_objects['crystal_centers']):
                    if screen[crystal_center[1], crystal_center[0]][0] == Indicators.CRYSTAL_BLUE_CHANNEL:
                        pos = n
                        break
                bbox = puzzle_objects['bboxes'][pos]

                # Initialize tracker
                tracker = cv2.TrackerMOSSE_create()
                tracker.init(screen, bbox)

                send_click(hwnd, *puzzle_objects['puzzle_start_button'])
                for _ in range(150):
                    screen = grab_screen(hwnd, save_dc, save_bitmap)
                    _, detected_bbox = tracker.update(screen)

                choice_click_pos = int(
                    detected_bbox[0] + detected_bbox[2]//2), int(detected_bbox[1] + detected_bbox[3]//2)
                cv2.imwrite('test_bbox.png', cv2.rectangle(screen, (int(detected_bbox[0]), int(detected_bbox[1])), (int(
                    detected_bbox[0]+detected_bbox[2]), int(detected_bbox[1]+detected_bbox[3])), (255, 0, 0), 2))
                send_click_n_wait(hwnd, *choice_click_pos)

            send_click_n_wait(hwnd, *game_objects['wave_skip_close_button'])

        for hero in game_objects['heroes']:
            if screen[hero[3], hero[2]][2] == Indicators.COOLDOWN_BAR_RGB[0]:
                send_click_n_wait(hwnd, hero[0], hero[1], 0.1)

        # Press "w" to exit
        if keyboard.is_pressed('w'):
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            break


if __name__ == '__main__':
    hwnd = get_game_screen_hwnd()
    coords = win32gui.GetWindowRect(hwnd)
    width = coords[2] - coords[0]
    height = coords[3] - coords[1]

    obj_dict = get_obj_positions(active_hero_cells, donate_cell,
                                 invest_castles, width, height)
    puzzle_obj_dict = get_puzzle_obj_positions(width, height)
    run_bot(hwnd, obj_dict, puzzle_obj_dict, invest_crystals)
