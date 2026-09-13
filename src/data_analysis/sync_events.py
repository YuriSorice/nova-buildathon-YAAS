import mne
import pandas as pd
import time
from pathlib import Path


def sync_game_to_eeg(raw_fif_path, eeg_csv_path, game_csv_path, output_path):
    print("Loading datasets...")

    eeg_df = pd.read_csv(eeg_csv_path)
    game_df = pd.read_csv(game_csv_path)
    output_first_half = output_path[:-4]
    file_format = ".csv"
    date = f"_{time.ctime()}"
    date = date.replace(" ", "_", -1)
    date = date.replace(":", "_", -1)

    output_path = output_first_half + date + file_format

    raw = mne.io.read_raw_fif(raw_fif_path, preload=False, verbose=False)
    eeg_start_unix = raw.info["meas_date"].timestamp()
    print(f"EEG start time: {eeg_start_unix}")

    epoch_duration = 2.0
    epoch_overlap = 1.0
    epoch_step = epoch_duration - epoch_overlap

    for col in ['Game_Modality', 'Game_Action', 'Game_Performance']:
        eeg_df[col] = "None"

    print("Aligning timestamps...")

    for _, row in game_df.iterrows():
        event_time = row['timestamp']
        modality = row['modality']
        action = row['action']
        performance = row['performance_state']

        relative_time = event_time - eeg_start_unix

        if relative_time < 0:
            continue

        for epoch_idx in eeg_df['Epoch']:
            epoch_start = epoch_idx * epoch_step
            epoch_end = epoch_start + epoch_duration

            if epoch_start <= relative_time <= epoch_end:

                curr_mod = eeg_df.at[epoch_idx, 'Game_Modality']
                eeg_df.at[epoch_idx, 'Game_Modality'] = (
                    str(
                        modality) if curr_mod == "None" else f"{curr_mod} | {modality}"
                )

                curr_action = eeg_df.at[epoch_idx, 'Game_Action']
                eeg_df.at[epoch_idx, 'Game_Action'] = (
                    str(
                        action) if curr_action == "None" else f"{curr_action} | {action}"
                )

                curr_perf = eeg_df.at[epoch_idx, 'Game_Performance']
                eeg_df.at[epoch_idx, 'Game_Performance'] = (
                    str(
                        performance) if curr_action == "None" else f"{curr_perf} | {performance}"
                )

    eeg_df.to_csv(output_path, index=False)
    print(f"Synchronized output saved to {output_path}")
    return output_path


if __name__ == "__main__":
    sync_game_to_eeg(
        raw_fif_path="../datafiles/LSLData/lsl_eeg_recording_raw.fif",
        eeg_csv_path="../datafiles/extracted_bandpowers.csv",
        game_csv_path="../games/game_session_log.csv",
        output_path="../datafiles/synced_data.csv"
    )
