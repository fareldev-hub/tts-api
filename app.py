import os
import uuid
import time
import threading
import glob
from flask import Flask, request, jsonify, send_from_directory
import torch
import torchaudio as ta

app = Flask(__name__)

AUTHOR = "farel alfareza"
AUDIO_EXPIRY_SECONDS = 3600

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.environ.get("VOICE_DIR", "/data/voice" if os.path.exists("/data") else os.path.join(BASE_DIR, "voice"))
os.makedirs(VOICE_DIR, exist_ok=True)

CANDIDATE_DIRS = [
    BASE_DIR,
    os.getcwd(),
    "/app",
    "/data",
    os.path.join(BASE_DIR, "voice"),
]


def find_wav(name_hint):
    candidates = [
        os.environ.get("FEMALE_VOICE_PATH" if name_hint == "female" else "MALE_VOICE_PATH"),
        os.path.join(BASE_DIR, f"voice_{name_hint}.wav"),
        os.path.join(os.getcwd(), f"voice_{name_hint}.wav"),
        os.path.join("/app", f"voice_{name_hint}.wav"),
        os.path.join("/data", f"voice_{name_hint}.wav"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    for d in CANDIDATE_DIRS:
        if not os.path.isdir(d):
            continue
        for pattern in [f"*{name_hint}*.wav", f"*{name_hint}*.WAV"]:
            matches = glob.glob(os.path.join(d, pattern))
            if matches:
                return matches[0]
    return None


def list_available_wavs():
    found = []
    for d in CANDIDATE_DIRS:
        if os.path.isdir(d):
            for f in glob.glob(os.path.join(d, "*.wav")) + glob.glob(os.path.join(d, "*.WAV")):
                found.append(f)
    return sorted(set(found))


_model = None
_model_lock = threading.Lock()
_device = "cuda" if torch.cuda.is_available() else "cpu"


def get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                print(f"[startup] Loading Chatterbox model on {_device}...", flush=True)
                from chatterbox.tts import ChatterboxTTS
                _model = ChatterboxTTS.from_pretrained(device=_device)
                print("[startup] Model loaded successfully.", flush=True)
    return _model


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
                    print(f"[cleanup] Removed expired audio: {filename}", flush=True)
        except Exception as e:
            print(f"[cleanup] Error: {e}", flush=True)
        time.sleep(300)


cleanup_thread = threading.Thread(target=cleanup_expired_audio, daemon=True)
cleanup_thread.start()
print("[startup] Cleanup thread started.", flush=True)
print(f"[startup] BASE_DIR={BASE_DIR}", flush=True)
print(f"[startup] CWD={os.getcwd()}", flush=True)
print(f"[startup] VOICE_DIR={VOICE_DIR}", flush=True)
print(f"[startup] WAV files found: {list_available_wavs()}", flush=True)


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

    if voice_type not in ("female", "male"):
        return jsonify({
            "status": "error",
            "author": AUTHOR,
            "error": "type harus female atau male"
        }), 400

    sample_path = find_wav(voice_type)

    try:
        model = get_model()
        exaggeration = 0.8 if voice_type == 'female' else 0.6

        if sample_path:
            print(f"[api] Using sample: {sample_path}", flush=True)
            wav = model.generate(
                text,
                audio_prompt_path=sample_path,
                exaggeration=exaggeration
            )
        else:
            print(f"[api] No sample found for {voice_type}, generating default voice.", flush=True)
            wav = model.generate(text)

        filename = f"{uuid.uuid4().hex}.wav"
        filepath = os.path.join(VOICE_DIR, filename)
        ta.save(filepath, wav, model.sr)

        return jsonify({
            "status": "success",
            "author": AUTHOR,
            "type": voice_type,
            "text": text,
            "voice_file": f"/voice/{filename}",
            "sample_used": sample_path if sample_path else None,
            "expires_in_seconds": AUDIO_EXPIRY_SECONDS,
            "message": "Audio berhasil dibuat, otomatis dihapus setelah 1 jam"
        })

    except Exception as e:
        print(f"[api] Error: {e}", flush=True)
        return jsonify({
            "status": "error",
            "author": AUTHOR,
            "error": str(e),
            "available_wavs": list_available_wavs(),
            "searched_dirs": CANDIDATE_DIRS
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
        "device": _device,
        "model_loaded": _model is not None,
        "base_dir": BASE_DIR,
        "cwd": os.getcwd(),
        "voice_dir": VOICE_DIR,
        "available_wavs": list_available_wavs()
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    print(f"[startup] Starting Flask on 0.0.0.0:{port}", flush=True)
    app.run(host='0.0.0.0', port=port, threaded=True)