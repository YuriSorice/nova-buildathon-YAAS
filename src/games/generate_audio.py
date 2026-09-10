import pyttsx3
from pathlib import Path

def generate_stimuli_audio():
    # Initialize the native offline text-to-speech engine
    engine = pyttsx3.init()
    
    # Slow down the speech rate slightly for clear, distinct syllables
    engine.setProperty('rate', 140) 
    
    # Distinct, non-rhyming words to prevent sensory processing confounds
    targets = ["dog", "cat", "cow", "duck", "sun", "toy", "bin"]

    script_dir = Path(__file__).resolve().parent
    output_dir = Path(script_dir / "../datafiles/audiofiles").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating .wav files in: {output_dir}")
    for word in targets:
        # Uppercase filenames to match your Pygame dictionary keys
        filename = f"{word.upper()}.wav"

        save_path = output_dir / filename
        # Saves directly to your local directory without freezing a live game loop
        engine.save_to_file(word, str(save_path))
        # engine.runAndWait() # put it here for linux
        print(f"Saved: {filename}")
        
    # Process the rendering queue
    engine.runAndWait()    
    print("Audio generation complete.")

if __name__ == "__main__":
    generate_stimuli_audio()