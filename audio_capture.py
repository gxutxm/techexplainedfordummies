import sounddevice as sd
import soundfile as sf
import whisper
import tempfile
import os

def record_audio(duration=10, fs=16000):
    print(f"\n[Microphone] Recording for {duration} seconds... Speak now!")
    # Capture audio using sounddevice
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait() # Wait for the recording to finish
    print("[Microphone] Recording finished.")
    return recording, fs

def transcribe_audio(audio_data, fs, model_size="base"):
    print(f"\n[Whisper] Loading model '{model_size}' and transcribing...")
    # Load the Whisper model (this may take a moment the first time to download)
    model = whisper.load_model(model_size)
    
    # Save to a temporary WAV file because Whisper expects a file path
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav_path = temp_wav.name
    
    try:
        sf.write(temp_wav_path, audio_data, fs)
        # Transcribe the audio
        result = model.transcribe(temp_wav_path)
        return result["text"].strip()
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
