from faster_whisper import WhisperModel
import io

# 模型 (tiny, base, small, medium, large)
model = WhisperModel("small", device="cpu", compute_type="int8")

def stt_whisper(audio_bytes: bytes, prompt_text: str = ""):
    # 將資料庫的標籤作為 initial_prompt 傳入
    segments, info = model.transcribe(
        io.BytesIO(audio_bytes), 
        beam_size=5,
        # 使用繁體中文的暗示，並帶入動態標籤
        initial_prompt=f"這是一個關於生活紀錄的繁體中文語音。相關詞彙：{prompt_text}"
    )
    
    text = "".join([segment.text for segment in segments])
    print(f"Whisper 辨識結果: {text}")
    return text