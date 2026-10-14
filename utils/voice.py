# utils/voice.py
# Free Urdu TTS using Edge TTS

import asyncio
import edge_tts
import nest_asyncio
import tempfile

nest_asyncio.apply()

VOICES = {
    "male_urdu": "ur-PK-AsadNeural",
    "female_urdu": "ur-PK-UzmaNeural",
    "male_english": "en-US-GuyNeural",
    "female_english": "en-US-JennyNeural"
}


async def _generate(text: str, voice: str, path: str):
    communicate = edge_tts.Communicate(
        text=text, voice=voice,
        rate="+5%", volume="+10%"
    )
    await communicate.save(path)


def text_to_speech(
    text: str,
    language: str = "en",
    gender: str = "male",
    output_path: str = None
) -> str:
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(
            suffix='.mp3', delete=False)
        output_path = tmp.name
        tmp.close()

    if language == "ur":
        voice = VOICES["female_urdu"] \
            if gender == "female" else VOICES["male_urdu"]
    else:
        voice = VOICES["female_english"] \
            if gender == "female" else VOICES["male_english"]

    try:
        asyncio.run(_generate(text, voice, output_path))
        return output_path
    except Exception as e:
        print(f"Voice error: {e}")
        return None