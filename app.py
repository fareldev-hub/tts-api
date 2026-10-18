import os
import uuid
import time
import threading
import numpy as np
import soundfile as sf
from flask import Flask, request, jsonify, send_from_directory
from huggingface_hub import hf_hub_download
import onnxruntime as ort
from ttstokenizer import IPATokenizer
import json
import nltk

nltk.download('averaged_perceptron_tagger_eng', quiet=True)

app = Flask(__name__)

AUTHOR = "farel alfareza"
AUDIO_EXPIRY_SECONDS = 3600
VOICE_DIR = os.environ.get("VOICE_DIR", "./voice")
os.makedirs(VOICE_DIR, exist_ok=True)

VOICE_MAP = {
    "female": os.environ.get("FEMALE_VOICE", "af_bella"),
    "male": os.environ.get("MALE_VOICE", "am_michael"),
}

print("[startup] Downloading Kokoro ONNX model...", flush=True)
model_path = hf_hub_download(
    repo_id="NeuML/kokoro-int8-onnx",
    filename="model.onnx"
)
voices_path = hf_hub_download(
    repo_id="NeuML/kokoro-int8-onnx",
    filename="voices.json"
)
print("[startup] Model downloaded.", flush=True)

with open(voices_path, "r", encoding="utf-8") as f:
    voices_data = json.load(f)

session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])

try:
    nltk.data.find('taggers/averaged_perceptron_tagger_eng')
except LookupError:
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)

tokenizer = IPATokenizer()
print("[startup] ONNX session ready.", flush=True)


def synthesize(text, voice_name, speed=1.0):
    inputs = tokenizer(text)
    speaker_key = voice_name.split("_")[0]
    speaker = np.array(voices_data[speaker_key], dtype=np.float32)
    style = speaker[len(inputs)]

    outputs = session.run(None, {
        "tokens": [[0, *inputs, 0]],
        "style": style,
        "speed": np.ones(1, dtype=np.float32) * speed
    })
    return outputs[0]


def cleanup_expired_audio():
    while True:
        try:
            now = time.time()
            for filename in os.listdir(VOICE_DIR):
                if not filename.lower().endswith(".wav"):
                    continue
                filepath = os.path.join(VOICE_DIR, filename)
                if now - os.path.getmtime(filepath) > AUDIO_EXPIRY_SECONDS:
                    os.remove(filepath)
                    print(f"[cleanup] Removed: {filename}", flush=True)
        except Exception as e:
            print(f"[cleanup] Error: {e}", flush=True)
        time.sleep(300)


threading.Thread(target=cleanup_expired_audio, daemon=True).start()
print("[startup] Cleanup thread started.", flush=True)


@app.route("/api", methods=["GET"])
def tts_api():
    text = request.args.get("text", "")
    voice_type = request.args.get("type", "female")

    if not text:
        return jsonify({"status": "error", "author": AUTHOR, "error": "Parameter text diperlukan"}), 400

    if voice_type not in VOICE_MAP:
        return jsonify({"status": "error", "author": AUTHOR, "error": "type harus female atau male"}), 400

    voice_name = VOICE_MAP[voice_type]

    try:
        audio = synthesize(text, voice_name)
        filename = f"{uuid.uuid4().hex}.wav"
        filepath = os.path.join(VOICE_DIR, filename)
        sf.write(filepath, audio, 24000)

        return jsonify({
            "status": "success",
            "author": AUTHOR,
            "type": voice_type,
            "voice_used": voice_name,
            "text": text,
            "voice_file": f"/voice/{filename}",
            "expires_in_seconds": AUDIO_EXPIRY_SECONDS,
            "message": "Audio berhasil dibuat, otomatis dihapus setelah 1 jam"
        })
    except Exception as e:
        print(f"[api] Error: {e}", flush=True)
        return jsonify({"status": "error", "author": AUTHOR, "error": str(e)}), 500


@app.route("/voice/<filename>")
def serve_voice(filename):
    filepath = os.path.join(VOICE_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"status": "error", "author": AUTHOR, "error": "File tidak ada atau sudah kedaluwarsa"}), 404
    if time.time() - os.path.getmtime(filepath) > AUDIO_EXPIRY_SECONDS:
        os.remove(filepath)
        return jsonify({"status": "error", "author": AUTHOR, "error": "File sudah kedaluwarsa"}), 404
    return send_from_directory(VOICE_DIR, filename)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "author": AUTHOR,
        "engine": "kokoro-onnx",
        "voices": VOICE_MAP
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[startup] Flask on 0.0.0.0:{port}", flush=True)
    app.run(host="0.0.0.0", port=port, threaded=True)