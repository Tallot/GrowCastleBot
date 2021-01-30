# coding: utf-8

import time
import random

import cv2
import keyboard
import win32api, win32con
from PIL import ImageGrab

# Settings
game_coords = [0, 0, 1650, 910]

bb = (1515, 907) # (255, 255, 255) battle button

giant = (535, 450)
palladin = (535, 540)
angel = (630, 545)
slinger = (725, 550)

dbm = (725, 340, 275) # dark bow master
dh = (535, 340, 275) # dark hunter
s = (445, 340, 275) # stone
e = (630, 215, 165) # elizabeth

cooldown = (84, 188, 255) # spell is ready

c_max = (537, 122, 563, 129) # 6th and 0th points: (255, 255, 255), (243, 243, 243)
invest = 10
tower_menu = (625, 635)
lightning_tower = (625, 305, 1400, 465)
minigun = (625, 425, 1400, 280)
ballista = (625, 545, 1400, 595)
lvl_up = (1240, 645)
close_lvl_menu = (1355, 295)
close_tower_menu = (1615, 200)


def click(x, y):
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
    time.sleep(0.5)

while keyboard.is_pressed('w') == False:
    screen = ImageGrab.grab(bbox=game_coords).load()

    if screen[bb[0], bb[1]][0] == 255:
    # Check if crystals are at max and spend them
        if screen[c_max[0], c_max[1]][0] == 191:
            print('Crystals at max!')
            tower = random.randint(0, 2)
            click(*tower_menu)
            if tower == 0:
                click(lightning_tower[0], lightning_tower[1])
                click(lightning_tower[2], lightning_tower[3])
            elif tower == 1:
                click(minigun[0], minigun[1])
                click(minigun[2], minigun[3])
            else:
                click(ballista[0], ballista[1])
                click(ballista[2], ballista[3])
            for _ in range(invest):
                click(*lvl_up)
            click(*close_lvl_menu)
            click(*close_tower_menu)
        click(*bb) # Run battle
        time.sleep(2.5)
        click(*giant)
        click(*palladin)
        click(*angel)
        click(*slinger)
    # use spells while in battle
    if screen[dbm[0], dbm[2]][0] == cooldown[0]:
        click(dbm[0], dbm[1])
    if screen[dh[0], dh[2]][0] == cooldown[0]:
        click(dh[0], dh[1])
    if screen[s[0], s[2]][0] == cooldown[0]:
        click(s[0], s[1])
    if screen[e[0], e[2]][0] == cooldown[0]:
        click(e[0], e[1])