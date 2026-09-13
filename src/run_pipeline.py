import subprocess
import sys
import threading
import time
import signal
import os
from pathlib import Path
import multiprocessing
import data_analysis.analyze_data as ad
import data_analysis.record_lsl as rl
import data_analysis.data_extraction as de
import data_analysis.sync_events as se
import games.nback as nb
import concurrent.futures

def run_pipeline():
    python_exe = sys.executable  
    
    # Define your folders
    base_dir = Path(__file__).resolve().parent
    data_extraction_dir = base_dir / "data_analysis"
    game_dir = base_dir / "games" 

    # 0. Clean up any old flags
    stop_flag = data_extraction_dir / "stop_recording.txt"
    if stop_flag.exists():
        stop_flag.unlink()

    print("1. Starting Mock LSL Stream...")
    mock_process = subprocess.Popen(
        [python_exe, "mock_lsl.py"], 
        cwd=data_extraction_dir,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    time.sleep(2)

    print("2. Starting EEG Recorder...")
    # Use the ThreadPoolExecutor just like in run_baseline
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Pass the stop_flag directly so there are no path mismatches
        future_record = executor.submit(rl.record_eeg_stream, "lsl_eeg_recording_raw.fif", stop_flag)
        time.sleep(2)

        try:
            print("\n--- 3. Launching Game (nback.py) ---")
            subprocess.run([python_exe, "nback.py"], cwd=game_dir)
            print("--- Game Finished ---\n")
        finally:
            # Guarantee the flag is created even if the game crashes
            print("4. Stopping Scripts (Creating stop flag)...")
            stop_flag.touch() 
            
        # Wait for recorder to see flag and close
        raw_eeg_output_path = future_record.result()
        print("   -> Recorder successfully closed!")

    print("5. Stopping Mock LSL Stream...")
    mock_process.terminate()
    mock_process.wait()

    print("\n6. Running Data Extraction...")
    subprocess.run([python_exe, "data_extraction.py"], cwd=data_extraction_dir)

    print("\n7. Synchronizing Events...")
    subprocess.run([python_exe, "sync_events.py"], cwd=data_extraction_dir)

    print("\n Pipeline complete!")

    if stop_flag.exists():
        stop_flag.unlink()


def run_pipeline_real():
    python_exe = sys.executable  
    
    # Define your folders so Python knows exactly where everything is
    base_dir = Path(__file__).resolve().parent
    data_extraction_dir = base_dir / "data_analysis"
    game_dir = base_dir / "games" 

    # 0. Clean up any old flags before starting
    stop_flag = data_extraction_dir / "stop_recording.txt"
    if stop_flag.exists():
        stop_flag.unlink()

    print("2. Starting Real EEG Recorder...")
    # Use the ThreadPoolExecutor just like the mock pipeline
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Pass the stop_flag directly to guarantee path matching
        future_record = executor.submit(rl.record_eeg_stream, "lsl_eeg_recording_raw.fif", stop_flag)
        time.sleep(2)

        try:
            print("\n--- 3. Launching Game (nback.py) ---")
            subprocess.run([python_exe, "nback.py"], cwd=game_dir)
            print("--- Game Finished ---\n")
        finally:
            # Guarantee the flag is created even if the game crashes or is closed
            print("4. Stopping Scripts (Creating stop flag)...")
            stop_flag.touch() 
            
        # Wait for recorder to see flag and safely save the data
        raw_eeg_output_path = future_record.result()
        print("   -> Recorder successfully closed!")

    print("\n6. Running Data Extraction...")
    subprocess.run([python_exe, "data_extraction.py"], cwd=data_extraction_dir)

    print("\n7. Synchronizing Events...")
    subprocess.run([python_exe, "sync_events.py"], cwd=data_extraction_dir)

    print("\n Pipeline complete!")

    if stop_flag.exists():
        stop_flag.unlink()


def run_baseline():
    python_exe = sys.executable  
        
    base_dir = Path(__file__).resolve().parent
    data_extraction_dir = base_dir / "data_analysis"
    game_dir = base_dir / "games" 

    # 0. Safety check: Ensure no leftover stop flag exists before we even begin
    stop_flag = data_extraction_dir / "stop_recording.txt"
    if stop_flag.exists():
        stop_flag.unlink()

    print("1. Starting Mock LSL Stream...")
    mock_process = subprocess.Popen(
        [python_exe, "mock_lsl.py"], 
        cwd=data_extraction_dir,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    time.sleep(2)
    
    print("2. Recording the idle baseline...")
    
    # --- IDLE RECORDING BLOCK ---
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start idle recording
        future_idle = executor.submit(rl.record_eeg_stream, "baseline_raw.fif")
        
        # Wait 10 seconds to actually gather idle baseline data
        time.sleep(10)
        
        print("Stopping Idle Recording (Creating stop flag)...")
        stop_flag.touch() 
        
        # Capture the actual return value once it safely closes
        raw_idle_eeg_path = future_idle.result()
        
    print("   -> Idle Recorder successfully closed!")

    # Clean up the flag BEFORE starting the next recording
    if stop_flag.exists():
        stop_flag.unlink()

    print("\n3. Running Baseline.1 Data Extraction...")
    # Use the dynamic variable returned from the thread
    processed_output_path_baseline = de.process_eeg_file(raw_idle_eeg_path, "datafiles/baseline.csv")
    print(f"saved baseline no activity to {processed_output_path_baseline}")


    print("\nStarting baseline activity...")
    baseline_game = nb.NBackGame(config = {
        "n_back" : 1,
        "use_color" : False,
        "use_spatial" : True,
        "use_audio" : False
    })
    
    # --- ACTIVE RECORDING BLOCK ---
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 1. Start active recording (make sure stop_flag is passed here!)
        future_active = executor.submit(rl.record_eeg_stream, "baseline_active_raw.fif", stop_flag)
        
        try:
            # 2. Run the game
            game_log_filepath = baseline_game.run()
            
        finally:
            # 3. This block runs NO MATTER WHAT. 
            # If the game crashes, this will still trigger, kill the recording thread, 
            # and allow Python to print the actual Pygame error to your terminal.
            print("Stopping Active Scripts (Creating stop flag)...")
            stop_flag.touch() 

        # Capture the actual return value once it safely closes
        raw_active_eeg_path = future_active.result()
    
    processed_output_path = de.process_eeg_file(raw_active_eeg_path, "datafiles/baseline_active_processed.csv")
    se.sync_game_to_eeg(raw_active_eeg_path, processed_output_path, game_log_filepath, "datafiles/synced_baseline.csv")

    # Final cleanup
    if stop_flag.exists():
        stop_flag.unlink()
# def run_baseline():
#     python_exe = sys.executable  
        
#     # Define your folders so Python knows exactly where everything is
#     base_dir = Path(__file__).resolve().parent
#     data_extraction_dir = base_dir / "data_analysis"
#     game_dir = base_dir / "games" # Example folder for your game

#     print("1. Starting Mock LSL Stream...")
#     # Add cwd=data_extraction_dir so Python runs it as if you were in that folder
#     mock_process = subprocess.Popen(
#         [python_exe, "mock_lsl.py"], 
#         cwd=data_extraction_dir,
#         creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
#     )
#     time.sleep(2)
#     print("2. Recording the idle baseline...")

#     recorder_thread = threading.Thread(
#         target=rl.record_eeg_stream,
#         args=("baseline_raw.fif",)
#     )
#     recorder_thread.start()
#     raw_eeg_output_path = "datafiles/LSLData/baseline_raw.fif"
#     time.sleep(10)
#     print("4. Stopping Scripts (Creating stop flag)...")
#     stop_flag = data_extraction_dir / "stop_recording.txt"
#     stop_flag.touch()  # Creates the empty text file

#     recorder_thread.join()
    
#     # rl.record_eeg_stream("baseline_raw.fif")
#     # time.sleep(10)

#     processed_output_path = de.process_eeg_file(raw_eeg_output_path, "baseline_processed.csv")
    

# # Wait for the recording script to see the file, break the loop, and save the .fif
#     print("   -> Recorder successfully closed!")

#     print("\n3. Running Baseline.1 Data Extraction...")
#     processed_output_path_baseline = de.process_eeg_file("datafiles/LSLData/baseline_raw.fif", "datafiles/baseline.csv")

#     print(f"saved baseline no activity to {processed_output_path_baseline}")

#     if Path(stop_flag).exists():
#         stop_flag.unlink()

#     print("Starting baseline activity...")
#     baseline_game = nb.NBackGame(config = {
#         "n_back" : 1,
#         "use_color" : False,
#         "use_spatial" : False,
#         "use_audio" : True
#     })
    
#     recorder_thread = threading.Thread(
#     target=rl.record_eeg_stream, 
#     args=("baseline_active_raw.fif",)
# )
#     recorder_thread.start()
#     raw_eeg_output_path = "datafiles/LSLData/baseline_active_raw.fif"
#     game_log_filepath = baseline_game.run(log_filename="baseline_game_session.csv")

#     print("4. Stopping Scripts (Creating stop flag)...")
#     stop_flag = data_extraction_dir / "stop_recording.txt"
#     stop_flag.touch()  # Creates the empty text file

#     recorder_thread.join()
# # Wait for the recording script to see the file, break the loop, and save the .fif
#     print("   -> Recorder successfully closed!")
#     processed_output_path = de.process_eeg_file(raw_eeg_output_path, "baseline_active_processed.csv")

#     se.sync_game_to_eeg(raw_eeg_output_path, processed_output_path, game_log_filepath, "synced_baseline.csv")

#     if Path(stop_flag).exists():
#         stop_flag.unlink()

    
def run_baseline_real():
    python_exe = sys.executable  
        
    base_dir = Path(__file__).resolve().parent
    data_extraction_dir = base_dir / "data_analysis"
    game_dir = base_dir / "games" 

    # 0. Safety check: Ensure no leftover stop flag exists before we even begin
    stop_flag = data_extraction_dir / "stop_recording.txt"
    if stop_flag.exists():
        stop_flag.unlink()

    print("1. Recording the real idle baseline...")
    
    # --- IDLE RECORDING BLOCK ---
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Pass stop_flag directly
        future_idle = executor.submit(rl.record_eeg_stream, "baseline_raw.fif", stop_flag)
        
        # Wait 10 seconds to gather idle baseline data
        time.sleep(10)
        
        print("Stopping Idle Recording (Creating stop flag)...")
        stop_flag.touch() 
        
        # Capture the actual return value once it safely closes
        raw_idle_eeg_path = future_idle.result()
        
    print("   -> Idle Recorder successfully closed!")

    # Clean up the flag BEFORE starting the next recording
    if stop_flag.exists():
        stop_flag.unlink()

    print("\n2. Running Baseline Data Extraction...")
    processed_output_path_baseline = de.process_eeg_file(raw_idle_eeg_path, "datafiles/baseline.csv")
    print(f"Saved baseline no activity to {processed_output_path_baseline}")


    print("\nStarting real baseline activity...")
    # Be sure to include log_filename here if you haven't permanently defaulted it in NBackGame
    baseline_game = nb.NBackGame(
        config={
            "n_back": 1,
            "use_color": False,
            "use_spatial": True,
            "use_audio": False
        },
        log_filename="baseline_game_session.csv" 
    )
    
    # --- ACTIVE RECORDING BLOCK ---
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start active recording
        future_active = executor.submit(rl.record_eeg_stream, "baseline_active_raw.fif", stop_flag)
        
        try:
            # Run the game
            game_log_filepath = baseline_game.run()
            
        finally:
            # Guarantee the flag triggers even if the game crashes or is closed
            print("Stopping Active Scripts (Creating stop flag)...")
            stop_flag.touch() 

        # Capture the actual return value once it safely closes
        raw_active_eeg_path = future_active.result()
    
    print("   -> Active Recorder successfully closed!")

    processed_output_path = de.process_eeg_file(raw_active_eeg_path, "datafiles/baseline_active_processed.csv")
    se.sync_game_to_eeg(raw_active_eeg_path, processed_output_path, game_log_filepath, "datafiles/synced_baseline.csv")

    # Final cleanup
    if stop_flag.exists():
        stop_flag.unlink()
    
    print("\n Real Baseline Pipeline Complete!")


if __name__ == "__main__":
    run_pipeline()

    # df = ad.fetch_synced_data("video_demo.csv")

    # tei_df = ad.calculate_task_engagement(df)
    # tbr_df = ad.calculate_tbr(df, channels=['Fz','C3', 'C4','Cz','Pz','PO7','PO8','Oz'])
    # tar_df = ad.calculate_tar(df, channels1=['Fz','C3', 'C4','Cz'], channels2=['PO7','PO8','Oz', 'Pz'])


    # ad.plot_all_ratios(tei_df, tbr_df, tar_df)

    # ad.plot_both_accuracies_matplotlib(ad.running_accuracy(df), ad.rolling_average_accuracy(df, window_size=5))