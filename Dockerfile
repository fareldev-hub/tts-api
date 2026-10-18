import os
import uuid
import time
import threading
import wave
from flask import Flask, request, jsonify, send_from_directory
from piper import PiperVoice

app = Flask(__name__)

AUTHOR = "farel alfareza"
AUDIO_EXPIRY_SECONDS = 3600
VOICE_DIR = os.environ.get("VOICE_DIR", "./voice")
MODEL_DIR = os.environ.get("MODEL_DIR", "./models")
os.makedirs(VOICE_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "id_ID-news_tts-medium.onnx")
CONFIG_PATH = os.path.join(MODEL_DIR, "id_ID-news_tts-medium.onnx.json")

print("[startup] Loading Piper voice model...", flush=True)
try:
    voice = PiperVoice.load(MODEL_PATH, config_path=CONFIG_PATH)
    print("[startup] Piper voice loaded.", flush=True)
except Exception as e:
    print(f"[startup] Failed to load Piper voice: {e}", flush=True)
    voice = None


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

    if voice is None:
        return jsonify({"status": "error", "author": AUTHOR, "error": "Model Piper belum dimuat"}), 500

    try:
        filename = f"{uuid.uuid4().hex}.wav"
        filepath = os.path.join(VOICE_DIR, filename)

        with wave.open(filepath, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)

        return jsonify({
            "status": "success",
            "author": AUTHOR,
            "type": voice_type,
            "voice_used": "id_ID-news_tts-medium",
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
        "engine": "piper",
        "model_loaded": voice is not None,
        "model": "id_ID-news_tts-medium"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[startup] Flask on 0.0.0.0:{port}", flush=True)
    app.run(host="0.0.0.0", port=port, threaded=True)