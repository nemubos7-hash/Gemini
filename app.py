import os
import io
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Gemini Starter (Text & Vision)", layout="wide")
st.title("🧪 Gemini Starter — Text & Vision")
st.caption("Masukkan API key, pilih model, lalu coba Text & Vision (gambar).")

# ---- Sidebar ----
with st.sidebar:
    st.header("🔑 API & Model")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AI...")
    model = st.selectbox(
        "Model",
        [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
        index=0
    )
    st.markdown("---")
    st.subheader("⚙️ Output Mode")
    as_json = st.toggle("Response sebagai JSON (application/json)", value=False)
    st.caption("Aktifkan jika kamu ingin output dalam format JSON.")

    st.markdown("---")
    st.subheader("ℹ️ Tips")
    st.write(
        "- Model *flash* lebih cepat dan murah, cocok untuk iterasi cepat.\n"
        "- Model *pro* lebih akurat untuk tugas kompleks.\n"
        "- Vision: kamu bisa unggah gambar lalu beri instruksi."
    )

if not api_key:
    st.info("Masukkan API key di sidebar untuk mulai.", icon="🔐")
    st.stop()

client = genai.Client(api_key=api_key)

tab_text, tab_vision, tab_json = st.tabs(["💬 Text", "🖼️ Vision (Image + Prompt)", "🧱 JSON Mode"])

# ---------- TEXT ----------
with tab_text:
    st.subheader("Text Generation")
    prompt = st.text_area("Prompt", value="Tuliskan 5 ide video YouTube bertema hewan lucu.", height=150)
    max_output = st.slider("Max output tokens", 256, 2048, 1024, step=128)
    if st.button("Generate Teks", type="primary"):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_output,
                    # kamu bisa tambahkan safety_settings atau system_instruction di sini
                )
            )
            st.success("Berhasil generate!")
            st.markdown(response.text or "_(kosong)_")
        except Exception as e:
            st.error(f"Error: {e}")

# ---------- VISION ----------
with tab_vision:
    st.subheader("Vision: Gambar + Prompt")
    uploaded = st.file_uploader("Unggah Gambar (PNG/JPG/WebP)", type=["png","jpg","jpeg","webp"])
    vision_prompt = st.text_area("Instruksi/pertanyaan untuk gambar", value="Jelaskan isi gambar secara rinci dan buat 3 caption alternatif.", height=120)
    col1, col2 = st.columns(2)
    with col1:
        max_output_v = st.slider("Max output tokens (Vision)", 256, 2048, 1024, step=128, key="maxoutv")
    with col2:
        mime_hint = st.text_input("MIME type override (opsional)", value="", placeholder="contoh: image/png")

    if st.button("Analisis Gambar", type="primary"):
        if not uploaded:
            st.warning("Mohon unggah gambar terlebih dahulu.")
        else:
            try:
                img_bytes = uploaded.read()
                mime_type = mime_hint.strip() or uploaded.type or "image/png"
                img_part = types.Part.from_bytes(img_bytes, mime_type=mime_type)
                text_part = types.Part.from_text(vision_prompt)

                response = client.models.generate_content(
                    model=model,
                    contents=[img_part, text_part],
                    config=types.GenerateContentConfig(
                        max_output_tokens=max_output_v,
                    )
                )
                st.success("Analisis selesai!")
                st.image(io.BytesIO(img_bytes), caption="Gambar yang diunggah", use_container_width=True)
                st.markdown("### Hasil")
                st.markdown(response.text or "_(kosong)_")
            except Exception as e:
                st.error(f"Error: {e}")

# ---------- JSON MODE ----------
with tab_json:
    st.subheader("Response JSON (schema opsional)")
    st.caption("Set 'Response sebagai JSON' di sidebar jika ingin MIME type JSON. "
               "Kalau tidak, hasil tetap teks biasa.")

    json_prompt = st.text_area(
        "Prompt (minta hasil berupa struktur data)",
        value="Buatkan daftar 3 ide konten: judul, target audiens, dan 3 poin utama.",
        height=140
    )

    schema_hint = st.text_area(
        "Skema JSON (opsional, untuk memberi contoh bentuk)",
        value='''{
  "ideas": [
    {"title": "", "audience": "", "bullets": ["", "", ""]}
  ]
}''',
        height=160
    )

    max_output_j = st.slider("Max output tokens (JSON)", 256, 4096, 1024, step=128, key="maxoutj")

    if st.button("Generate JSON", type="primary"):
        try:
            config = types.GenerateContentConfig(max_output_tokens=max_output_j)
            if as_json:
                # Set MIME type ke JSON untuk mendorong output JSON
                config.response_mime_type = "application/json"

            contents = [json_prompt]
            # Beri contoh skema sebagai conditioning (opsional)
            if schema_hint.strip():
                contents = [
                    types.Part.from_text("Keluarkan persis JSON valid mengikuti bentuk berikut tanpa komentar:"),
                    types.Part.from_text(schema_hint),
                    types.Part.from_text("Sekarang isi dengan data yang relevan untuk prompt berikut."),
                    types.Part.from_text(json_prompt),
                ]

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )

            st.success("Berhasil!")
            output = response.text or "{}"
            # Coba parse agar rapi, kalau gagal tampilkan apa adanya
            try:
                # Bersihkan code fences ```json
                cleaned = output.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.strip("`")
                    cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
                parsed = __import__("json").loads(cleaned)
                st.json(parsed)
            except Exception:
                st.code(output, language="json")
        except Exception as e:
            st.error(f"Error: {e}")