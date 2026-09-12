import mne
import numpy as np
import pandas as pd
from scipy.signal import welch
import time
import csv
import pylsl
from pathlib import Path

script_dir = Path(__file__).resolve().parent
raw_path = script_dir.parent / "datafiles" / "LSLData" / "lsl_eeg_recording.fif"
# raw_path = script_dir.parent / "datafiles" / "Ewing_Patrick_2026-08-10_13-07-25_EO-EC.cnt"
raw = mne.io.read_raw_fif(raw_path, preload = True)

epochs = mne.make_fixed_length_epochs(raw, duration=2.0, overlap=1.0, verbose = False)
data = epochs.get_data() * 1e6
sfreq = raw.info["sfreq"]
start_time = raw.info["meas_date"].timestamp()
ch_names = raw.ch_names


def preprocess_eeg(raw, l_freq=1.0, h_freq=40.0, n_components=15, eog_ch='Fp1'):
    """
    Applies a bandpass filter followed by ICA to clean raw EEG data.
    """
    # 1. Bandpass Filter (1-40 Hz) to remove drift and high-frequency noise (like power lines)
    raw_filtered = raw.copy().filter(l_freq=l_freq, h_freq=h_freq, verbose=True)

    n_comps = min(n_components, len(raw.ch_names))
    # Initialize and Fit ICA
    ica = mne.preprocessing.ICA(
        n_components=n_comps,
        method='fastica',
        random_state=42
    )
    ica.fit(raw_filtered)
    
    # The if statement is for working with mock data, could be removed for final product
    if eog_ch in raw.ch_names:
        eog_indices, eog_scores = ica.find_bads_eog(raw_filtered, ch_name=eog_ch)
        ica.exclude = eog_indices
    else:
        print(f"Skipping EOG rejection: channel {eog_ch} not found.")
    
    # 4. Reconstruct Clean Signal
    raw_cleaned = raw_filtered.copy()
    ica.apply(raw_cleaned)
    
    return raw_cleaned, ica


def bandpower(psd, freqs, band):
    """Gets the bandpower of a specific epoch."""
    band_idx = np.logical_and(freqs >= band[0], freqs <= band[1])
    return np.trapezoid(psd[band_idx], freqs[band_idx])

def extract_bandpowers(epochs_data, sfreq, ch_names, bands):
    """Calculates the PSD and extracts the bandpower for all epochs."""
    features = []

    for epoch_idx, epoch, in enumerate(epochs_data):
        epoch_features = {'Epoch': epoch_idx}

        for ch_idx, channel_data in enumerate(epoch):
            freqs, psd = welch(channel_data, sfreq, nperseg=int(sfreq))

            for band_name, band_limits, in bands.items():
                power = bandpower(psd, freqs, band_limits)
                col_name = f"{ch_names[ch_idx]}_{band_name}"
                epoch_features[col_name] = power

        features.append(epoch_features)

    return pd.DataFrame(features)

def process_eeg_file(input_path, output_path):
    """Loads, preprocessed, creates epochs, extracts bandpowers"""
    print(f"Loading file: {input_path.name}")

    # raw = mne.io.read_raw_ant(input_path, preload=True, verbose=False) # cnt files
    raw = mne.io.read_raw_fif(input_path, preload=True, verbose=False) # fif files

    print("Filtering and applying ICA...")
    raw_clean, ica_object = preprocess_eeg(raw, eog_ch='Fp1')

    print("Epoching data...")

    epochs = mne.make_fixed_length_epochs(raw_clean, duration=2.0, overlap=1.0, verbose = False)
    data = epochs.get_data() * 1e6
    sfreq = raw.info["sfreq"]
    ch_names = raw.ch_names

    bands = {
        'Theta' : (4, 8),
        'Alpha' : (8, 12),
        'Beta' : (12, 30)
    }

    print("Calculating bandpowers...")

    df_features = extract_bandpowers(data, sfreq, ch_names, bands)
    df_features.to_csv(output_path, index=False)

    print(f"Extraction complete, Saved {len(df_features)} epochs to {output_path.name}")

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    raw_path = script_dir.parent / "datafiles" / "LSLData" / "lsl_eeg_recording.fif" # 
    # raw_path = script_dir.parent / "datafiles" / "Ewing_Patrick_2026-08-10_13-07-25_EO-EC.cnt"
    output_csv = script_dir.parent / "datafiles" / "extracted_bandpowers.csv"
    
    # Ensure input file exists before running
    if raw_path.exists():
        process_eeg_file(raw_path, output_csv)
    else:
        print(f"Error: Could not find {raw_path}")








