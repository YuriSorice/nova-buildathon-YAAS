import time
import numpy as np
from pylsl import StreamInfo, StreamOutlet

def run_mock_eeg():
    # 1. Setup stream parameters matching standard EEG
    n_channels = 8
    srate = 250
    info = StreamInfo(name='MockEEG', type='EEG', channel_count=n_channels, 
                      nominal_srate=srate, channel_format='float32', source_id='mock_12345')

    # 2. Add channel labels to the XML metadata so your receiver finds them
    channels = info.desc().append_child("channels")
    for i in range(n_channels):
        ch = channels.append_child("channel")
        ch.append_child_value("label", f"Mock_{i+1}")

    # 3. Create the outlet to begin broadcasting
    outlet = StreamOutlet(info)
    print(f"Broadcasting MockEEG stream at {srate}Hz...")
    
    try:
        while True:
            # Generate 10 random samples (simulating microvolts)
            chunk = np.random.randn(10, n_channels) * 15.0 
            outlet.push_chunk(chunk.tolist())
            # Sleep exactly the duration of 10 samples
            time.sleep(10.0 / srate)
    except KeyboardInterrupt:
        print("\nStopping mock stream.")

if __name__ == '__main__':
    run_mock_eeg()