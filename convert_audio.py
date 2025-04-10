import os
from pathlib import Path
from pydub import AudioSegment


def convert_mp3_to_wav(input_dir="reference_speakers", output_dir=None, max_duration=None):
    """Конвертирует все MP3 в WAV с возможной обрезкой."""
    input_path = Path(input_dir)
    output_path = Path(output_dir or f"{input_dir}_wav")
    output_path.mkdir(exist_ok=True)

    for mp3_file in input_path.glob("*.mp3"):
        # Загрузка аудио
        audio = AudioSegment.from_mp3(mp3_file)

        # Обрезка (если задана max_duration)
        if max_duration:
            audio = audio[:max_duration * 1000]  # pydub работает в миллисекундах

        # Сохранение в WAV (16-bit, 22050 Гц, моно)
        wav_file = output_path / f"{mp3_file.stem}.wav"
        audio.export(
            wav_file,
            format="wav",
            codec="pcm_s16le",
            parameters=["-ar", "22050", "-ac", "1"]
        )
        print(f"Конвертирован: {mp3_file.name} → {wav_file.name}")


if __name__ == "__main__":
    # Настройки (измените при необходимости)
    INPUT_DIR = "reference_speakers"
    MAX_DURATION = 10  # в секундах (None, если обрезка не нужна)

    convert_mp3_to_wav(INPUT_DIR, max_duration=MAX_DURATION)