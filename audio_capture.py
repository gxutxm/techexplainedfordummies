import sounddevice as sd
import soundfile as sf
import whisper
import tempfile
import os

import queue
import threading
import sys
import numpy as np

def record_audio(duration=60, fs=16000):
    print(f"\n[Microphone] Press Enter to START recording...")
    input()
    print(f"[Microphone] Recording started (max {duration}s)... Press Enter to STOP.")
    
    q = queue.Queue()
    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(indata.copy())

    stop_event = threading.Event()
    
    def wait_for_input():
        input()
        stop_event.set()
        
    t = threading.Thread(target=wait_for_input)
    t.daemon = True
    t.start()
    
    try:
        with sd.InputStream(samplerate=fs, channels=1, dtype='float32', callback=callback):
            stop_event.wait(timeout=duration)
            
        audio_data = []
        while not q.empty():
            audio_data.append(q.get())
            
        if audio_data:
            recording = np.concatenate(audio_data, axis=0)
        else:
            recording = np.zeros((0, 1), dtype='float32')
            
        print("[Microphone] Recording stopped.")
        return recording, fs
    except Exception as e:
        print(f"[Microphone Error]: {e}")
        return np.zeros((0, 1), dtype='float32'), fs

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
