# SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""CircuitPython Essentials HID Keyboard example"""

import board
import digitalio
import busio
import usb_hid
from adafruit_hid.mouse import Mouse
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

KB_EVT_START = 248
MOUSE_EVT_START = 249
KEY_SEQUENCE_EVT_START = 250
EVT_END = 251
KB_EVT_TYPE_KEYDOWN = 1
KB_EVT_TYPE_KEYUP = 2
KB_EVT_TYPE_RESET = 3
MOUSE_EVT_TYPE_MOVE = 1
MOUSE_EVT_TYPE_LEFT_DOWN = 2
MOUSE_EVT_TYPE_LEFT_UP = 3
MOUSE_EVT_TYPE_MIDDLE_DOWN = 4
MOUSE_EVT_TYPE_MIDDLE_UP = 5
MOUSE_EVT_TYPE_RIGHT_DOWN = 6
MOUSE_EVT_TYPE_RIGHT_UP = 7
MOUSE_EVT_TYPE_WHEEL = 8
MOUSE_EVT_TYPE_RESET = 9
MOUSE_EVT_TYPE_CONFIG_MOVE_FACTOR = 10
R_BUF_LEN = 32
ARDUINO_TO_KEYCODES = {
    "128": Keycode.CONTROL,
    "129": Keycode.SHIFT,
    "130": Keycode.ALT,
    "131": Keycode.GUI,
    "179": Keycode.TAB,
    "193": Keycode.CAPS_LOCK,
    "178": Keycode.BACKSPACE,
    "176": Keycode.ENTER,
    "237": Keycode.APPLICATION,
    "209": Keycode.INSERT,
    "212": Keycode.DELETE,
    "210": Keycode.HOME,
    "213": Keycode.END,
    "211": Keycode.PAGE_UP,
    "214": Keycode.PAGE_DOWN,
    "218": Keycode.UP_ARROW,
    "217": Keycode.DOWN_ARROW,
    "216": Keycode.LEFT_ARROW,
    "215": Keycode.RIGHT_ARROW,
    "206": Keycode.PRINT_SCREEN,
    "207": Keycode.SCROLL_LOCK,
    "208": Keycode.PAUSE,
    "177": Keycode.ESCAPE,
}
#F1-F12
for i in range(12):
    key=str(194+i)
    ARDUINO_TO_KEYCODES[key] = 112+i
led = False
rBuf = [0] * R_BUF_LEN
rBufCursor = 0
mouseMoveFactor = 1
tx = board.GP0
rx = board.GP1
ser = busio.UART(tx, rx, baudrate=9600)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
kb = Keyboard(usb_hid.devices)
ms = Mouse(usb_hid.devices)
kb_layout = KeyboardLayoutUS(kb)


def led_on():
    led.value = True


def led_off():
    led.value = False


def parse_r_buf():
    global rBuf, rBufCursor, mouseMoveFactor
    if rBuf[0] == KB_EVT_START and rBufCursor == 3:
        if rBuf[1] == KB_EVT_TYPE_KEYDOWN:
            if rBuf[2] < 126:
                aa = kb_layout.keycodes(chr(rBuf[2]))
                for i in aa:
                    kb.press(i)
            else:
                aa = ARDUINO_TO_KEYCODES[str(rBuf[2])]
#                print(str(rBuf[2]))
                kb.press(aa)

        elif rBuf[1] == KB_EVT_TYPE_KEYUP:
            if rBuf[2] < 126:
                aa = kb_layout.keycodes(chr(rBuf[2]))
                for i in aa:
                    kb.release(i)
            else:
                aa = ARDUINO_TO_KEYCODES[str(rBuf[2])]
                kb.release(aa)

        elif rBuf[1] == KB_EVT_TYPE_RESET:
            kb.release_all()
    elif rBuf[0] == MOUSE_EVT_START and rBufCursor == 4:
        if rBuf[1] == MOUSE_EVT_TYPE_MOVE:
            ms.move(
                (rBuf[2] - 120) * mouseMoveFactor, (rBuf[3] - 120) * mouseMoveFactor
            )
        elif rBuf[1] == MOUSE_EVT_TYPE_LEFT_DOWN:
            ms.press(Mouse.LEFT_BUTTON)
        elif rBuf[1] == MOUSE_EVT_TYPE_LEFT_UP:
            ms.release(Mouse.LEFT_BUTTON)
        elif rBuf[1] == MOUSE_EVT_TYPE_RIGHT_DOWN:
            ms.press(Mouse.RIGHT_BUTTON)
        elif rBuf[1] == MOUSE_EVT_TYPE_RIGHT_UP:
            ms.release(Mouse.RIGHT_BUTTON)
        elif rBuf[1] == MOUSE_EVT_TYPE_MIDDLE_DOWN:
            ms.press(Mouse.MIDDLE_BUTTON)
        elif rBuf[1] == MOUSE_EVT_TYPE_MIDDLE_UP:
            ms.release(Mouse.MIDDLE_BUTTON)
        elif rBuf[1] == MOUSE_EVT_TYPE_WHEEL:
            ms.move(0, 0, rBuf[2] - 120)
        elif rBuf[1] == MOUSE_EVT_TYPE_RESET:
            ms.release_all()
        elif rBuf[1] == MOUSE_EVT_TYPE_CONFIG_MOVE_FACTOR:
            mouseMoveFactor = rBuf[2]
    elif rBuf[0] == KEY_SEQUENCE_EVT_START and rBufCursor > 1:
        kb.release_all()
        for i in range(1,rBufCursor):
            kb_layout.write(chr(rBuf[i]))


def reset_r_buf():
    global rBuf, rBufCursor
    rBufCursor = 0
    rBuf[0] = 0


while True:
    curVal = ser.read(1)
    if curVal is None or len(curVal) == 0:
        continue
    curVal = ord(curVal)
    if curVal == EVT_END:
        led_on()
        parse_r_buf()
        reset_r_buf()
        led_off()
    else:
        if rBufCursor == 0:
            if (
                curVal == KB_EVT_START
                or curVal == MOUSE_EVT_START
                or curVal == KEY_SEQUENCE_EVT_START
            ):
                rBuf[rBufCursor] = curVal
                rBufCursor += 1
        else:
            if rBufCursor < R_BUF_LEN:
                rBuf[rBufCursor] = curVal
                rBufCursor += 1
            else:
                rBuf[0] = 0
