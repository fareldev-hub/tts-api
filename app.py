import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

AUTHOR = "farel alfareza"
MODAL_URL = os.environ.get("MODAL_URL")

VOICE_CONFIG = {
    "female": {"language": "Malay"},
    "male": {"language": "Malay"},
}

@app.route("/api", methods=["GET"])
def tts_api():
    text = request.args.get("text", "")
    voice_type = request.args.get("type", "female")

    if not text:
        return jsonify({"status": "error", "author": AUTHOR, "error": "Parameter text diperlukan"}), 400
    if voice_type not in VOICE_CONFIG:
        return jsonify({"status": "error", "author": AUTHOR, "error": "type harus female atau male"}), 400

    config = VOICE_CONFIG[voice_type]

    try:
        resp = requests.post(
            MODAL_URL,
            json={"text": text, "language": config["language"]},
            timeout=180
        )
        data = resp.json()

        if "error" in data:
            return jsonify({"status": "error", "author": AUTHOR, "error": data["error"]}), 500

        return jsonify({
            "status": "success",
            "author": AUTHOR,
            "type": voice_type,
            "text": text,
            "audio_base64": data["audio_base64"],
            "message": "Audio berhasil dibuat (MOSS-TTS v1.5)"
        })
    except Exception as e:
        return jsonify({"status": "error", "author": AUTHOR, "error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok", "author": AUTHOR, "engine": "moss-tts-modal"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, threaded=True)