import mne
import numpy as np
import pandas as pd
import sys
import time
from datetime import datetime, timezone
import pylsl
from pylsl import StreamInlet, resolve_byprop, resolve_streams
from pathlib import Path

def record_eeg_stream(output_filename="lsl_eeg_recording_raw.fif"):
    """Uses a StreamInlet to place incoming data chunks from lsl into a file for offline processing."""
    print("Searching for LSL EEG Stream...")
    streams = resolve_byprop('type', 'EEG', timeout=5.0)


    if not streams:
        all_streams = resolve_streams()
        if all_streams:
            streams = [all_streams[0]]
            print(f"No eeg tagged stream found, falling back to: {streams[0].name()}")
        else:
            print("Error: no lsl streams found on network.")
            print("Ensure ANT Neuro or g.tec software is running and broadcasting.")
            sys.exit(1)

    stream_info = streams[0]
    print(f"Connected to stream: {stream_info.name()} with SourceID: {stream_info.source_id()}")

    inlet = StreamInlet(stream_info, max_buflen=360, max_chunklen=512)

    info = inlet.info()
    sfreq = float(info.nominal_srate())
    n_channels = int(info.channel_count())

    ch_names = []
    ch_types = []
    ch_node = info.desc().child("channels").child("channel")
    while not ch_node.empty():
        label = ch_node.child_value("label")
        c_type = ch_node.child_value("type").lower()

        ch_names.append(label if label else f"CH_{len(ch_names)}")

        if 'eeg' in c_type:
            ch_types.append('eeg')
        elif any(keyword in label.lower() for keyword in ['acc', 'gyro', 'batt', 'count', 'val', 'status']):
            ch_types.append('misc')
        else:
            ch_types.append('eeg_notypetag') if not c_type else ch_types.append('misc')

        ch_node = ch_node.next_sibling()

    if len(ch_names) != n_channels:
        print("[WARNING] Missing or incomplete channel metadata in LSL stream.")
        stream_name = info.name().lower()
        
        # Smart Fallback: Detect Unicorn by name or by its unique 17-channel signature
        if 'unicorn' in stream_name or n_channels == 17:
            print("[RECORDER] Applying Unicorn Hybrid Black fallback profile...")
            ch_names = ['Fz', 'C3', 'Cz', 'C4', 'Pz', 'PO7', 'Oz', 'PO8', 
                        'Accel_X', 'Accel_Y', 'Accel_Z', 
                        'Gyro_X', 'Gyro_Y', 'Gyro_Z', 
                        'Battery', 'Counter', 'Validation']
            # First 8 are EEG, remaining 9 are miscellaneous telemetry
            ch_types = ['eeg'] * 8 + ['misc'] * 9
        else:
            # Generic fallback for completely unknown devices without XML
            print(f"[RECORDER] Unknown device. Applying generic layout for {n_channels} channels...")
            ch_names = [f"CH_{i:02d}" for i in range(n_channels)]
            ch_types = ['eeg'] * n_channels
    print(f"Stream params: {n_channels} channels at {sfreq} Hz")
    print(f"Channels: {', '.join(ch_names[:8])}{'... ' if len(ch_names) > 8 else ''}")

    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir.parent / "datafiles" / "LSLData"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename

    all_samples = []
    all_timestamps = []

    print("\nRecording started, use CTRL + C to stop and save.")
    try:
        first = True
        while True:
            if Path("stop_recording.txt").exists():
                print("\n[RECORDER] Stop signal received! Exiting loop")
                break
            samples, timestamps = inlet.pull_chunk(timeout=1.0, max_samples=512)
            if timestamps:
                all_samples.extend(samples)
                all_timestamps.extend(timestamps)
                if first:
                    offset = time.time() - pylsl.local_clock()
                    eeg_start_unix = all_timestamps[0] + offset 
                    print(f"EEG Recording started at Unix Time: {eeg_start_unix}")
                    first = False

    except KeyboardInterrupt:
        print("\n[RECORDER] Stop signal received! Exiting loop...")

    if not all_samples:
        print("[RECORDER] No samples collected. Exiting without saving.")
        return

    print(f"[RECORDER] Preparing to save {len(all_timestamps)} samples to disk...")

    data_array = np.array(all_samples, dtype=np.float64).T
    if np.max(np.abs(data_array)) > 1.0:
        data_array *= 1e-6

    mne_info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
    raw = mne.io.RawArray(data_array, mne_info)

    if all_timestamps:
        start_time = time.time() - pylsl.local_clock() + all_timestamps[0]
        meas_date = datetime.fromtimestamp(start_time, tz=timezone.utc)
        raw.set_meas_date(meas_date)

    print(f"[RECORDER] Writing to {output_path}...")
    raw.save(output_path, overwrite=True)
    print("[RECORDER] File saved successfully!")

if __name__ == "__main__":
    record_eeg_stream()