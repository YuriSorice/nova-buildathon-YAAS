import mne
import numpy as np
import pandas as pd
from scipy.signal import welch
from pathlib import Path

script_dir = Path(__file__).resolve().parent
raw_path = script_dir.parent / "datafiles" / "Ewing_Patrick_2026-08-10_13-07-25_EO-EC.cnt"
raw = mne.io.read_raw_ant(raw_path, preload = True)

raw.filter(l_freq = 1.0, h_freq = 40.0, verbose = True)

epochs = mne.make_fixed_length_epochs(raw, duration=2.0, overlap=1.0, verbose = False)
data = epochs.get_data() * 1e6
sfreq = raw.info["sfreq"]
ch_names = raw.ch_names

def bandpower(psd, freqs, band):
    band_idx = np.logical_and(freqs >= band[0], freqs <= band[1])
    return np.trapezoid(psd[:, band_idx], freqs[band_idx], axis=1)

records = []
for epoch_idx, epoch_data in enumerate(data):
    freqs, psd = welch(epoch_data, fs=sfreq, nperseg=min(int(sfreq * 2), epoch_data.shape[1]))

    theta = bandpower(psd, freqs, (4, 8))
    alpha = bandpower(psd, freqs, (8, 13))
    beta = bandpower(psd, freqs, (13, 30))

    mean_theta = np.mean(theta)
    mean_alpha = np.mean(alpha)
    mean_beta = np.mean(beta)

    engagement = mean_beta / (mean_alpha + mean_theta + 1e-6)
    tbr = mean_theta / (mean_beta + 1e-6)

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