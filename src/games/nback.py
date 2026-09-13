import time
import pygame as pg
import random
import csv
import glob
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import src.data_analysis.analyze_data as ad
import json

class NBackGame:

    def __init__(self, config, stim=1.75, game_length=15, num_match=3, log_filename="game_session_log.csv"):
        self.SCREEN_WIDTH = 800
        self.SCREEN_HEIGHT = 600
        self.FPS = 60
        self.CELL_SIZE = 100
        self.PADDING = 15
    
        self.GRID_CENTER_X = self.SCREEN_WIDTH // 2
        self.GRID_CENTER_Y = self.SCREEN_HEIGHT // 2
    
        self.STIMULUS_DURATION = stim
        self.ISI_DURATION = 1.0
        self.GAME_LENGTH = game_length
        self.MATCH_COUNT = num_match
        self.cfg = config
        self.COLORS = {
            "RED": (220, 50, 50),
            "BLUE": (50, 100, 220),
            "GREEN": (50, 200, 50),
            "YELLOW": (230, 210, 50),
            "BLACK": (0, 0, 0),
            "DARK_GREY": (75, 75, 75),
            "LIGHT_GREY": (180, 180, 180),
            "WHITE": (255, 255, 255)
        }

        self.ACTIVE_COLORS = ["RED", "BLUE", "GREEN", "YELLOW"]

        pg.init()
        pg.mixer.init()
        pg.font.init()
        self.screen = pg.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pg.display.set_caption("2-Back Game")
        self.clock = pg.time.Clock()

        # Load audio files
        script_dir = Path(__file__).resolve().parent
        audio_dir = script_dir.parent / "datafiles" / "audiofiles"

        # Load font
        self.font = pg.font.SysFont(None, 24)

        TARGET_WORDS = ["DOG", "CAT", "COW", "DUCK", "SUN", "TOY", "BIN"]
        self.AUDIO_FILES = {}

        for word in TARGET_WORDS:
            file_path = audio_dir / f"{word}.wav"
            if file_path.exists():
                self.AUDIO_FILES[word] = pg.mixer.Sound(str(file_path))
            else:
                print(f"Warning: {word}.wav not found at {file_path}.")
        self.ACTIVE_AUDIO = list(self.AUDIO_FILES.keys())

        self.is_target = {"color": False, "spatial": False, "audio": False } 
        self.responses = {"color": False, "spatial": False, "audio": False }
        self.feedback_states = {"color": "NEUTRAL", "spatial": "NEUTRAL", "audio": "NEUTRAL"}
        self.turn_counter = 0

        self.session_sequence = self.generate_sequence(self.GAME_LENGTH, self.MATCH_COUNT)
        self.log_filename = log_filename
        with open(self.log_filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "modality", "action", "performance_state"])

        
    def save_state(self):
        df = ad.fetch_synced_data("synced_data_alan_focused.csv")

        #baseline csv is synced_baseline plus a bunch of dates so if any file name starts with synced_baseline_ use that file
        baseline_df = ad.fetch_synced_data("synced_baseline*.csv")

        accuracy = int(ad.calculate_accuracy(df))
        tei_df = ad.calculate_task_engagement(df)
        tei_dict = tei_df.to_dict()
        tbr_df = ad.calculate_tbr(df, channels=['Fz','C3', 'C4','Cz','Pz','PO7','PO8','Oz'])
        tbr_dict = tbr_df.to_dict()
        tar_df = ad.calculate_tar(df, channels1=['Fz','C3', 'C4','Cz'], channels2=['PO7','PO8','Oz', 'Pz'])
        tar_dict = tar_df.to_dict()
        baseline_tar_df = ad.calculate_tar(baseline_df, channels=['Fz','C3', 'C4','Cz','Pz','PO7','PO8','Oz'])
        baseline_tar_dict = baseline_tar_df.to_dict()
        baseline_beta_df = baseline_df[['Fz_Beta', 'C3_Beta', 'C4_Beta', 'Cz_Beta', 'Pz_Beta', 'PO7_Beta', 'PO8_Beta', 'Oz_Beta']].mean()
        baseline_beta_dict = baseline_beta_df.to_dict()
        dprime = ad.calculate_dprime(df)

        state = {
            "config" : self.cfg,
            "accuracy" : accuracy,
            "tei" : tei_dict,
            "tbr" : tbr_dict,
            "tar" : tar_dict,
            "baseline_beta": baseline_beta_dict,
            "baseline_tar": baseline_tar_dict,
            "dprime": dprime
        }
        with open("game_state.json", "w") as file:
            json.dump(state, file, indent=4)

    def draw_grid(self):
        """Draws the 2-back grid centered on the given coordinates."""
        grid_width = self.CELL_SIZE * 3
        start_x = self.GRID_CENTER_X - (grid_width // 2)
        start_y = self.GRID_CENTER_Y - (grid_width // 2)

        line_color = self.COLORS["DARK_GREY"]
        thickness = 4

        # horizontal lines
        pg.draw.line(self.screen, line_color, (start_x , start_y + self.CELL_SIZE), (start_x + grid_width, start_y + self.CELL_SIZE), thickness)
        pg.draw.line(self.screen, line_color, (start_x , start_y + self.CELL_SIZE * 2), (start_x + grid_width, start_y + self.CELL_SIZE * 2), thickness)

        # vertical lines
        pg.draw.line(self.screen, line_color, (start_x  + self.CELL_SIZE, start_y), (start_x + self.CELL_SIZE, start_y + grid_width), thickness)
        pg.draw.line(self.screen, line_color, (start_x + self.CELL_SIZE * 2, start_y), (start_x + self.CELL_SIZE * 2, start_y + grid_width), thickness)

    def draw_color(self, color, coords):
        """Fills a specific cell with a circle of a given color"""
        start_x = int(self.GRID_CENTER_X - self.CELL_SIZE + (coords[0] * self.CELL_SIZE))
        start_y = int(self.GRID_CENTER_Y - self.CELL_SIZE + (coords[1] * self.CELL_SIZE))

        radius = (self.CELL_SIZE // 2) - self.PADDING # PADDING is padding
        pg.draw.circle(self.screen, color, (start_x, start_y), radius)

    def draw_legend(self):
        """Draws the keybinds for the active configuration settings."""
        active_settings = []
        if self.cfg["use_color"]: active_settings.append(("COLOR [F]", "color"))
        if self.cfg["use_spatial"]: active_settings.append(("SPATIAL [J]", "spatial"))
        if self.cfg["use_audio"]: active_settings.append(("AUDIO [SPACE]", "audio"))

        if not active_settings:
            return

        box_width, box_height = 140, 40

        spacing = 20
        total_width = len(active_settings) * box_width + (1 - len(active_settings)) * spacing
        start_x = (self.SCREEN_WIDTH - total_width) // 2
        start_y = self.SCREEN_HEIGHT - 70

        for i, (label, mod_key) in enumerate(active_settings):
            bx = start_x + i * (box_width + spacing)
            by = start_y

            state_color = self.COLORS["LIGHT_GREY"]
            if self.feedback_states[mod_key] == "CORRECT":
                state_color = self.COLORS["GREEN"]
            elif self.feedback_states[mod_key] == "ERROR":
                state_color = self.COLORS["RED"]

            pg.draw.rect(self.screen, state_color, (bx, by, box_width, box_height), border_radius=6)
            pg.draw.rect(self.screen, self.COLORS["DARK_GREY"], (bx, by, box_width, box_height), 2, border_radius=6)

            txt_surface = self.font.render(label, True, self.COLORS["BLACK"])
            txt_rect = txt_surface.get_rect(center=(bx+box_width // 2, by + box_height // 2))
            self.screen.blit(txt_surface, txt_rect)

    def generate_sequence(self, length, match_count):
        """Generates the array with a guaranteed target distribution.
        Prevents outlier games with for example, no matches or 70% matches."""
        n_back = self.cfg["n_back"]
        sequence = []
        color_targets = set(random.sample(range(n_back, length), match_count)) if self.cfg["use_color"] else set()
        spatial_targets = set(random.sample(range(n_back, length), match_count)) if self.cfg["use_spatial"] else set()
        audio_targets = set(random.sample(range(n_back, length), match_count)) if self.cfg["use_audio"] else set()

        
        for i in range(length):
            turn_stimulus = {}
            # color stim loop
            if self.cfg["use_color"]:
                if i in color_targets:
                    turn_stimulus["color"] = sequence[i - n_back]["color"]
                else:
                    color_pool = self.ACTIVE_COLORS.copy()
                    if i >= n_back:
                        avoid_color = sequence[i - n_back]["color"]
                        if avoid_color in color_pool:
                            color_pool.remove(avoid_color)
                    turn_stimulus["color"] = random.choice(color_pool)
            else:
                turn_stimulus["color"] = "BLUE"

            # spatial stim loop
            if self.cfg["use_spatial"]:
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
            if self.cfg["use_audio"]:
                if i in audio_targets:
                    turn_stimulus["audio"] = sequence[i - n_back]["audio"]
                else:
                    audio_pool = self.ACTIVE_AUDIO.copy()
                    if i >= n_back:
                        avoid_audio = sequence[i - n_back]["audio"]
                        if avoid_audio in audio_pool:
                            audio_pool.remove(avoid_audio)
                    turn_stimulus["audio"] = random.choice(audio_pool)
            else:
                turn_stimulus["audio"] = None

            sequence.append(turn_stimulus)

        return sequence

    def log_event(self, modality, action, state):
        """Writes the game event data to csv."""
        with open(self.log_filename, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([time.time(), modality, action, state])




    def get_target_matches(self, current, target):
        """Returns a dictionary mapping of which specific elements are currently matching."""
        return {
            "color": self.cfg["use_color"] and (current["color"] == target["color"]),
            "spatial": self.cfg["use_spatial"] and (current["spatial"] == target["spatial"]),
            "audio": self.cfg["use_audio"] and (current["audio"] == target["audio"])
        }

    def handle_input(self, modality, action_timestamp):
        """Logs performance of input keys."""
        if not self.responses[modality]:
            self.responses[modality] = True
            if self.is_target[modality]:
                self.feedback_states[modality] = "CORRECT"
                self.log_event(modality, "pressed", "CORRECT_HIT")
                print(f"[{action_timestamp}] {modality.upper()} CORRECT HIT")
            else:
                self.feedback_states[modality] = "ERROR"
                self.log_event(modality, "pressed", "IMPULSIVITY_ERROR")
                print(f"[{action_timestamp}] {modality.upper()} IMPULSIVITY ERROR")

    def run(self):
        last_switch_time = time.perf_counter()

        current_stimulus = self.session_sequence[self.turn_counter]
        if self.cfg["use_audio"] and current_stimulus.get("audio"):
            self.AUDIO_FILES[current_stimulus["audio"]].play()

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
                    if event.key == pg.K_f and self.cfg["use_color"]:
                        self.handle_input("color", action_timestamp)
                    if event.key == pg.K_j and self.cfg["use_spatial"]:
                        self.handle_input("spatial", action_timestamp)
                    if event.key == pg.K_SPACE and self.cfg["use_audio"]:
                        self.handle_input("audio", action_timestamp)

            current_time = time.perf_counter()
            elapsed = current_time - last_switch_time

            current_time = time.perf_counter()
            elapsed = current_time - last_switch_time

            if elapsed >= self.STIMULUS_DURATION:
                # Check for inattention errors on the current item before moving on
                for mod in ["color", "spatial", "audio"]:
                    config_key = f"use_{mod}"
                    if self.cfg[config_key] and self.is_target[mod] and not self.responses[mod]:
                        self.feedback_states[mod] = "ERROR"
                        self.log_event(mod, "missed", "INATTENTION_ERROR")
                        print(f"[{time.time()}] {mod.upper()} INATTENTION ERROR - Missed target")

                # Advance to the next turn
                self.turn_counter += 1
                if self.turn_counter >= self.GAME_LENGTH:
                    running = False
                else:
                    current_stimulus = self.session_sequence[self.turn_counter]
                    
                    # Reset responses and feedback for the new turn
                    self.responses = {"color": False, "spatial": False, "audio": False}
                    self.feedback_states = {"color": "NEUTRAL", "spatial": "NEUTRAL", "audio": "NEUTRAL"}

                    # Calculate new n-back targets
                    if self.turn_counter >= self.cfg["n_back"]:
                        target_stimulus = self.session_sequence[self.turn_counter - self.cfg["n_back"]]
                        self.is_target = self.get_target_matches(current_stimulus, target_stimulus)
                    else:
                        is_target = {"color": False, "spatial": False, "audio": False}

                    # Play audio if active
                    if self.cfg["use_audio"] and current_stimulus.get("audio"):
                        self.AUDIO_FILES[current_stimulus["audio"]].play()

                last_switch_time = current_time
                
            self.screen.fill(self.COLORS["WHITE"])
            self.draw_grid()

            if current_stimulus:
                color_val = self.COLORS[current_stimulus["color"]] if self.cfg["use_color"] else self.COLORS["BLUE"]
                self.draw_color(color_val, current_stimulus["spatial"])

            self.draw_legend()
        
            pg.display.flip()
            self.clock.tick(self.FPS)

        last_switch_time = time.perf_counter()
        self.save_state()

        pg.quit()
        return self.log_filename


if __name__ == "__main__":
    config = {
        "n_back": 2,
        "use_color": True,
        "use_spatial": True,
        "use_audio": False
    }
    game = NBackGame(config)
    game.run()