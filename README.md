# Zydra Voice

API Text-to-Speech sederhana berbasis Flask dan Piper TTS, mendukung suara pria dan wanita bahasa Indonesia, dengan UI web bawaan dan hasil audio otomatis dihapus setelah 1 jam.

---

## Fitur

- Generate suara dari teks melalui endpoint `/api`
- Mendukung dua tipe suara: `female` (wanita) dan `male` (pria), masing-masing memakai model Piper yang berbeda
- UI web sederhana di `/` untuk mencoba langsung dari browser
- File audio otomatis dihapus setelah 1 jam (3600 detik) melalui thread pembersihan latar belakang
- Response JSON menyertakan field `author`
- Endpoint `/health` untuk pengecekan status layanan dan status model

---

## Struktur Proyek

```
.
├── app.py
├── requirements.txt
├── Dockerfile
├── models/
│   ├── id_ID-news_tts-medium.onnx
│   ├── id_ID-news_tts-medium.onnx.json
│   ├── id_ID-ardi-medium.onnx
│   └── id_ID-ardi-medium.onnx.json
└── voice/             (direktori output, dibuat otomatis)
```

---

## Environment Variables

| Variabel | Default | Keterangan |
|---|---|---|
| `VOICE_DIR` | `./voice` | Direktori penyimpanan file audio hasil generate |
| `MODEL_DIR` | `./models` | Direktori penyimpanan model Piper |
| `PORT` | `8080` | Port layanan (di Railway diinjeksi otomatis) |

---

## Endpoint

### `GET /`

Menampilkan UI web sederhana untuk memasukkan teks, memilih suara pria/wanita, dan memutar hasil audio langsung di browser.

### `GET /api`

Menghasilkan audio dari teks.

**Query Parameters:**

| Parameter | Wajib | Nilai | Default |
|---|---|---|---|
| `text` | Ya | Teks yang akan diubah menjadi suara | — |
| `type` | Tidak | `female` atau `male` | `female` |

**Contoh Request:**

```
GET /api?type=female&text=Halo%20semua%2C%20apa%20kabar%3F
```

**Contoh Response Sukses:**

```json
{
  "status": "success",
  "author": "farel alfareza",
  "type": "female",
  "voice_used": "Wanita (id_ID-news_tts-medium)",
  "text": "Halo semua, apa kabar?",
  "voice_file": "/voice/3f2a1b9c8d7e4f6a.wav",
  "expires_in_seconds": 3600,
  "message": "Audio berhasil dibuat, otomatis dihapus setelah 1 jam"
}
```

**Contoh Response Error:**

```json
{
  "status": "error",
  "author": "farel alfareza",
  "error": "Parameter text diperlukan"
}
```

### `GET /voice/<filename>`

Mengunduh atau memutar file audio yang telah dihasilkan. Jika file sudah kedaluwarsa (lebih dari 1 jam), akan mengembalikan `404`.

### `GET /health`

Pengecekan status layanan dan status model.

```json
{
  "status": "ok",
  "author": "farel alfareza",
  "engine": "piper",
  "models": {
    "female": true,
    "male": true
  }
}
```

---

## Instalasi Lokal (Windows / Linux)

1. Pastikan Python 3.11 sudah terinstal.
2. Buat virtual environment dan instal dependensi:

```bash
pip install -r requirements.txt
```

3. Unduh model Piper bahasa Indonesia ke direktori `models/`:

```bash
mkdir -p models
wget -O models/id_ID-news_tts-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/id/id_ID/news_tts/medium/id_ID-news_tts-medium.onnx"
wget -O models/id_ID-news_tts-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/id/id_ID/news_tts/medium/id_ID-news_tts-medium.onnx.json"
wget -O models/id_ID-ardi-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/main/id/id_ID/ardi/medium/id_ID-ardi-medium.onnx"
wget -O models/id_ID-ardi-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/main/id/id_ID/ardi/medium/id_ID-ardi-medium.onnx.json"
```

4. Jalankan:

```bash
python app.py
```

Layanan akan berjalan di `http://localhost:8080`. Buka browser ke alamat tersebut untuk melihat UI.

---

## Deployment ke Railway

1. Push proyek ke GitHub.
2. Di Railway pilih **New Project → Deploy from GitHub repo**, pilih repository.
3. Railway akan mendeteksi `Dockerfile` dan membangun image secara otomatis. Model Piper diunduh saat build, sehingga tidak perlu di-commit ke Git.
4. Jika ingin file audio tersimpan persisten, tambahkan **Volume** dan mount ke `/data`, lalu atur `VOICE_DIR=/data/voice`.
5. Di **Settings → Networking**, klik **Generate Domain** untuk mendapatkan URL publik.

---

## Catatan Penting

- **Piper berjalan sepenuhnya di CPU**, dengan konsumsi memori rendah (di bawah 200 MB untuk dua model `medium`), sehingga cocok untuk paket gratis Railway.
- **Suara pria dan wanita memakai model yang berbeda**: `id_ID-news_tts-medium` untuk wanita, `id_ID-ardi-medium` untuk pria. Jika salah satu model gagal diunduh saat build, periksa ketersediaannya di repositori `rhasspy/piper-voices`.
- Kualitas suara Piper `medium` tergolong natural untuk ukurannya, tetapi tidak memiliki fitur cloning suara atau kontrol ekspresi seperti tertawa.
- File audio disimpan di `VOICE_DIR` dan **otomatis dihapus setelah 1 jam** oleh thread pembersihan yang berjalan setiap 5 menit.
- Jika Railway Volume tidak dipasang, file akan hilang setiap kali container restart.

---

# Developer
By farel alfareza

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-black.svg)](https://flask.palletsprojects.com/)
[![Piper TTS](https://img.shields.io/badge/Piper-TTS-green.svg)](https://github.com/rhasspy/piper)

# Support

[![Donate](https://img.shields.io/badge/Support-Saweria-orange?style=for-the-badge&logo=buymeacoffee&logoColor=white)](https://saweria.co/fareldev)