import modal
import io
import base64

app = modal.App("moss-tts-v15")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libsndfile1")
    .pip_install(
        "moss-tts-lite",
        "soundfile",
        "fastapi[standard]",
        "huggingface-hub",
    )
)

model_cache = modal.Volume.from_name("moss-tts-cache", create_if_missing=True)

@app.cls(
    image=image,
    gpu="L4",
    volumes={"/root/.cache": model_cache},
    scaledown_window=300,
    timeout=600,
)
class MossTTS:
    @modal.enter()
    def load_model(self):
        from moss_tts_lite.cli import synthesize
        self.synthesize = synthesize
        import subprocess
        subprocess.run([
            "huggingface-cli", "download",
            "baicai1145/MOSS-TTS-v1.5-W4GPTQ-w1",
            "--local-dir", "/root/.cache/moss-w4"
        ], check=True)

    @modal.method()
    def generate(self, text: str, language: str = "Malay"):
        import soundfile as sf
        wav, sr, _, _ = self.synthesize(
            text,
            output=None,
            model_dir="/root/.cache/moss-w4",
            quant="w4gptq",
            language=language,
        )
        buffer = io.BytesIO()
        sf.write(buffer, wav, sr, format="WAV")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

@app.function(image=image, gpu="L4")
@modal.fastapi_endpoint(method="POST")
def tts_endpoint(item: dict):
    text = item.get("text", "").strip()
    if not text:
        return {"error": "text required"}
    language = item.get("language", "Malay")
    model = MossTTS()
    audio_b64 = model.generate.remote(text, language)
    return {"status": "success", "audio_base64": audio_b64}