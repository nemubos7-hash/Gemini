# Gemini Streamlit Starter (google-genai)

UI sederhana untuk mencoba **Gemini** via SDK `google-genai`:
- 💬 Text generation
- 🖼️ Vision (image + prompt)
- 🧱 Output JSON (opsional)

## 1) Persiapan
- Python 3.9+
- Buat virtualenv (opsional):
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # Windows: .venv\Scripts\activate
  ```

- Install dependency:
  ```bash
  pip install -r requirements.txt
  ```

## 2) Jalankan
```bash
streamlit run app.py
```

Masukkan **Gemini API key** di sidebar. Pilih model (`gemini-1.5-flash` atau `gemini-1.5-pro`).

## Catatan
- Fitur Vision membutuhkan upload gambar (PNG/JPG/WebP). 
- Mode JSON akan mengatur `response_mime_type="application/json"` agar model mengeluarkan JSON.
- Kamu bisa menambahkan `system_instruction`, `safety_settings`, atau `tools` sesuai kebutuhan.

## Troubleshooting
- **UNAUTHENTICATED / API key invalid**: periksa key dan quota.
- **Quota exceeded**: turunkan ukuran output tokens atau ganti model.
- **Model not found**: pastikan nama model benar dan tersedia di region akunmu.