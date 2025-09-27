
import os
import time
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Google Flow Style Veo Generator", layout="wide")
st.title("🎬 Google Flow — Veo 3 Video Generator")
st.caption("Text→Video, Image→Video, dan Generate Image (Gemini Flash 2.5). Ala Google Flow.")

# ========== API KEY ==========
API_KEY = st.text_input("Masukkan Gemini API Key", type="password")
if API_KEY:
    client = genai.Client(api_key=API_KEY)

# ========== STEP 1: INPUT PROMPT ==========
st.header("1. Input Prompt & Gambar")
multi_prompt = st.text_area("Masukkan prompt (1 baris = 1 output)", height=200)
uploaded_files = st.file_uploader("Upload gambar untuk Image→Video (bisa banyak)", type=["png","jpg","jpeg"], accept_multiple_files=True)

# ========== STEP 2: CONFIGURASI ==========
st.header("2. Konfigurasi")
model = st.selectbox("Pilih Model", ["veo-3-preview", "veo-3-fast", "veo-3-quality", "veo-2"])
aspect_ratio = st.selectbox("Aspect Ratio", ["16:9", "9:16", "1:1"])
resolution = st.radio("Resolusi", ["720p", "1080p"])
seed = st.text_input("Seed (untuk hasil konsisten, kosongkan jika random)")
batch_size = st.number_input("Batch Size", min_value=1, max_value=10, value=1)
negative_prompt = st.text_area("Negative Prompt (opsional)")

# ========== STEP 3: EKSEKUSI ==========
st.header("3. Eksekusi")
if st.button("🚀 Generate Video"):
    if not API_KEY:
        st.error("Masukkan API Key dulu.")
    else:
        prompts = [p.strip() for p in multi_prompt.split("\n") if p.strip()]
        if not prompts:
            st.error("Isi minimal 1 prompt.")
        else:
            for i, p in enumerate(prompts):
                with st.spinner(f"Render video {i+1}/{len(prompts)}..."):
                    try:
                        video = client.models.generate_content(
                            model=model,
                            contents=[p],
                            config=types.GenerateContentConfig(
                                aspect_ratio=aspect_ratio,
                                video=types.VideoConfig(
                                    resolution=resolution,
                                    seed=int(seed) if seed else None
                                )
                            )
                        )
                        st.video(video.candidates[0].video.uri)
                        st.success(f"✅ Video {i+1} selesai!")
                    except Exception as e:
                        st.error(f"Gagal render video {i+1}: {e}")
