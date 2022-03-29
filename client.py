import threading
import time

import pygame
import random
import socket
import pickle

"""
10 x 20 square grid
shapes: S, Z, I, O, J, L, T
represented in order by 0 - 6
"""

pygame.font.init()

# GLOBALS VARS
s_width = 1200
s_height = 750
play_width = 300  # meaning 300 // 10 = 30 width per block
play_height = 600  # meaning 600 // 20 = 30 height per block
block_size = 30
top_left_y = s_height - play_height - 30

opponent_grid = None
high_score = 0

host = "127.0.0.1"  # localhost
port = 55555

# SHAPE FORMATS

S = [['.....',
      '......',
      '..00..',
      '.00...',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '...0.',
      '.....']]

Z = [['.....',
      '.....',
      '.00..',
      '..00.',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '.0...',
      '.....']]

I = [['..0..',
      '..0..',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '0000.',
      '.....',
      '.....',
      '.....']]

O = [['.....',
      '.....',
      '.00..',
      '.00..',
      '.....']]

J = [['.....',
      '.0...',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..00.',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '...0.',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '.00..',
      '.....']]

L = [['.....',
      '...0.',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '..00.',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '.0...',
      '.....'],
     ['.....',
      '.00..',
      '..0..',
      '..0..',
      '.....']]

T = [['.....',
      '..0..',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '..0..',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '..0..',
      '.....']]

shapes = [S, Z, I, O, J, L, T]
shape_colors = [(0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 255, 0), (255, 165, 0), (0, 0, 255), (128, 0, 128)]


# index 0 - 6 represent shape


class Piece(object):
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = shape_colors[shapes.index(shape)]
        self.rotation = 0


def create_grid(locked_positions={}):
    grid = [[(0, 0, 0) for x in range(10)] for x in range(20)]  # initialize grid with 10 * 20 with each grid color (0, 0, 0)

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if (j, i) in locked_positions:
                c = locked_positions[(j, i)]
                grid[i][j] = c
    return grid


def convert_shape_format(shape):
    positions = []
    format = shape.shape[shape.rotation % len(shape.shape)]

    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == "0":
                positions.append((shape.x + j, shape.y + i))

    for i, position in enumerate(positions):
        positions[i] = (position[0] - 2, position[1] - 4)

    return positions


def valid_space(shape, grid):
    # flatten 2d list to 1d list e.g. 20x10 -> 200x1
    # grid[i][j] == (0, 0, 0) is to check whether the position has existing block already
    accepted_position = [[(j, i) for j in range(10) if grid[i][j] == (0, 0, 0)] for i in range(20)]
    accepted_position = [j for sub in accepted_position for j in sub]

    formatted = convert_shape_format(shape)

    for pos in formatted:
        if pos not in accepted_position:
            if pos[1] > -1:
                return False
    return True


def check_lost(positions):
    for pos in positions:
        x, y = pos
        if y < 1:
            return True

    return False


def get_shape():
    return Piece(5, 0, random.choice(shapes))


def draw_text_middle(surface, text, size, color):
    font = pygame.font.SysFont("comicsans", size, bold=True)
    label = font.render(text, 1, color)

    surface.blit(label, (s_width // 2 - label.get_width() / 2,
                         s_height // 2 - label.get_height() / 2))


def draw_grid(surface, grid, top_left_x):
    sx = top_left_x
    sy = top_left_y

    for i in range(len(grid)):
        pygame.draw.line(surface, (128, 128, 128), (sx, sy + i * block_size), (sx + play_width, sy + i * block_size))
        for j in range(len(grid[i])):
            pygame.draw.line(surface, (128, 128, 128), (sx + j * block_size, sy), (sx + j * block_size, sy + play_height))


def clear_rows(grid, locked_positions):
    increment = 0
    for i in range(len(grid) - 1, -1, -1):
        row = grid[i]

        if (0, 0, 0) not in row:
            increment += 1
            row_index = i
            for j in range(len(row)):
                try:
                    del locked_positions[(j, i)]
                except:
                    continue

    if increment > 0:
        for key in sorted(list(locked_positions), key=lambda x: x[1])[::-1]:
            x, y = key
            if y < row_index:   # only shift the blocks above the row index with increment value
                new_key = (x, y + increment)
                locked_positions[new_key] = locked_positions.pop(key)

    return increment


def draw_next_shape(shape, surface, top_left_x, multiplayer):
    font = pygame.font.SysFont("comicsans", 30)
    label = font.render("Next Shape", 1, (255, 255, 255))

    if multiplayer:
        sx = top_left_x + play_width * 2 + 100
    else:
        sx = top_left_x + play_width + 50
    sy = top_left_y + play_height / 2 - 120
    format = shape.shape[shape.rotation % len(shape.shape)]

    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == "0":
                pygame.draw.rect(surface, shape.color, (sx + j * 30 + 15, sy + i * 30 + 25, block_size, block_size))

    surface.blit(label, (sx + 10, sy - 30))


def draw_window(surface, player_grid, multi_player, top_left_x, opp_top_left_x, score=0, high_score=0):
    surface.fill((0, 0, 0))

    pygame.font.init()
    font = pygame.font.SysFont("comicsans", 40)
    player_label = font.render("You", True, (255, 255, 255))    # Can further change to player's nickname
    opp_label = font.render("Opponent", True, (255, 255, 255))    # Can further change to opponent's nickname

    surface.blit(player_label, (top_left_x + play_width / 2 - (player_label.get_width() / 2), 30))  # middle of the screen
    if multi_player:
        surface.blit(opp_label, (opp_top_left_x + play_width / 2 - (opp_label.get_width() / 2), 30))  # middle of the screen

    # print current score
    font = pygame.font.SysFont("comicsans", 30)
    label = font.render("Score: {0}".format(score), True, (255, 255, 255))

    if multi_player:
        sx = top_left_x + play_width * 2 + 100
    else:
        sx = top_left_x + play_width + 50
    sy = top_left_y + play_height / 2 - 100

    surface.blit(label, (sx + 20, sy + 160))

    # print last score
    label = font.render("High score: {0}".format(high_score), True, (255, 255, 255))

    sx = top_left_x - 250
    sy = top_left_y + 100

    surface.blit(label, (sx + 10, sy + 160))

    for i in range(len(player_grid)):
        for j in range(len(player_grid[i])):
            pygame.draw.rect(surface, player_grid[i][j], (top_left_x + j * block_size, top_left_y + i * block_size, block_size, block_size), 0)
            if multi_player:
                pygame.draw.rect(surface, opponent_grid[i][j], (opp_top_left_x + j * block_size, top_left_y + i * block_size, block_size, block_size), 0)

        pygame.draw.rect(surface, (255, 0, 0), (top_left_x, top_left_y, play_width + 1, play_height), 4)
        if multi_player:
            pygame.draw.rect(surface, (255, 0, 0), (opp_top_left_x, top_left_y, play_width + 1, play_height), 4)

    draw_grid(surface, player_grid, top_left_x)
    if multi_player:
        draw_grid(surface, opponent_grid, opp_top_left_x)


def main(win, multi_player, client):
# def main(win, multi_player):
    if multi_player:
        top_left_x = s_width // 2 - play_width - 30
    else:
        top_left_x = (s_width - play_width) // 2
    opp_top_left_x = s_width // 2 - play_width + 300

    locked_positions = {}
    change_piece = False
    run = True
    current_piece = get_shape()
    next_piece = get_shape()
    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 0.27
    level_time = 0
    score = 0

    global opponent_grid
    opponent_grid = create_grid(locked_positions)

    while run:
        player_grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()    # get time since last clock.tick()
        level_time += clock.get_rawtime()
        clock.tick()

        if level_time / 1000 > 5:
            level_time = 0
            if fall_speed > 0.12:   # max speed = 0.27 - 0.12 = 0.15
                fall_speed -= 0.005

        if fall_time / 1000 > fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not (valid_space(current_piece, player_grid)) and current_piece.y > 0:   # piece is not at the top
                current_piece.y -= 1
                change_piece = True     # lock the piece and generate another piece

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not (valid_space(current_piece, player_grid)):
                        current_piece.x += 1
                if event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not (valid_space(current_piece, player_grid)):
                        current_piece.x -= 1
                if event.key == pygame.K_DOWN:
                    current_piece.y += 1
                    if not (valid_space(current_piece, player_grid)):
                        current_piece.y -= 1
                if event.key == pygame.K_UP:
                    current_piece.rotation += 1
                    if not (valid_space(current_piece, player_grid)):
                        current_piece.rotation -= 1

        shape_positions = convert_shape_format(current_piece)

        for i in range(len(shape_positions)):
            x, y = shape_positions[i]
            if y > -1:
                player_grid[y][x] = current_piece.color

        if change_piece:
            for position in shape_positions:
                pos = (position[0], position[1])
                locked_positions[pos] = current_piece.color    # append frozen pieces to locked positions dict
            current_piece = next_piece
            next_piece = get_shape()
            change_piece = False
            score += clear_rows(player_grid, locked_positions) * 10

        draw_window(win, player_grid, multi_player, top_left_x, opp_top_left_x, score, high_score)
        draw_next_shape(next_piece, win, top_left_x, multi_player)

        if multi_player:
            client.send(pickle.dumps(player_grid))

            data = pickle.loads(client.recv(16384))

            if data == "Lost":
                draw_text_middle(win, "YOU WIN!", 80, (255, 255, 255))
                pygame.display.update()
                pygame.time.delay(1500)
                run = False
                client.send(pickle.dumps("Score,{0}".format(score)))
            else:
                opponent_grid = data

        pygame.display.update()

        if check_lost(locked_positions):
            draw_text_middle(win, "YOU LOST!", 80, (255, 255, 255))
            client.send(pickle.dumps("Lost"))

            pygame.display.update()
            pygame.time.delay(1500)
            run = False
            client.send(pickle.dumps("Score,{0}".format(score)))


def ready(client):
    run = True

    while run:
        message = pickle.loads(client.recv(1024))
        if message == "Game start":
            print(message)
            run = False

    main(win, True, client)
    pygame.display.quit()


def waiting_room(win):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))

    message = client.recv(1024).decode()
    if message == "Connected to the server":
        print(message)

        win.fill((0, 0, 0))
        draw_text_middle(win, "Please wait for another player", 60, (255, 255, 255))
        pygame.display.update()

        while True:
            message = client.recv(1024).decode()
            if "Game start" in message:
                print("Game start")

                global high_score
                high_score = int(message.split(',')[1].strip())

                break

        main(win, True, client)
        pygame.display.quit()

    else:
        print("Connection error")
        client.close()


win = pygame.display.set_mode((s_width, s_height))
pygame.display.set_caption("Tetris")

waiting_room(win)  # start game
