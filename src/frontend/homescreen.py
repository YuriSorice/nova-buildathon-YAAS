import customtkinter as ctk
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageTk
import json
import matplotlib
matplotlib.use("TkAgg") # Forces Matplotlib to render inside Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
# from data_analysis.extract_features import analyze_data

focus_ratio = 1.0  # Global variable to hold the focus ratio for feedback

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MindGames")
        self.geometry("1000x650")

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
        self.scrollable_frame = ctk.CTkScrollableFrame(self.tab_results,fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # build the home screen UI
        self.welcome_label = ctk.CTkLabel(
            self.tab_home, text="Select a game to begin your session.", font=("Comic Sans MS", 24))
        self.welcome_label.pack(pady=40)

        # create three distinct buttons.
        self.btn_game1 = ctk.CTkButton(self.tab_home, text="Launch Game 1", width=200,
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

    # independent Observer Methods
    def start_game_1(self):
        self.btn_game1.configure(state="disabled", text="Game Running...")

        project_root = Path(__file__).resolve().parents[2]
        game_path = project_root / "src" / "games" / "nback.py"
        self.game_process = subprocess.Popen(
            [sys.executable, str(game_path)], cwd=str(project_root))

        self.check_game_status()

    def check_game_status(self):
        # .poll() returns None if the process is still running
        if self.game_process.poll() is None:
            # Check again in 500 milliseconds
            self.after(500, self.check_game_status)
        else:
            # The game closed! Reset the button and process data
            self.btn_game1.configure(state="normal", text="Launch Game 1")
            self.process_and_display_data()

    def build_results(self, game_score=None, eeg_data=None, focus_ratio=None):
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
            "Comic Sans MS", 20, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(game_stats_side, text=f"Accuracy: {game_score}%", font=(
            "Comic Sans MS", 16)).pack(pady=2)
        ctk.CTkLabel(game_stats_side, text="Reaction Time: 1.2s", font=(
            # Placeholder for reaction time
            "Comic Sans MS", 16)).pack(pady=(2, 15))

        # build EEG analysis side
        eeg_analysis_side = ctk.CTkFrame(
            display_container, corner_radius=15, fg_color="#2b2b2b")
        eeg_analysis_side.grid(row=0, column=1, padx=10,
                               pady=10, sticky="nsew")

        # build EEG analysis side
        ctk.CTkLabel(eeg_analysis_side, text="Your Focus", font=(
            "Comic Sans MS", 20, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(eeg_analysis_side, text=f"Task Engagement Index: ", font=(
            # Placeholder for concentration level
            "Comic Sans MS", 16)).pack(pady=2)
        ctk.CTkLabel(eeg_analysis_side, text=f"Theta/Beta Ratio: ", font=(
            # Placeholder for concentration level
            "Comic Sans MS", 16)).pack(pady=2)
        ctk.CTkLabel(eeg_analysis_side, text=f"Theta/Alpha Ratio: ", font=(
            # Placeholder for concentration level
            "Comic Sans MS", 16)).pack(pady=(2, 15))

        # build user feedback section
        user_feedback = ctk.CTkFrame(
            self.scrollable_frame, corner_radius=15, fg_color="#1e3a3e")
        user_feedback.pack(fill="x", padx=20, pady=20)

        theta_beta_ratio = focus_ratio if focus_ratio is not None else 0.0
        if theta_beta_ratio > 0.5:
            feedback_text = "You... completed it... I guess. Next time, remember to use the keys. Your EEG data shows elevated Alpha waves, which may indicate a relaxed or distracted state. Consider focusing more during the game."
        else:
            feedback_text = "Gotta admit, you did much better than the last guy. Your EEG data indicates a high level of Beta waves, suggesting active engagement and focus during the game. Keep up the good work!"

        ctk.CTkLabel(user_feedback, text="What it all means:", font=(
            "Comic Sans MS", 20, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(user_feedback, text=feedback_text, font=(
            "Comic Sans MS", 16), wraplength=800).pack(pady=15, padx=15)

        # build graph display section
        graph_frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=15, fg_color="#2b2b2b")
        graph_frame.pack(fill="both", padx=20, pady=10, expand=True)

        # create a Matplotlib figure and axis for the graph
        fig = Figure(figsize=(8, 3), dpi=100, facecolor="#2b2b2b")
        ax = fig.add_subplot(111)

        # customize the graph's appearance to match the dark theme
        ax.set_facecolor("#2b2b2b")
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color("#50B5CA")

        # Placeholder data for the graph
        time_minutes = [1, 2, 3, 4, 5]
        theta_beta_ratio = [2.1, 3.4, 5.6, 7.0, 11.4]

        # plot the data with a line and markers, and fill the area under the curve for visual emphasis
        ax.plot(time_minutes, theta_beta_ratio, color="#50B5CA", linewidth=2, marker='o')
        ax.fill_between(time_minutes, theta_beta_ratio, color="#50B5CA", alpha=0.3)
        ax.set_title("Theta/Beta Ratio Over Time", color="white", fontsize=16, fontname="Comic Sans MS")
        ax.set_xlabel("Time (seconds)", color="white", fontsize=12, fontname="Comic Sans MS")
        ax.set_ylabel("Theta/Beta Ratio", color="white", fontsize=12, fontname="Comic Sans MS")

        # convert the Matplotlib figure to a Tkinter-compatible canvas and display it
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()

        # render the canvas to ensure it displays correctly
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)



    # def process_and_display_data(self):
    #     # switch the UI to the Results tab
    #     self.tabs.set("Results")
    #     self.results_title.configure(text="Processing EEG Data...")
    #     self.update() # force the UI to update immediately so the user sees the "Processing" text
    #
    #     try:
    #         with open("eeg_results.json", "r") as file:
    #             game_data = json.load(file)
    #             score = game_data.get("game_score", "N/A")
    #
    #         focus_level = analyze_session("eeg_results.json")
    #
    #         self.build_results(game_score=score, eeg_data=game_data)
    #
    #         # Load the image
    #         # raw.compute_psd().plot().savefig("eeg_results.png")  # Example of saving a plot from MNE
    #         # my_image = ctk.CTkImage(light_image=Image.open("eeg_results.png"), size=(600, 300))
    #
    #         # self.graph_label.configure(image=my_image, text="") # Remove the text, show the image
    #         self.results_title.configure(text="Concentration Analysis Complete")
    #
    #     except FileNotFoundError:
    #         self.results_title.configure(text="EEG data file not found.")
    #
    #     except Exception as e:
    #         self.results_title.configure(text="Error loading graph image.")

    def process_and_display_data(self):
        # 1. Switch to Data tab and show the loading state
        self.tabs.set("Results")
        self.results_title.configure(text="Processing EEG Data...")
        self.update()

        # 2. Simulate the time it takes for MNE to run the ICA math (2000 ms = 2 seconds)
        # This calls a temporary helper method instead of crashing on the missing files
        self.after(2000, self._render_mock_dashboard)

    def _render_mock_dashboard(self):
        # 3. Bypass the JSON and data_extraction files entirely for now.
        # Pass fake testing numbers directly into your dashboard builder.

        fake_score = 88
        fake_ratio = 1.7

        self.build_results(game_score=fake_score, focus_ratio=fake_ratio)
        print("Mock dashboard rendered successfully!")


if __name__ == "__main__":
    app = FocusApp()
    app.mainloop()
