import modal
import io
import base64

app = modal.App("chatterbox-multilingual-tts")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libsndfile1", "git")
    .pip_install(
        "chatterbox-tts",
        "soundfile",
        "fastapi[standard]",
        "huggingface-hub[hf_transfer]",
    )
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

hf_cache = modal.Volume.from_name("chatterbox-cache", create_if_missing=True)

@app.cls(
    image=image,
    gpu="L4",
    volumes={"/root/.cache/huggingface": hf_cache},
    scaledown_window=300,
    timeout=600,
)
class Chatterbox:
    @modal.enter()
    def load_model(self):
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        self.model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")
        print("Chatterbox Multilingual loaded")

    @modal.method()
    def generate(self, text: str, language: str = "ms", exaggeration: float = 0.7):
        import torchaudio as ta
        wav = self.model.generate(
            text,
            language_id=language,
            exaggeration=exaggeration,
            cfg_weight=0.4,
        )
        buffer = io.BytesIO()
        ta.save(buffer, wav, self.model.sr, format="wav")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

@app.function(image=image, gpu="L4")
@modal.fastapi_endpoint(method="POST")
def tts_endpoint(item: dict):
    text = item.get("text", "").strip()
    if not text:
        return {"error": "text required"}
    language = item.get("language", "ms")
    exaggeration = float(item.get("exaggeration", 0.7))
    model = Chatterbox()
    audio_b64 = model.generate.remote(text, language, exaggeration)
    return {"status": "success", "audio_base64": audio_b64}