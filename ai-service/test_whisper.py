from app.services.transcribe import transcribe_audio

audio_path = "uploads/b93228c6-fb8d-47ee-97ac-ef50e2eb013f.m4a"

text = transcribe_audio(audio_path)

print("===== TRANSCRIPT =====")
print(text)