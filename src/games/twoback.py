import time
import pygame as pg
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
CELL_SIZE = 100
PADDING = 15
GRID_CENTER_X = SCREEN_WIDTH // 2
GRID_CENTER_Y = SCREEN_HEIGHT // 2
STIMULUS_DURATION = 1.0
ISI_DURATION = STIMULUS_DURATION # for now

config = {
    "n_back" : 2,
    "use_color" : True,
    "use_spatial" : False,
    "use_audio" : False
}


COLORS = {
    "RED": (220, 50, 50),
    "BLUE": (50, 100, 220),
    "GREEN": (50, 200, 50),
    "YELLOW": (230, 210, 50),
    "BLACK": (0, 0, 0),
    "DARK_GREY": (75, 75, 75),
    "WHITE": (255, 255, 255)
}

ACTIVE_COLORS = ["RED", "BLUE", "GREEN", "YELLOW"]

pg.init()
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pg.display.set_caption("2-Back Game")
clock = pg.time.Clock()


def draw_grid(surface):
    """Draws the 2-back grid centered on the given coordinates."""
    grid_width = CELL_SIZE * 3
    start_x = GRID_CENTER_X - (grid_width // 2)
    start_y = GRID_CENTER_Y - (grid_width // 2)

    line_color = COLORS["DARK_GREY"]
    thickness = 4

    # horizontal lines
    pg.draw.line(surface, line_color, (start_x , start_y + CELL_SIZE), (start_x + grid_width, start_y + CELL_SIZE), thickness)
    pg.draw.line(surface, line_color, (start_x , start_y + CELL_SIZE * 2), (start_x + grid_width, start_y + CELL_SIZE * 2), thickness)

    # vertical lines
    pg.draw.line(surface, line_color, (start_x  + CELL_SIZE, start_y), (start_x + CELL_SIZE, start_y + grid_width), thickness)
    pg.draw.line(surface, line_color, (start_x + CELL_SIZE * 2, start_y), (start_x + CELL_SIZE * 2, start_y + grid_width), thickness)

def draw_color(surface, color, col=1, row=1):
    """Fills a specific cell with a circle of a given color"""
    start_x = int(GRID_CENTER_X - CELL_SIZE + (col * CELL_SIZE))
    start_y = int(GRID_CENTER_Y - CELL_SIZE + (row * CELL_SIZE))

    radius = (CELL_SIZE // 2) - PADDING # PADDING is padding
    pg.draw.circle(surface, color, (start_x, start_y), radius)

def generate_stimulus(cfg):
    """Generates a stimulus list based on the config's active flags."""
    return {
        "color" : random.choice(ACTIVE_COLORS) if cfg["use_color"] else "BLUE",
        "spatial" : (random.choice(0, 2), random.choice(0, 2)) if cfg["use_spatial"] else (1, 1),
        # TODO AUDIO
    }

def get_target_matches(current, target, cfg):
    """Returns a dictionary mapping of which specific elements are currently matching."""
    return {
        "color": cfg["use_color"] and (current["color"] == target["color"]),
        "spatial": cfg["use_spatial"] and (current["spatial"] == target["spatial"])
        # TODO audio
    }

def handle_input(modality, action_timestamp):
    """Logs performance of input keys."""
    if not responses[modality]:
        responses[modality] = True
        if is_target[modality]:
            print(f"[{action_timestamp}] {modality.upper()} CORRECT HIT")
        else:
            print(f"[{action_timestamp}] {modality.upper()} IMPULSIVITY ERROR")

state = "BLANK"
last_switch_time = time.perf_counter()
show_color = False
stimulus_history = []
current_stimulus = None

is_target = {"color": False, "spatial": False } # TODO: Audio
responses = {"color": False, "spatial": False } # TODO: Audio

running = True
while running:
    for event in pg.event.get():
        # quit conditions
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            running = False

            if state == "STIMULUS":
                action_timestamp = time.time()
                if event.key == pg.K_f and config["use_color"]:
                    handle_input("color", action_timestamp)

    current_time = time.perf_counter()
    elapsed = current_time - last_switch_time

    if state == "BLANK" and elapsed >= ISI_DURATION:
        state = "STIMULUS"
        show_color = True
        last_switch_time = current_time

        onset_timestamp = time.time()
        #TODO: log onto a csv file
    
    elif state == "STIMULUS" and elapsed >= STIMULUS_DURATION:
        state = "BLANK"
        show_color = False
        last_switch_time = current_time
        
    screen.fill(COLORS["WHITE"])
    draw_grid(screen)

    if show_color:
        draw_color(screen, COLORS["RED"])
   
    pg.display.flip()
    clock.tick(60)

pg.quit()