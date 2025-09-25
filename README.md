# Gemini Playground — AI Studio–like (Plus)

**Tambahan fitur:**
- ✅ Multi-prompt **Text→Video** (1 baris = 1 job), dengan opsi **aspect ratio (termasuk 9:16)**, durasi, seed, dan mode.
- ✅ Multi-prompt **Image→Video** (upload banyak gambar, 1 baris prompt per gambar), opsi **aspect ratio (9:16)**, durasi, seed.
- ✅ **Generate Image** via "Gemini 2.5 Flash Image" (dengan fallback; beberapa akun membutuhkan model Imagen-3.0/fast).

> ⚠️ **Catatan penting video**: Pembuatan video (Text→Video, Image→Video) umumnya memakai endpoint **Veo/Vertex AI** yang belum tersedia di semua akun/SDK. App ini menyiapkan **antrean jobs** dan export ke JSON. Ketika endpoint tersedia, ganti bagian **placeholder** dengan pemanggilan API video yang sesuai.

## Jalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Integrasi Video API
Ganti blok bertanda komentar `# Placeholder for Veo/Vertex call` dengan kode pemanggilan layanan video (misal Veo/Vertex). Contoh pseudo:

```python
video = veo.generate_video(prompt=line, aspect_ratio="9:16", duration_seconds=8, mode="preview", seed=seed)
save_url = video.media[0].uri  # contoh
```

## Image Generation
Tab **Generate Image** mencoba beberapa `model_id` umum:
- `gemini-2.5-flash` (jika mendukung image gen)
- `gemini-2.5-flash-image` (nama alternatif)
- `imagen-3.0-fast` atau `imagen-3.0` (umum untuk Image generation)

Jika akunmu belum mengaktifkan model image gen, hasil bisa berupa **teks** atau error. Pastikan project/region dan quota sudah benar.