import mne
import numpy as np
import pandas as pd
from scipy.signal import welch
from pathlib import Path

# getting the path, reading the data
script_dir = Path(__file__).resolve().parent
raw_path = script_dir.parent / "datafiles" / "Ewing_Patrick_2026-08-10_13-07-25_EO-EC.cnt"
raw = mne.io.read_raw_ant(raw_path, preload = True)

# filter out unnecessary freqs, (lower than 1 hz is things like sweat and movement)
raw.filter(l_freq = 1.0, h_freq = 40.0, verbose = True)

# split the data into epochs, windows of time to get data readings
epochs = mne.make_fixed_length_epochs(raw, duration=2.0, overlap=1.0, verbose = False)
data = epochs.get_data() * 1e6
sfreq = raw.info["sfreq"]
ch_names = raw.ch_names

# total power at given freqs for a given epoch
def bandpower(psd, freqs, band):
    band_idx = np.logical_and(freqs >= band[0], freqs <= band[1])
    return np.trapezoid(psd[:, band_idx], freqs[band_idx], axis=1)

# welch's method is a fast fourier transform, it turns the time reading into a frequency reading
records = []
for epoch_idx, epoch_data in enumerate(data):
    freqs, psd = welch(epoch_data, fs=sfreq, nperseg=min(int(sfreq * 2), epoch_data.shape[1]))
# getting bandpower for different frequencies

    theta = bandpower(psd, freqs, (4, 8)) # unfocused frequencies
    alpha = bandpower(psd, freqs, (8, 13)) # unfocused frequencies
    beta = bandpower(psd, freqs, (13, 30)) # focused frequencies

    mean_theta = np.mean(theta)
    mean_alpha = np.mean(alpha)
    mean_beta = np.mean(beta)

    engagement = mean_beta / (mean_alpha + mean_theta + 1e-6) # how hard you're focusing/thinking actively
    tbr = mean_theta / (mean_beta + 1e-6) # how distracted, how idle your brain is

    records.append({
        "epoch": epoch_idx,
        "time_sec": epoch_idx * 1.0,
        "theta": mean_theta,
        "alpha": mean_alpha,
        "beta": mean_beta,
        "engagement_index": engagement,
        "tbr": tbr
    })

features_df = pd.DataFrame(records)
print(features_df.head(10))