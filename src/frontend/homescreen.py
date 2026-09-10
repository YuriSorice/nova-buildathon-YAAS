import customtkinter as ctk
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageTk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MindGames")
        self.geometry("900x600")

        # create the tabbed navigation
        self.tabs = ctk.CTkTabview(self, segmented_button_selected_color="#50B5CA", segmented_button_selected_hover_color="#3D98A8", text_color="#17212B",)

        self.tabs._segmented_button.configure(font=("Comic Sans MS", 16, "bold"))        
        self.tabs.pack(padx=20, pady=20, fill="both", expand=True)

        # create two tabs: Home and data
        self.tab_home = self.tabs.add("Home")
        self.tab_results = self.tabs.add("Results")

        # build the home screen UI
        self.welcome_label = ctk.CTkLabel(
            self.tab_home, text="Select a game to begin your session.", font=("Comic Sans MS", 24))
        self.welcome_label.pack(pady=40)

        # create three distinct buttons.
        self.btn_game1 = ctk.CTkButton(self.tab_home, text="Launch Game 1", width=200,
                                       height=80, command=self.start_game_1, font=("Comic Sans MS", 20, "bold"), fg_color="#50B5CA")
        self.btn_game1.pack(pady=20)

        #build data placeholder
        self.results_title = ctk.CTkLabel(self.tab_results, text="Awaiting Game Session...", font=("Comic Sans MS", 24))
        self.results_title.pack(pady=20)

        # will hold graph image
        self.graph_label = ctk.CTkLabel(self.tab_results, text="") 
        self.graph_label.pack(pady=10)

        self.game_process = None # Variable to track the running game

        '''
        self.btn_game2 = ctk.CTkButton(self.tab_home, text="Launch Game 2", width=200,
                                       height=80, command=self.start_game_2, font=("Comic Sans MS", 20, "bold"), fg_color="#50B5CA")
        self.btn_game2.pack(pady=20)
        '''

    # independent Observer Methods
    def start_game_1(self):
        self.btn_game1.configure(state="disabled", text="Game Running...")

        project_root = Path(__file__).resolve().parents[2]
        game_path = project_root / "src" / "games" / "nback.py"
        self.game_process = subprocess.Popen([sys.executable, str(game_path)],cwd=str(project_root))

        self.check_game_status()
    

    def start_game_2(self):
        print("Starting Game 2...")

        # TODO: Launch the Pygame window for Game 2

    def check_game_status(self):
        # .poll() returns None if the process is still running
        if self.game_process.poll() is None:
            # Check again in 500 milliseconds
            self.after(500, self.check_game_status)
        else:
            # The game closed! Reset the button and process data
            self.btn_game1.configure(state="normal", text="Launch Game 1")
            self.process_and_display_data()

    def process_and_display_data(self):
        # switch the UI to the Results tab
        self.tabs.set("Results")
        self.results_title.configure(text="Processing EEG Data...")
        
        # force the UI to update immediately so the user sees the "Processing" text
        self.update() 
        
        # --- YOUR MNE ICA CODE GOES HERE ---
        # e.g., clean_raw, fitted_ica = clean_eeg_with_ica(raw_data)
        # raw_data.plot().savefig('eeg_results.png')
        
        # 2. Load and display the saved image
        try:
            # Load the image using PIL (Replace 'placeholder.png' with your actual MNE output image)
            # my_image = ctk.CTkImage(light_image=Image.open("eeg_results.png"), size=(600, 300))
            
            # self.graph_label.configure(image=my_image, text="") # Remove the text, show the image
            self.results_title.configure(text="Concentration Analysis Complete")
            print("Data displayed successfully.")
            
        except Exception as e:
            self.results_title.configure(text="Error loading graph image.")
            print(f"Error: {e}")


if __name__ == "__main__":
    app = FocusApp()
    app.mainloop()
