import os
import uuid
import time
import threading
from flask import Flask, request, jsonify, send_from_directory
from chatterbox.tts import ChatterboxTTS
import torchaudio as ta
import torch

app = Flask(__name__)

AUTHOR = "farel alfareza"

VOICE_DIR = os.environ.get("VOICE_DIR", "/data/voice" if os.path.exists("/data") else "./voice")
os.makedirs(VOICE_DIR, exist_ok=True)

VOICE_SAMPLES = {
    "female": os.environ.get("FEMALE_VOICE_PATH", "./voice_female.wav"),
    "male": os.environ.get("MALE_VOICE_PATH", "./voice_male.wav"),
}

AUDIO_EXPIRY_SECONDS = 3600

print("Loading Chatterbox model (CPU mode)...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = ChatterboxTTS.from_pretrained(device=device)
print(f"Model loaded on {device}")


def cleanup_expired_audio():
    while True:
        try:
            now = time.time()
            for filename in os.listdir(VOICE_DIR):
                if not filename.endswith(".wav"):
                    continue
                filepath = os.path.join(VOICE_DIR, filename)
                if now - os.path.getmtime(filepath) > AUDIO_EXPIRY_SECONDS:
                    os.remove(filepath)
                    print(f"Cleaned expired audio: {filename}")
        except Exception as e:
            print(f"Cleanup error: {e}")
        time.sleep(300)


cleanup_thread = threading.Thread(target=cleanup_expired_audio, daemon=True)
cleanup_thread.start()


@app.route('/api', methods=['GET'])
def tts_api():
    text = request.args.get('text', '')
    voice_type = request.args.get('type', 'female')

    if not text:
        return jsonify({
            "status": "error",
            "author": AUTHOR,
            "error": "Parameter text diperlukan"
        }), 400

    if voice_type not in VOICE_SAMPLES:
        return jsonify({
            "status": "error",
            "author": AUTHOR,
            "error": "type harus female atau male"
        }), 400

    sample_path = VOICE_SAMPLES[voice_type]
    if not os.path.exists(sample_path):
        return jsonify({
            "status": "error",
            "author": AUTHOR,
            "error": f"Sampel suara untuk {voice_type} tidak ditemukan: {sample_path}"
        }), 500

    try:
        exaggeration = 0.8 if voice_type == 'female' else 0.6

        wav = model.generate(
            text,
            audio_prompt_path=sample_path,
            exaggeration=exaggeration
        )

        filename = f"{uuid.uuid4().hex}.wav"
        filepath = os.path.join(VOICE_DIR, filename)
        ta.save(filepath, wav, model.sr)

        return jsonify({
            "status": "success",
            "author": AUTHOR,
            "type": voice_type,
            "text": text,
            "voice_file": f"/voice/{filename}",
            "expires_in_seconds": AUDIO_EXPIRY_SECONDS,
            "message": "Audio berhasil dibuat, otomatis dihapus setelah 1 jam"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "author": AUTHOR,
            "error": str(e)
        }), 500


@app.route('/voice/<filename>')
def serve_voice(filename):
    filepath = os.path.join(VOICE_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({
            "status": "error",
            "author": AUTHOR,
            "error": "File tidak ada atau sudah kedaluwarsa"
        }), 404
    if time.time() - os.path.getmtime(filepath) > AUDIO_EXPIRY_SECONDS:
        os.remove(filepath)
        return jsonify({
            "status": "error",
            "author": AUTHOR,
            "error": "File sudah kedaluwarsa"
        }), 404
    return send_from_directory(VOICE_DIR, filename)


@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "author": AUTHOR,
        "device": device
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)