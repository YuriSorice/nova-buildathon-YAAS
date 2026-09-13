from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageTk
import json
import matplotlib
import os
matplotlib.use("TkAgg")  # forces Matplotlib to render inside Tkinter

BASE_DIR = Path(__file__).resolve().parent.parent
FILE_PATH = BASE_DIR / "games" / "game_state.json"

project_root = Path(__file__).resolve().parents[2]
src_folder = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_folder) not in sys.path:
    sys.path.insert(0, str(src_folder))

import data_analysis.analyze_data as da  # Import your data analysis module



ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MindGames")
        self.geometry("1100x750")

        # create the tabbed navigation
        self.tabs = ctk.CTkTabview(self, segmented_button_selected_color="#50B5CA",
                                   segmented_button_selected_hover_color="#3D98A8", text_color="#17212B",)

        self.tabs._segmented_button.configure(
            font=("Comic Sans MS", 16, "bold"))
        self.tabs.pack(padx=20, pady=20, fill="both", expand=True)

        # create two tabs: Home and data
        self.tab_home = self.tabs.add("Home")
        self.tab_results = self.tabs.add("Results")

        # add scrollable frame to the Results tab
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.tab_results, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # add explanation for the game on the home tab
        self.explanation_frame = ctk.CTkFrame(
            self.tab_home, corner_radius=15, fg_color="#1e3a3e")
        self.explanation_frame.pack(fill="x", padx=60, pady=(0, 30))

        self.explanation_title = ctk.CTkLabel(self.explanation_frame, text="How to Play", font=(
            "Comic Sans MS", 20, "bold"), text_color="#50B5CA")
        self.explanation_title.pack(pady=(15, 5))

        game_explanation = (
            "This game is an exercise that challenges your working memory and your sustained focus.\n\n"
            "• The Objective: Watch the sequence of circles appearing on screen.\n"
            "• Press the corresponding key if the current state of the circle matches its state shown N turns ago.\n"
            "• For example, the color of the circle, its location, or the audio played.\n"
            "• Keep your jaw relaxed and your head still.\n"
            "• The game will adjust difficulty depending on your performance."
        )

        self.explanation_body = ctk.CTkLabel(self.explanation_frame, text=game_explanation, font=(
            "Comic Sans MS", 18), justify="left", anchor="w")
        self.explanation_body.pack(pady=(5, 15), padx=30, fill="x")

        # build the home screen welcome UI
        self.welcome_label = ctk.CTkLabel(
            self.tab_home, text="Select 'Calibration' to begin your session.", font=("Comic Sans MS", 24))
        self.welcome_label.pack(pady=(20, 20))

        # create calibration button
        self.calibration_btn = ctk.CTkButton(self.tab_home, text="Calibration (60s)", width=200, height=80, font=(
            "Comic Sans MS", 20, "bold"), fg_color="#F39C12", hover_color="#D68910", command=self.start_calibration)
        self.calibration_btn.pack(pady=(10, 20))

        # create game launch button.
        self.btn_game1 = ctk.CTkButton(self.tab_home, text="Launch N-Back Game", width=200,
                                       height=80, command=self.start_game_1, font=("Comic Sans MS", 20, "bold"), fg_color="#50B5CA")
        self.btn_game1.pack(pady=20)

        # build data placeholder
        self.results_title = ctk.CTkLabel(
            self.scrollable_frame, text="Awaiting Game Session...", font=("Comic Sans MS", 24))
        self.results_title.pack(pady=20)

        # will hold graph image
        self.graph_label = ctk.CTkLabel(self.scrollable_frame, text="")
        self.graph_label.pack(pady=10)

        self.game_process = None  # Variable to track the running game

    def start_calibration(self):
        self.is_calibration_run = True
        self.calibration_btn.configure(state="disabled", text="Calibrating...")
        self.btn_game1.configure(state="disabled")

        with open(FILE_PATH, "w") as f:
            json.dump({}, f, indent=4)

        project_root = Path(__file__).resolve().parents[2]
        src_folder = project_root / "src"

        python_command = "from run_pipeline import run_baseline_real; run_baseline_real()"

        # passes a "calibration" argument to game script so it knows to run the 60s version
        self.game_process = subprocess.Popen(
            [sys.executable, "-c", python_command], cwd=str(src_folder))


        self.check_game_status()

    # independent Observer Methods
    def start_game_1(self):
        self.is_calibration_run = False
        self.calibration_btn.configure(state="disabled")
        self.btn_game1.configure(state="disabled", text="Game Running...")

        project_root = Path(__file__).resolve().parents[2]
        src_folder = project_root / "src"
        python_command = "from run_pipeline import run_pipeline_real; run_pipeline_real()"

        # runs normal game
        self.game_process = subprocess.Popen(
            [sys.executable, "-c", python_command], cwd=str(src_folder))

        self.check_game_status()

    def check_game_status(self):
        # .poll() returns None if the process is still running
        if self.game_process.poll() is None:
            # Check again in 500 milliseconds
            self.after(500, self.check_game_status)
        else:
            # The game closed! Reset the button and process data
            self.calibration_btn.configure(
                state="normal", text="Calibration (60s)")
            self.btn_game1.configure(state="normal", text="Launch N-Back Game")
            if self.is_calibration_run:
                self.show_calibration_complete()
            else:
                datafiles_dir = src_folder / "datafiles"
                sync_events_files = sorted(
                    datafiles_dir.glob("synced_data_*.csv"),
                    key=lambda path: path.stat().st_mtime,
                )
                sync_events_path = sync_events_files[-1] if sync_events_files else None
                self.process_and_display_data(sync_events_path)

    def show_calibration_complete(self):
        # switch to results
        self.tabs.set("Results")

        # clear placeholders
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.results_title = ctk.CTkLabel(
            self.scrollable_frame, text="Calibration Complete.\nBaseline recorded.\nYou may begin the real test.", font=("Comic Sans MS", 24))
        self.results_title.pack(pady=(100, 30))

        # Button to return to home
        return_btn = ctk.CTkButton(self.scrollable_frame, text="Return to Home Tab", font=(
            "Comic Sans MS", 20, "bold"), width=250, height=60, fg_color="#50B5CA", command=lambda: self.tabs.set("Home"))
        return_btn.pack(pady=20)

    def build_results(self, game_score=None, running_accuracy=None, rolling_average_accuracy=None, tei=None, tbr=None, tar=None, playerstate=None):
        # clear previous results
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.results_title = ctk.CTkLabel(
            self.scrollable_frame, text="Game Session Complete!", font=("Comic Sans MS", 24))
        self.results_title.pack(pady=20)

        display_container = ctk.CTkFrame(
            self.scrollable_frame, fg_color="transparent")
        display_container.pack(fill="x", padx=20, pady=10)
        display_container.grid_columnconfigure((0, 1), weight=1)

        # build game stats side
        game_stats_side = ctk.CTkFrame(
            display_container, corner_radius=15, fg_color="#2b2b2b")
        game_stats_side.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(game_stats_side, text="Game Performance", font=(
            "Comic Sans MS", 20, "bold")).pack(pady=(15, 1))
        ctk.CTkLabel(game_stats_side, text="", font=(
            "Comic Sans MS", 16)).pack(pady=(2, 10))
        ctk.CTkLabel(game_stats_side, text=f"Accuracy: {game_score}%", font=(
            "Comic Sans MS", 16)).pack(pady=2)

        # build EEG analysis side
        eeg_analysis_side = ctk.CTkFrame(
            display_container, corner_radius=15, fg_color="#2b2b2b")
        eeg_analysis_side.grid(row=0, column=1, padx=10,
                               pady=10, sticky="nsew")

        # build EEG analysis side
        ctk.CTkLabel(eeg_analysis_side, text="Your Focus", font=(
            "Comic Sans MS", 20, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(eeg_analysis_side, text=f"Task Engagement Index: {round(tei["tei"].mean(), 3)}", font=(
            # Placeholder for concentration level
            "Comic Sans MS", 16)).pack(pady=2)
        ctk.CTkLabel(eeg_analysis_side, text=f"Theta/Beta Ratio: {round(tbr["tbr"].mean(), 3)}", font=(
            # Placeholder for concentration level
            "Comic Sans MS", 16)).pack(pady=2)
        ctk.CTkLabel(eeg_analysis_side, text=f"Theta/Alpha Ratio: {round(tar["tar"].mean(), 3)}", font=(
            # Placeholder for concentration level
            "Comic Sans MS", 16)).pack(pady=(2, 15))

        # build user feedback section
        user_feedback1 = ctk.CTkFrame(
            self.scrollable_frame, corner_radius=15, fg_color="#1e3a3e")
        user_feedback1.pack(fill="x", padx=20, pady=20)

        feedback_text = (
            "You are probably wondering what these waves and ratios entail. \n"
            "The Theta Waves are representative of daydreaming, fatigue, or drowsiness. \n"
            "The Beta Waves are representative of active concentration. \n"
            "The Alpha Waves are representative of a relaxed or disengaged state. \n"
            "By combining these different wavelengths together, we are able to construct educated stats. \n"
            "--------------------------------------------------------------------- \n"
            "A high Theta/Beta ratio indicates that the brain is struggling with active concentration or is fatigued. \n"
            "A high Theta/Alpha ratio indicates that the brain is working hard. \n"
            "Now that you have an understanding of the markers, we can look at how this affects YOU."
        )

        ctk.CTkLabel(user_feedback1, text="What this data means:", font=(
            "Comic Sans MS", 20, "bold")).pack(pady=(15, 5))
        feedback_box = ctk.CTkTextbox(user_feedback1, font=(
            "Comic Sans MS", 16), width=800, height=320, fg_color="transparent", wrap="word")
        feedback_box.pack(pady=15, padx=15)
        feedback_box.insert("0.0", feedback_text)
        feedback_box.tag_config("center", justify="center")
        feedback_box.tag_add("center", "1.0", "end")
        feedback_box._textbox.configure(spacing1=8, spacing2=8, spacing3=8)
        feedback_box.configure(state="disabled")


        # build user feedback section
        user_feedback2 = ctk.CTkFrame(
            self.scrollable_frame, corner_radius=15, fg_color="#1e3a3e")
        user_feedback2.pack(fill="x", padx=20, pady=20)

        if playerstate == "optimal":
            feedback_text2 = "You're in the sweet spot. Right now the game difficulty is just right. Next time you play, the speed will increase."
        elif playerstate == "bored":
            feedback_text2 = "You're really cruising. Time to increase the difficulty."
        elif playerstate == "overload":
            feedback_text2 = "This difficulty may be asking a lot right now. Next run we will ease off."
        elif playerstate == "abandoned":
            feedback_text2 = "This doesn't seem to be grabbing your attention right now. Lets dial it back."
        else:
            feedback_text2 = "Run one more time to get more data."
            
        ctk.CTkLabel(user_feedback2, text="What this data means for YOU:", font=(
            "Comic Sans MS", 20, "bold")).pack(pady=(15, 5))
        feedback_box2 = ctk.CTkTextbox(user_feedback2, font=(
            "Comic Sans MS", 16), width=800, height=90, fg_color="transparent", wrap="word")
        feedback_box2.pack(pady=15, padx=15)
        feedback_box2.insert("0.0", feedback_text2)
        feedback_box2.tag_config("center", justify="center")
        feedback_box2.tag_add("center", "1.0", "end")
        feedback_box2._textbox.configure(spacing1=8, spacing2=8, spacing3=8)
        feedback_box2.configure(state="disabled")

        # build graph display section
        graph_frame1 = ctk.CTkFrame(
            self.scrollable_frame, corner_radius=15, fg_color="#2b2b2b")
        graph_frame1.pack(fill="both", padx=20, pady=(5, 2))

        # create a Matplotlib figure and axis for the graph
        fig1 = da.plot_both_accuracies(
            running_accuracy, rolling_average_accuracy)
        fig1.tight_layout()

        # convert the Matplotlib figure to a Tkinter-compatible canvas and display it
        canvas1 = FigureCanvasTkAgg(fig1, master=graph_frame1)
        canvas_widget1 = canvas1.get_tk_widget()
        canvas_widget1.configure(
            background="#2b2b2b", highlightthickness=0, borderwidth=0)
        canvas1.draw()

        # render the canvas to ensure it displays correctly
        canvas_widget1.pack(fill="both", expand=True, padx=5, pady=5)

        graph_frame2 = ctk.CTkFrame(
            self.scrollable_frame, corner_radius=15, fg_color="#2b2b2b")
        graph_frame2.pack(fill="both", padx=20, pady=(2, 5))

        # create a Matplotlib figure and axis for the graph
        fig2 = da.plot_eeg_data(tei, tbr, tar)
        fig2.tight_layout()

        # convert the Matplotlib figure to a Tkinter-compatible canvas and display it
        canvas2 = FigureCanvasTkAgg(fig2, master=graph_frame2)
        canvas_widget2 = canvas2.get_tk_widget()
        canvas_widget2.configure(
            background="#2b2b2b", highlightthickness=0, borderwidth=0)
        canvas2.draw()

        # render the canvas to ensure it displays correctly
        canvas_widget2.pack(fill="both", expand=True, padx=5, pady=5)

    def process_and_display_data(self, sync_events_path=None):
        # switch the UI to the Results tab
        self.tabs.set("Results")
        self.results_title.configure(text="Processing EEG Data...")
        self.update()  # force the UI to update immediately so the user sees the "Processing" text

        try:
            # Fetch the game session data
            df_data = da.fetch_synced_data(sync_events_path)
            baseline_df = da.fetch_synced_data("synced_baseline*.csv")
            print(baseline_df)
            baseline_tar_df = da.calculate_tar(baseline_df,
                                                ['Fz'], ['Pz', 'PO7', 'Oz', 'PO8'])
            baseline_beta_df = da.get_beta(baseline_df, ['Fz', 'C3', 'Cz', 'C4', 'Pz', 'PO7', 'Oz', 'PO8'])
            dprime = da.calculate_dprime(baseline_df)
            tei_df = da.calculate_task_engagement(
                df_data, ['Fz','Cz'])
            tbr_df = da.calculate_tbr(
                df_data, ['Fz', 'C3', 'Cz', 'C4', 'Pz', 'PO7', 'Oz', 'PO8'])
            tar_df = da.calculate_tar(df_data, ['Fz'], ['Pz', 'PO7', 'Oz', 'PO8'])
            beta_df = da.get_beta(df_data, ['Fz', 'C3', 'Cz', 'C4', 'Pz', 'PO7', 'Oz', 'PO8'])
            accuracy = int(da.calculate_accuracy(df_data) * 100)
            running_accuracy_df = da.running_accuracy(df_data)
            rolling_average_accuracy_df = da.rolling_average_accuracy(
            df_data, window_size=3)

            BASE_DIR = Path(__file__).resolve().parent.parent
            FILE_PATH = BASE_DIR / "games" / "game_state.json"

            with open(FILE_PATH, "r") as f:
                game_state = json.load(f)

            data = {
                "accuracy": accuracy,
                "tei": tei_df.to_dict(),
                "tbr": tbr_df.to_dict(),
                "tar": tar_df.to_dict(),
                "beta": beta_df.to_dict(),
                "baseline_beta": baseline_beta_df.to_dict(),
                "baseline_tar": baseline_tar_df.to_dict(),
                "dprime": dprime if dprime==dprime else 1.5,
                "player_mode": 1
            }

            game_state.update(data)

            with open(FILE_PATH, "w") as f:
                json.dump(game_state, f, indent=4)

            player_state = da.update_game_state(FILE_PATH)

            self.build_results(
                game_score=accuracy,
                running_accuracy=running_accuracy_df,
                rolling_average_accuracy=rolling_average_accuracy_df, tei=tei_df, tbr=tbr_df, tar=tar_df, playerstate=player_state
            )

            self.results_title.configure(
                text="Concentration Analysis Complete")

        except FileNotFoundError:
            self.results_title.configure(text="EEG data file not found.")

        except Exception as e:
            self.results_title.configure(text="Error loading graph image.")
            print(f"Error loading results: {e}")


if __name__ == "__main__":
    app = FocusApp()
    app.mainloop()
