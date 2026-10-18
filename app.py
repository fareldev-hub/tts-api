import os
import uuid
import time
import threading
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from chatterbox_onnx import ChatterboxOnnx

app = Flask(__name__)

AUTHOR = "farel alfareza"
AUDIO_EXPIRY_SECONDS = 3600
VOICE_DIR = os.environ.get("VOICE_DIR", "./voice")
os.makedirs(VOICE_DIR, exist_ok=True)

# Inisialisasi Chatterbox ONNX (kuantisasi Q4 untuk hemat memori)
print("[startup] Initializing Chatterbox ONNX (quantized)...", flush=True)
synthesizer = ChatterboxOnnx(quantized=True)
print("[startup] Chatterbox ONNX ready.", flush=True)


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
    if voice_type not in ("female", "male"):
        return jsonify({"status": "error", "author": AUTHOR, "error": "type harus female atau male"}), 400

    filename = f"{uuid.uuid4().hex}.wav"
    filepath = os.path.join(VOICE_DIR, filename)

    try:
        # Chatterbox ONNX mendukung voice cloning via target_voice_path.
        # Jika Anda punya sampel suara pria/wanita, letakkan di folder ./voices/
        # dan sesuaikan path di bawah. Untuk saat ini, gunakan suara default.
        exaggeration = 0.8 if voice_type == "female" else 0.5

        synthesizer.synthesize(
            text=text,
            target_voice_path=None,
            exaggeration=exaggeration,
            output_file_name=filepath,
            apply_watermark=False,
        )

        return jsonify({
            "status": "success",
            "author": AUTHOR,
            "type": voice_type,
            "text": text,
            "voice_file": f"/voice/{filename}",
            "expires_in_seconds": AUDIO_EXPIRY_SECONDS,
            "message": "Audio berhasil dibuat (Chatterbox ONNX), otomatis dihapus setelah 1 jam"
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
        "engine": "chatterbox-onnx",
        "quantized": True,
    })


UI_HTML = """
<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>Zydra Voice</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; background: #f6f7fb; color: #1f2937; }
  h1 { font-size: 1.5rem; margin-bottom: 4px; }
  .author { color: #6b7280; font-size: 0.9rem; margin-bottom: 24px; }
  label { display: block; font-weight: 600; margin: 16px 0 6px; }
  textarea, select, button { width: 100%; font-size: 1rem; padding: 10px; border-radius: 8px; border: 1px solid #d1d5db; box-sizing: border-box; }
  textarea { min-height: 100px; resize: vertical; }
  button { background: #2563eb; color: #fff; border: none; cursor: pointer; margin-top: 16px; font-weight: 600; }
  button:disabled { background: #93c5fd; cursor: not-allowed; }
  .status { margin-top: 16px; font-size: 0.9rem; color: #6b7280; }
  audio { width: 100%; margin-top: 16px; }
  .error { color: #dc2626; }
</style>
</head>
<body>
  <h1>Zydra Voice</h1>
  <div class="author">oleh farel alfareza</div>

  <label for="text">Teks</label>
  <textarea id="text" placeholder="Tulis teks di sini...">Halo, ini adalah contoh suara dari Zydra Voice.</textarea>

  <label for="type">Suara</label>
  <select id="type">
    <option value="female">Wanita</option>
    <option value="male">Pria</option>
  </select>

  <button id="btn" onclick="generate()">Buat Suara</button>

  <div id="status" class="status"></div>
  <div id="player"></div>

<script>
async function generate() {
  const text = document.getElementById('text').value.trim();
  const type = document.getElementById('type').value;
  const btn = document.getElementById('btn');
  const status = document.getElementById('status');
  const player = document.getElementById('player');

  if (!text) {
    status.className = 'status error';
    status.textContent = 'Teks tidak boleh kosong.';
    return;
  }

  btn.disabled = true;
  status.className = 'status';
  status.textContent = 'Memproses... (mungkin butuh beberapa detik)';
  player.innerHTML = '';

  try {
    const res = await fetch(`/api?type=${encodeURIComponent(type)}&text=${encodeURIComponent(text)}`);
    const data = await res.json();

    if (data.status !== 'success') {
      throw new Error(data.error || 'Gagal membuat suara');
    }

    status.className = 'status';
    status.textContent = 'Berhasil. File otomatis dihapus setelah 1 jam.';
    const audio = document.createElement('audio');
    audio.controls = true;
    audio.src = data.voice_file;
    player.appendChild(audio);

    const dl = document.createElement('a');
    dl.href = data.voice_file;
    dl.textContent = 'Unduh audio';
    dl.style.display = 'block';
    dl.style.marginTop = '8px';
    dl.setAttribute('download', '');
    player.appendChild(dl);
  } catch (e) {
    status.className = 'status error';
    status.textContent = e.message;
  } finally {
    btn.disabled = false;
  }
}
</script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(UI_HTML)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[startup] Flask on 0.0.0.0:{port}", flush=True)
    app.run(host="0.0.0.0", port=port, threaded=True)