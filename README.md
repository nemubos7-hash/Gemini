# Gemini Playground — AI Studio–like

Tampilan Streamlit yang meniru *feel* Google AI Studio: panel konfigurasi di kiri, playground/chat di kanan, dan tab Request/Response untuk mengintip objek mentah.

## Fitur
- Chat/playground dengan **Prompt**, **attachment gambar**, dan **system instruction**
- Panel **Generation Config**: temperature, top_p, top_k, max_output_tokens
- **Riwayat** percakapan dalam sesi
- Tab **Request/Response**: pratinjau request & objek response mentah
- Gaya UI gelap mirip AI Studio

## Jalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```
Masukkan **Gemini API key** di sidebar.

## Catatan
- Menggunakan SDK resmi `google-genai`
- Attachment hanya gambar (PNG/JPG/WebP); bisa tambahkan MIME override bila diperlukan.