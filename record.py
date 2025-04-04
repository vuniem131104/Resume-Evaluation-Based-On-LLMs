import sounddevice as sd
import numpy as np
import whisper
import wave

SAMPLERATE = 16000  
SILENCE_THRESHOLD = 500  
SILENCE_DURATION = 2  

def is_silent(audio_chunk, silence_threshold=SILENCE_THRESHOLD):
    return np.max(np.abs(audio_chunk)) < silence_threshold

def start_record(chunk_duration=0.5, samplerate=SAMPLERATE, silence_duration=SILENCE_DURATION, model="base"):

    recorded_audio = []
    silent_time = 0

    while True:
        chunk = sd.rec(int(chunk_duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
        sd.wait()
        recorded_audio.append(chunk)
        
        if is_silent(chunk):
            silent_time += chunk_duration
        else:
            silent_time = 0  
        
        if silent_time >= silence_duration:
            break

    filename = "temp_audio.wav"
    recorded_audio = np.concatenate(recorded_audio, axis=0)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  
        wf.setframerate(samplerate)
        wf.writeframes(recorded_audio.tobytes())

    model = whisper.load_model(model)

    result = model.transcribe(filename)
    return result["text"]

