import os
import time
import streamlit as st
from google import genai
from google.genai import types

# ========== CONFIG ==========
st.set_page_config(page_title="Google Flow (Veo + Gemini)", layout="wide")
st.title("🎬 Google Flow — Video & Image Generator")
st.caption("Text→Video | Image→Video | Generate Image (Gemini Flash 2.5)")

# API Key
API_KEY = os.getenv("GEMINI_API_KEY") or st.text_input("🔑 Masukkan Gemini API Key", type="password")
if not API_KEY:
    st.stop()

client = genai.Client(api_key=API_KEY)

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Pengaturan")
    model_type = st.selectbox("Pilih Model", ["veo-3", "veo-3-fast", "veo-2"])
    aspect_ratio = st.selectbox("Aspect Ratio", ["16:9", "9:16"])
    resolution = st.selectbox("Resolusi", ["720p", "1080p"])
    negative_prompt = st.text_area("🛑 Negative Prompt (opsional)", "")
    seed = st.number_input("Seed (opsional)", min_value=0, step=1)
    batch = st.number_input("Batch size", min_value=1, max_value=5, value=1)

# ========== MODE ==========
tab1, tab2, tab3 = st.tabs(["📝 Text → Video", "🖼️ Image → Video", "✨ Generate Image"])

with tab1:
    st.subheader("Text → Video")
    text_prompts = st.text_area("Masukkan prompt (1 baris = 1 video)", height=150)
    if st.button("Generate Video dari Text"):
        if not text_prompts.strip():
            st.warning("Masukkan minimal 1 prompt.")
        else:
            prompts = [p.strip() for p in text_prompts.split("\n") if p.strip()]
            for i, prompt in enumerate(prompts, 1):
                st.info(f"🎬 Generating video {i}...")
                video = client.models.generate_videos(
                    model=model_type,
                    prompt=prompt,
                    config=types.GenerateVideosConfig(
                        aspect_ratio=aspect_ratio,
                        resolution=resolution,
                        negative_prompt=negative_prompt or None,
                        seed=seed if seed > 0 else None,
                    )
                )
                with st.spinner("⏳ Rendering..."):
                    while True:
                        status = client.models.get_generation(video.id)
                        if status.done:
                            break
                        time.sleep(3)
                st.video(status.output[0].uri)

with tab2:
    st.subheader("Image → Video")
    uploaded_files = st.file_uploader("Upload 1–5 gambar", type=["jpg", "png"], accept_multiple_files=True)
    if st.button("Generate Video dari Gambar"):
        if not uploaded_files:
            st.warning("Upload minimal 1 gambar.")
        else:
            for i, file in enumerate(uploaded_files, 1):
                st.info(f"🎬 Generating video dari gambar {i}...")
                video = client.models.generate_videos(
                    model=model_type,
                    prompt="",
                    image=open(file.name, "rb"),
                    config=types.GenerateVideosConfig(
                        aspect_ratio=aspect_ratio,
                        resolution=resolution,
                        negative_prompt=negative_prompt or None,
                        seed=seed if seed > 0 else None,
                    )
                )
                with st.spinner("⏳ Rendering..."):
                    while True:
                        status = client.models.get_generation(video.id)
                        if status.done:
                            break
                        time.sleep(3)
                st.video(status.output[0].uri)

with tab3:
    st.subheader("Generate Image (Gemini Flash 2.5)")
    image_prompts = st.text_area("Masukkan prompt gambar (1 baris = 1 output)", height=150)
    if st.button("Generate Gambar"):
        if not image_prompts.strip():
            st.warning("Masukkan minimal 1 prompt.")
        else:
            prompts = [p.strip() for p in image_prompts.split("\n") if p.strip()]
            for i, prompt in enumerate(prompts, 1):
                st.info(f"🖼️ Generating image {i}...")
                img = client.models.generate_images(
                    model="gemini-2.5-flash",
                    prompt=prompt,
                )
                st.image(img.output[0].uri)
