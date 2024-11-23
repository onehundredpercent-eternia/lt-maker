TILEWIDTH, TILEHEIGHT = 16, 16
TILEX, TILEY = 15, 10
WINWIDTH, WINHEIGHT = int(TILEX * TILEWIDTH), int(TILEY * TILEHEIGHT)
PORTRAIT_WIDTH, PORTRAIT_HEIGHT = 128, 112
COLORKEY = 128, 160, 128
FPS = 60
FRAMERATE = 1000//FPS

AUTOTILE_FRAMES = 16

VERSION = "2023.11.30a"

if __name__ == '__main__':
    print(VERSION)

APP_AUTHOR = "rainlash"
APP_NAME = "Lex Talionis"

# (left, top, right, bottom)
left = 10
right = WINWIDTH - 24
top = 10
bottom = WINHEIGHT - 56
center = WINWIDTH // 2

arrow_height_offset = 3

side_button_offset = 6
top_button_y_offset = 8

A_POS = (right + side_button_offset, bottom)
B_POS = (right - 16, bottom + 16 + side_button_offset)
Y_POS = (right - 32 - side_button_offset, bottom)
X_POS = (right - 16, bottom - 16 - side_button_offset)
L_POS = (left - 2, top - top_button_y_offset)
R_POS = (right - 2, top - top_button_y_offset)
START_POS = (center - 20, bottom + 36)
LEFT_POS = (left - side_button_offset, bottom - arrow_height_offset)
RIGHT_POS = (left + 32 + side_button_offset, bottom - arrow_height_offset)
UP_POS = (left + 16, bottom - 16 - arrow_height_offset - side_button_offset)
DOWN_POS = (left + 16, bottom + 16 - arrow_height_offset + side_button_offset)
