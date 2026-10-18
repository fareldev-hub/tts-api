# Chatterbox TTS API

API Text-to-Speech sederhana berbasis Flask dan Chatterbox TTS, mendukung suara pria dan wanita, dengan hasil audio otomatis dihapus setelah 1 jam.

---

## Fitur

- Generate suara dari teks melalui endpoint `/api`
- Mendukung dua tipe suara: `female` (wanita) dan `male` (pria)
- Suara dihasilkan dengan teknik voice cloning dari sampel `.wav` yang disiapkan
- Ekspresi suara dapat diatur melalui parameter `exaggeration` (wanita lebih ekspresif, pria lebih stabil)
- File audio otomatis dihapus setelah 1 jam (3600 detik) melalui thread pembersihan latar belakang
- Response JSON
- Endpoint `/health` untuk pengecekan status layanan

---

## Struktur Proyek

```
.
├── app.py
├── requirements.txt
├── Dockerfile
├── voice_female.wav   (sampel suara wanita, 10-30 detik)
├── voice_male.wav     (sampel suara pria, 10-30 detik)
└── voice/             (direktori output, dibuat otomatis)
```

---

## Environment Variables

| Variabel | Default | Keterangan |
|---|---|---|
| `VOICE_DIR` | `/data/voice` jika `/data` ada, selain itu `./voice` | Direktori penyimpanan file audio |
| `FEMALE_VOICE_PATH` | `./voice_female.wav` | Path sampel suara wanita |
| `MALE_VOICE_PATH` | `./voice_male.wav` | Path sampel suara pria |
| `PORT` | `5000` (lokal), `8080` (Docker) | Port layanan |

---

## Endpoint

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

Pengecekan status layanan.

```json
{
  "status": "ok",
  "author": "farel alfareza",
  "device": "cpu"
}
```

---

## Instalasi Lokal (Windows / Linux)

1. Pastikan Python 3.11 dan FFmpeg sudah terinstal.
2. Buat virtual environment dan instal dependensi:

```bash
pip install -r requirements.txt
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

3. Siapkan `voice_female.wav` dan `voice_male.wav` di direktori proyek.
4. Jalankan:

```bash
python app.py
```

Layanan akan berjalan di `http://localhost:5000`.

---

## Deployment ke Railway

1. Push proyek ke GitHub (sertakan `voice_female.wav` dan `voice_male.wav`).
2. Di Railway pilih **New Project → Deploy from GitHub repo**, pilih repository.
3. Railway akan mendeteksi `Dockerfile` dan membangun image secara otomatis.
4. Tambahkan **Volume** dan mount ke `/data` agar file audio tersimpan persisten.
5. Atur environment variables:

```
VOICE_DIR=/data/voice
FEMALE_VOICE_PATH=./voice_female.wav
MALE_VOICE_PATH=./voice_male.wav
```

6. Di **Settings → Networking**, klik **Generate Domain** untuk mendapatkan URL publik.

---

## Catatan Penting

- **Chatterbox berjalan di CPU pada Railway**, sehingga proses generasi audio bisa memakan waktu beberapa detik hingga puluhan detik tergantung panjang teks. Untuk performa lebih baik, pertimbangkan menjalankan model di platform dengan GPU (misalnya Modal) dan menggunakan Railway hanya sebagai API layer.
- **Pemilihan pria/wanita sepenuhnya bergantung pada file sampel** yang Anda berikan. Untuk hasil terbaik, gunakan rekaman bersih 10-30 detik tanpa noise latar belakang.
- File audio disimpan di `VOICE_DIR` dan **otomatis dihapus setelah 1 jam** oleh thread pembersihan yang berjalan setiap 5 menit.
- Jika Railway Volume tidak dipasang, file akan hilang setiap kali container restart.

---

# Developer
By farel alfareza

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-black.svg)](https://flask.palletsprojects.com/)
[![Chatterbox TTS](https://img.shields.io/badge/Chatterbox-TTS-orange.svg)](https://github.com/resemble-ai/chatterbox)

# Support


[![Donate](https://img.shields.io/badge/Support-Saweria-orange?style=for-the-badge&logo=buymeacoffee&logoColor=white)](https://saweria.co/fareldev)