from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")

def transcribe_audio(file_path: str) -> str:
    segments, info = model.transcribe(
        file_path,
        language=None,
        condition_on_previous_text=False,
        vad_filter=True,          # filters out silence
    )
    detected = info.language
    print(f"WHISPER DETECTED LANGUAGE: {detected}")

    # if whisper detected something other than en/fr, force english
    if detected not in ("en", "fr"):
        segments, info = model.transcribe(
            file_path,
            language="en",
            condition_on_previous_text=False,
            vad_filter=True,
        )

    return " ".join([segment.text for segment in segments]).strip()