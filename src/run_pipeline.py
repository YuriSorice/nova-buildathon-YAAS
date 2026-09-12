import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def run_pipeline(filename):
    python_exe = sys.executable  
    
    # Define your folders so Python knows exactly where everything is
    base_dir = Path(__file__).resolve().parent
    data_extraction_dir = base_dir / "data_analysis"
    game_dir = base_dir / "games" # Example folder for your game

    print("1. Starting Mock LSL Stream...")
    # Add cwd=data_extraction_dir so Python runs it as if you were in that folder
    mock_process = subprocess.Popen(
        [python_exe, "mock_lsl.py"], 
        cwd=data_extraction_dir,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    time.sleep(2)

    print("2. Starting EEG Recorder...")
    record_process = subprocess.Popen(
        [python_exe, "record_lsl.py"],
        cwd=data_extraction_dir,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    time.sleep(2)

    print("\n--- 3. Launching Game (nback.py) ---")
    subprocess.run([python_exe, "nback.py"], cwd=game_dir)
    print("--- Game Finished ---\n")

    print("4. Stopping Scripts (Creating stop flag)...")
    stop_flag = data_extraction_dir / "stop_recording.txt"
    stop_flag.touch()  # Creates the empty text file

# Wait for the recording script to see the file, break the loop, and save the .fif
    record_process.wait() 
    print("   -> Recorder successfully closed!")


    print("5. Stopping Mock LSL Stream...")
    mock_process.terminate()
    mock_process.wait()

    print("\n6. Running Data Extraction...")
    subprocess.run([python_exe, "data_extraction.py"], cwd=data_extraction_dir)

    print("\n7. Synchronizing Events...")
    subprocess.run([python_exe, "sync_events.py"], cwd=data_extraction_dir)

    print("\n Pipeline complete!")

    if Path(stop_flag).exists():
        stop_flag.unlink()

def run_pipeline_real(filename):
    python_exe = sys.executable  
    
    # Define your folders so Python knows exactly where everything is
    base_dir = Path(__file__).resolve().parent
    data_extraction_dir = base_dir / "data_analysis"
    game_dir = base_dir / "games" # Example folder for your game

    print("2. Starting EEG Recorder...")
    record_process = subprocess.Popen(
        [python_exe, "record_lsl.py"],
        cwd=data_extraction_dir,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    time.sleep(2)

    print("\n--- 3. Launching Game (nback.py) ---")
    subprocess.run([python_exe, "nback.py"], cwd=game_dir)
    print("--- Game Finished ---\n")

    print("4. Stopping Scripts (Creating stop flag)...")
    stop_flag = data_extraction_dir / "stop_recording.txt"
    stop_flag.touch()  # Creates the empty text file

# Wait for the recording script to see the file, break the loop, and save the .fif
    record_process.wait() 
    print("   -> Recorder successfully closed!")

    print("\n6. Running Data Extraction...")
    subprocess.run([python_exe, "data_extraction.py"], cwd=data_extraction_dir)

    print("\n7. Synchronizing Events...")
    subprocess.run([python_exe, "sync_events.py"], cwd=data_extraction_dir)

    print("\n Pipeline complete!")

    if Path(stop_flag).exists():
        stop_flag.unlink()


if __name__ == "__main__":
    run_pipeline_real()