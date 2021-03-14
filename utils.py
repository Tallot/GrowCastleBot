# coding: utf-8

import time
from ctypes import windll

import numpy as np
import win32api
import win32con
import win32gui


def create_np_im(buffer, info):
    im = np.frombuffer(buffer, '>u1')
    im = np.delete(im, np.arange(3, im.size, 4))  # remove alpha channel
    np_im = im.reshape((info['bmHeight'], info['bmWidth'], 3))

    return np_im  # BGR scheme


def change_screen(hwnd, x_pos, y_pos, width, height):
    # x_pos, y_pos - upper left corner
    # width, height - desired window size

    win32gui.MoveWindow(hwnd, x_pos, y_pos, x_pos +
                        width, y_pos + height, True)


def send_click(hwnd, x, y):
    lParam = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN,
                         win32con.MK_LBUTTON, lParam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP,
                         win32con.MK_LBUTTON, lParam)


def send_click_n_wait(hwnd, x, y, interval=0.4):
    send_click(hwnd, x, y)
    time.sleep(interval)


def get_game_screen_hwnd(app_window_title='BlueStacks',
                         game_window_title='BlueStacks Android PluginAndroid'):
    parent_hwnd = win32gui.FindWindow(None, app_window_title)

    child_handles = []

    def enum_callaback(hwnd, param):
        child_handles.append(hwnd)

    win32gui.EnumChildWindows(parent_hwnd, enum_callaback, None)
    child_handles_map = {win32gui.GetWindowText(
        child): child for child in child_handles}

    game_hwnd = child_handles_map[game_window_title]

    return game_hwnd


def grab_screen(hwnd, save_dc, save_bitmap):
    '''
    Allows getting graphical content of window that is on background
    '''
    _ = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
    bmpinfo = save_bitmap.GetInfo()
    bmpstr = save_bitmap.GetBitmapBits(True)
    screen = create_np_im(bmpstr, bmpinfo)

    return screen


def mse(a, b):
    # NOTE: the two images must have the same dimension
    error = np.sum((a.astype(np.float32) - b.astype(np.float32)) ** 2)
    error /= (a.shape[0] * b.shape[1])

    return error
