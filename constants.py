# coding: utf-8
'''
Module defines classes with static constant values for game objects detection
'''

import numpy as np


class Ratios:
    '''
    Contains relative positions of interactive game objects
    Should not be changed unless game UI is changed
    '''
    __slots__ = ()  # Prevent dynamic attributes adding

    # Heroes
    FIRST_CELL_CENTER = np.array((0.234, 0.132))
    FIRST_CELL_CD_BAR = np.array((0.229, 0.071))  # CD - CoolDown
    DST_BTWN_CELLS_CENTERS = np.array((0.062, 0.13))
    DONATE_CELL_CENTER = np.array((0.168, 0.265))
    DONATE_CELL_CD_BAR = np.array((0.166, 0.205))

    # Altar
    ALTAR_CELL_CENTER = np.array((0.096, 0.308))

    # Castle
    CASTLE_MENU_BUTTONS = {
        'minigun': np.array((0.803, 0.214)),
        'lightning_castle': np.array((0.803, 0.435)),
        'ballista': np.array((0.803, 0.576))
    }
    CASTLE_LEVEL_UP_BUTTON = np.array((0.702, 0.66))
    CASTLE_LEVEL_UP_MENU_CLOSE_BUTTON = np.array((0.777, 0.222))
    CASTLE_MENU_CLOSE_BUTTON = np.array((0.954, 0.105))

    # General
    BATTLE_BUTTON = np.array((0.931, 0.922))
    WAVE_SKIP_CLOSE_BUTTON = np.array((0.695, 0.323))
    CRYSTALS_AMOUNT_BBOX = np.array((0.222, 0.004, 0.255, 0.051))

    # Puzzle
    CIRCLE_CENTER = np.array((0.479, 0.641))
    BBOX_CIRCLE_CENTERS_DST = 0.082  # 0.079
    BBOX_SIZE = 0.043  # bbox is a square
    CRYSTAL_CIRCLE_CENTERS_DST = 0.1425
    PUZZLE_START_BUTTON = np.array((0.296, 0.907))


class Indicators:
    '''
    Game objects colors that indicate different events (presence/absence of object etc.)
    Should not be changed unless game UI is changed
    '''
    __slots__ = ()  # Prevent dynamic attributes adding

    # Cooldown is ready for hero
    COOLDOWN_BAR_RGB = (84, 188, 255)

    # Battle start is ready
    BATTLE_BUTTON_RGB = (191, 185, 172)

    # Crystals amount panel
    CRYSTALS_MAX_AMOUNT = np.load('./data/60_crystals.npy').T

    # Puzzle
    CRYSTAL_BLUE_CHANNEL = 255
    PUZZLE_START_BUTTON_RGB = (120, 85, 43)
    PUZZLE_END_EVENT_RGB = (89, 87, 73)
