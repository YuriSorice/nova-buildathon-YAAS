import customtkinter as ctk

ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue")

class FocusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EEG Concentration Hub")
        self.geometry("900x600")

        # create the tabbed navigation
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(padx=20, pady=20, fill="both", expand=True)

        # create two tabs: Home and data
        self.tab_home = self.tabs.add("Home")
        self.tab_results = self.tabs.add("Data")

        # build the home screen UI
        self.welcome_label = ctk.CTkLabel(self.tab_home, text="Select a game to begin your session.", font=("Comic Sans MS", 24))
        self.welcome_label.pack(pady=40)

        # create three distinct buttons. 
        self.btn_game1 = ctk.CTkButton(self.tab_home, text="Launch Game 1", width=200, height=80, command=self.start_game_1, font=("Comic Sans MS", 20, "bold"))
        self.btn_game1.pack(pady=20)

        self.btn_game2 = ctk.CTkButton(self.tab_home, text="Launch Game 2", width=200, height=80, command=self.start_game_2, font=("Comic Sans MS", 20, "bold"))
        self.btn_game2.pack(pady=20)

        self.btn_game3 = ctk.CTkButton(self.tab_home, text="Launch Game 3", width=200, height=80, command=self.start_game_3, font=("Comic Sans MS", 20, "bold"))
        self.btn_game3.pack(pady=20)

    # independent Observer Methods
    def start_game_1(self):
        print("Starting Game 1...")
        # TODO: Start LSL EEG stream
        # TODO: Launch the Pygame window for Game 1
        
    def start_game_2(self):
        print("Starting Game 2...")

        # TODO: Launch the Pygame window for Game 2
        
    def start_game_3(self):
        print("Starting Game 3...")

        # TODO: Launch the Pygame window for Game 3

if __name__ == "__main__":
    app = FocusApp()
    app.mainloop()