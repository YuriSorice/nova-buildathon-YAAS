import time
import pygame as pg
import random
from pathlib import Path

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
CELL_SIZE = 100
PADDING = 15
GRID_CENTER_X = SCREEN_WIDTH // 2
GRID_CENTER_Y = SCREEN_HEIGHT // 2
STIMULUS_DURATION = 1.75
ISI_DURATION = 1.0
GAME_LENGTH = 12
MATCH_COUNT = 3


# TODO bug in the generating sequence loop
# TODO log all the info
config = {
    "n_back" : 2,
    "use_color" : True,
    "use_spatial" : False,
    "use_audio" : True
}


COLORS = {
    "RED": (220, 50, 50),
    "BLUE": (50, 100, 220),
    "GREEN": (50, 200, 50),
    "YELLOW": (230, 210, 50),
    "BLACK": (0, 0, 0),
    "DARK_GREY": (75, 75, 75),
    "LIGHT_GREY": (180, 180, 180),
    "WHITE": (255, 255, 255)
}

ACTIVE_COLORS = ["RED", "BLUE", "GREEN", "YELLOW"]

pg.init()
pg.mixer.init()
pg.font.init()
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pg.display.set_caption("2-Back Game")
clock = pg.time.Clock()

# Load audio files
script_dir = Path(__file__).resolve().parent
audio_dir = script_dir.parent.parent / "datafiles" / "audiofiles"

# Load font
font = pg.font.SysFont(None, 24)

TARGET_WORDS = ["DOG", "CAT", "COW", "DUCK", "SUN", "TOY", "BIN"]
AUDIO_FILES = {}

for word in TARGET_WORDS:
    file_path = audio_dir / f"{word}.wav"
    if file_path.exists():
        AUDIO_FILES[word] = pg.mixer.Sound(str(file_path))
    else:
        print(f"Warning: {word}.wav not found at {file_path}.")
ACTIVE_AUDIO = list(AUDIO_FILES.keys())

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

def draw_color(surface, color, coords):
    """Fills a specific cell with a circle of a given color"""
    start_x = int(GRID_CENTER_X - CELL_SIZE + (coords[0] * CELL_SIZE))
    start_y = int(GRID_CENTER_Y - CELL_SIZE + (coords[1] * CELL_SIZE))

    radius = (CELL_SIZE // 2) - PADDING # PADDING is padding
    pg.draw.circle(surface, color, (start_x, start_y), radius)

def draw_legend(surface, cfg, feedback):
    """Draws the keybinds for the active configuration settings."""
    active_settings = []
    if cfg["use_color"]: active_settings.append(("COLOR [F]", "color"))
    if cfg["use_spatial"]: active_settings.append(("SPATIAL [J]", "spatial"))
    if cfg["use_audio"]: active_settings.append(("AUDIO [SPACE]", "audio"))

    if not active_settings:
        return

    box_width, box_height = 140, 40

    spacing = 20
    total_width = len(active_settings) * box_width + (1 - len(active_settings)) * spacing
    start_x = (SCREEN_WIDTH - total_width) // 2
    start_y = SCREEN_HEIGHT - 70

    for i, (label, mod_key) in enumerate(active_settings):
        bx = start_x + i * (box_width + spacing)
        by = start_y

        state_color = COLORS["LIGHT_GREY"]
        if feedback[mod_key] == "CORRECT":
            state_color = COLORS["GREEN"]
        elif feedback[mod_key] == "ERROR":
            state_color = COLORS["RED"]

        pg.draw.rect(surface, state_color, (bx, by, box_width, box_height), border_radius=6)
        pg.draw.rect(surface, COLORS["DARK_GREY"], (bx, by, box_width, box_height), 2, border_radius=6)

        txt_surface = font.render(label, True, COLORS["BLACK"])
        txt_rect = txt_surface.get_rect(center=(bx+box_width // 2, by + box_height // 2))
        surface.blit(txt_surface, txt_rect)

def generate_sequence(config, length, match_count):
    """Generates the array with a guaranteed target distribution.
    Prevents outlier games with for example, no matches or 70% matches."""
    n_back = config["n_back"]
    sequence = []
    color_targets = set(random.sample(range(n_back, length), match_count)) if config["use_color"] else set()
    spatial_targets = set(random.sample(range(n_back, length), match_count)) if config["use_spatial"] else set()
    audio_targets = set(random.sample(range(n_back, length), match_count)) if config["use_audio"] else set()

    
    for i in range(length):
        turn_stimulus = {}
        # color stim loop
        if config["use_color"]:
            if i in color_targets:
                turn_stimulus["color"] = sequence[i - n_back]["color"]
            else:
                color_pool = ACTIVE_COLORS.copy()
                if i >= n_back:
                    avoid_color = sequence[i - n_back]["color"]
                    if avoid_color in color_pool:
                        color_pool.remove(avoid_color)
                turn_stimulus["color"] = random.choice(color_pool)
        else:
            turn_stimulus["color"] = "BLUE"

        # spatial stim loop
        if config["use_spatial"]:
            if i in spatial_targets:
                turn_stimulus["spatial"] = sequence[i - n_back]["spatial"]
            else:
                spatial_pool = [(x,y) for x in range(3) for y in range(3)]
                if i >= n_back:
                    avoid_space = sequence[i - n_back]["spatial"]
                    if avoid_space in spatial_pool:
                        spatial_pool.remove(avoid_space)
                turn_stimulus["spatial"] = random.choice(spatial_pool)
        else:
            turn_stimulus["spatial"] = (1, 1)

        # audio stim loop
        if config["use_audio"]:
            if i in audio_targets:
                turn_stimulus["audio"] = sequence[i - n_back]["audio"]
            else:
                audio_pool = ACTIVE_AUDIO.copy()
                if i >= n_back:
                    avoid_audio = sequence[i - n_back]["audio"]
                    if avoid_audio in audio_pool:
                        audio_pool.remove(avoid_audio)
                turn_stimulus["audio"] = random.choice(audio_pool)
        else:
            turn_stimulus["audio"] = None

        sequence.append(turn_stimulus)

    return sequence



# def generate_stimulus(cfg):
#     """Generates a stimulus list based on the config's active flags."""
#     return {
#         "color" : random.choice(ACTIVE_COLORS) if cfg["use_color"] else "BLUE",
#         "spatial" : (random.randint(0, 2), random.randint(0, 2)) if cfg["use_spatial"] else (1, 1),
#         "audio" : random.choice(ACTIVE_AUDIO) if cfg["use_audio"] else None
#     }

def get_target_matches(current, target, cfg):
    """Returns a dictionary mapping of which specific elements are currently matching."""
    return {
        "color": cfg["use_color"] and (current["color"] == target["color"]),
        "spatial": cfg["use_spatial"] and (current["spatial"] == target["spatial"]),
        "audio": cfg["use_audio"] and (current["audio"] == target["audio"])
    }

def handle_input(modality, action_timestamp):
    """Logs performance of input keys."""
    if not responses[modality]:
        responses[modality] = True
        if is_target[modality]:
            feedback_states[modality] = "CORRECT"
            print(f"[{action_timestamp}] {modality.upper()} CORRECT HIT")
        else:
            feedback_states[modality] = "ERROR"
            print(f"[{action_timestamp}] {modality.upper()} IMPULSIVITY ERROR")

state = "BLANK"
last_switch_time = time.perf_counter()
show_color = False
stimulus_history = []


is_target = {"color": False, "spatial": False, "audio": False } 
responses = {"color": False, "spatial": False, "audio": False }
feedback_states = {"color": "NEUTRAL", "spatial": "NEUTRAL", "audio": "NEUTRAL"}

session_sequence = generate_sequence(config, GAME_LENGTH, MATCH_COUNT)

turn_counter = 0
current_stimulus = session_sequence[turn_counter]
if config["use_audio"] and current_stimulus.get("audio"):
    AUDIO_FILES[current_stimulus["audio"]].play()

running = True
while running:
    for event in pg.event.get():
        # quit conditions
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                running = False
                continue


            action_timestamp = time.time()
            if event.key == pg.K_f and config["use_color"]:
                handle_input("color", action_timestamp)
            if event.key == pg.K_j and config["use_spatial"]:
                handle_input("spatial", action_timestamp)
            if event.key == pg.K_SPACE and config["use_audio"]:
                handle_input("audio", action_timestamp)

    current_time = time.perf_counter()
    elapsed = current_time - last_switch_time

    current_time = time.perf_counter()
    elapsed = current_time - last_switch_time

    if elapsed >= STIMULUS_DURATION:
        # Check for inattention errors on the current item before moving on
        for mod in ["color", "spatial", "audio"]:
            config_key = f"use_{mod}"
            if config[config_key] and is_target[mod] and not responses[mod]:
                feedback_states[mod] = "ERROR"
                print(f"[{time.time()}] {mod.upper()} INATTENTION ERROR - Missed target")

        # Advance to the next turn
        turn_counter += 1
        if turn_counter >= GAME_LENGTH:
            running = False
        else:
            current_stimulus = session_sequence[turn_counter]
            
            # Reset responses and feedback for the new turn
            responses = {"color": False, "spatial": False, "audio": False}
            feedback_states = {"color": "NEUTRAL", "spatial": "NEUTRAL", "audio": "NEUTRAL"}

            # Calculate new n-back targets
            if turn_counter >= config["n_back"]:
                target_stimulus = session_sequence[turn_counter - config["n_back"]]
                is_target = get_target_matches(current_stimulus, target_stimulus, config)
            else:
                is_target = {"color": False, "spatial": False, "audio": False}

            # Play audio if active
            if config["use_audio"] and current_stimulus.get("audio"):
                AUDIO_FILES[current_stimulus["audio"]].play()

        last_switch_time = current_time
        
    screen.fill(COLORS["WHITE"])
    draw_grid(screen)

    if current_stimulus:
        color_val = COLORS[current_stimulus["color"]] if config["use_color"] else COLORS["BLUE"]
        draw_color(screen, color_val, current_stimulus["spatial"])

    draw_legend(screen, config, feedback_states)
   
    pg.display.flip()
    clock.tick(FPS)

pg.quit()