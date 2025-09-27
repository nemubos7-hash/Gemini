import os
import time
import streamlit as st
from google import genai
from google.genai import types

# ====== Konfigurasi Awal ======
st.set_page_config(page_title="Google Flow (Veo + Gemini)", layout="wide")
st.title("🎬 Google Flow — Veo + Gemini")
st.caption("Text→Video, Image→Video, dan Generate Image (Gemini 2.5 Flash)")

# ====== API Key ======
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    API_KEY = st.text_input("🔑 Masukkan Google Gemini API Key:", type="password")

if not API_KEY:
    st.warning("Masukkan API Key dulu untuk lanjut.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# ====== Fungsi Download Video ======
def download_video_file(video_ref, filename: str) -> bytes:
    """Download file video, return bytes"""
    file_obj = client.files.download(file=video_ref)
    data = file_obj.bytes
    with open(filename, "wb") as f:
        f.write(data)
    return data

# ====== Fungsi Polling Proses ======
def wait_for_operation(op):
    with st.spinner("⏳ Rendering video... tunggu sebentar"):
        while not op.done:
            time.sleep(3)
            op = client.operations.get(name=op.name)
    return op

# ====== Text to Video ======
def run_text_to_video(prompts, aspect, resolution, negative, seed):
    with st.spinner("🚀 Kirim prompt ke model..."):
        try:
            op = client.models.generate_videos(
                model="veo-3",
                config=types.GenerateVideosConfig(
                    input=prompts,
                    aspect_ratio=aspect,
                    resolution=resolution,
                    negative_prompt=negative,
                    seed=seed if seed else None,
                )
            )
        except Exception as e:
            st.error(f"Gagal submit prompt: {e}")
            return

    op = wait_for_operation(op)

    if not op.result.videos:
        st.error("❌ Tidak ada hasil video.")
        return

    for i, vid in enumerate(op.result.videos):
        fname = f"text2video_{i}.mp4"
        data = download_video_file(vid.video, fname)
        st.video(data)
        st.download_button("⬇️ Download MP4", data=data, file_name=fname, mime="video/mp4")

# ====== Image to Video ======
def run_image_to_video(imgs, prompts, aspect, resolution, negative, seed):
    with st.spinner("🚀 Kirim gambar + prompt ke model..."):
        try:
            op = client.models.generate_videos(
                model="veo-3",
                config=types.GenerateVideosConfig(
                    input=prompts,
                    aspect_ratio=aspect,
                    resolution=resolution,
                    negative_prompt=negative,
                    seed=seed if seed else None,
                ),
                images=imgs
            )
        except Exception as e:
            st.error(f"Gagal submit image2video: {e}")
            return

    op = wait_for_operation(op)

    if not op.result.videos:
        st.error("❌ Tidak ada hasil video.")
        return

    for i, vid in enumerate(op.result.videos):
        fname = f"image2video_{i}.mp4"
        data = download_video_file(vid.video, fname)
        st.video(data)
        st.download_button("⬇️ Download MP4", data=data, file_name=fname, mime="video/mp4")

# ====== UI Tabs ======
tab1, tab2, tab3 = st.tabs(["Text → Video", "Image → Video", "Generate Image"])

with tab1:
    st.subheader("📝 Text → Video")
    prompts = st.text_area("Prompt (1 baris = 1 video)", height=150)
    aspect = st.selectbox("Aspect Ratio", ["16:9", "9:16"])
    resolution = st.selectbox("Resolution", ["720p", "1080p"])
    negative = st.text_area("Negative Prompt (opsional)")
    seed = st.text_input("Seed (opsional)")
    if st.button("🎬 Generate dari Text"):
        if prompts.strip():
            run_text_to_video(prompts.splitlines(), aspect, resolution, negative, seed)

with tab2:
    st.subheader("🖼️ Image → Video")
    imgs = st.file_uploader("Upload gambar (bisa multi)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    prompts = st.text_area("Prompt (1 baris = 1 video)", height=150)
    aspect = st.selectbox("Aspect Ratio (Image→Video)", ["16:9", "9:16"])
    resolution = st.selectbox("Resolution (Image→Video)", ["720p", "1080p"])
    negative = st.text_area("Negative Prompt (opsional, image→video)")
    seed = st.text_input("Seed (opsional, image→video)")
    if st.button("🎬 Generate dari Image"):
        if imgs and prompts.strip():
            run_image_to_video(imgs, prompts.splitlines(), aspect, resolution, negative, seed)

with tab3:
    st.subheader("🖌️ Generate Image (Gemini 2.5 Flash)")
    prompt = st.text_area("Prompt gambar")
    if st.button("🖼️ Generate Gambar"):
        try:
            result = client.models.generate_images(
                model="gemini-2.5-flash",
                prompt=prompt
            )
            for i, img in enumerate(result.images):
                st.image(img.inline_data.data, caption=f"Image {i+1}")
        except Exception as e:
            st.error(f"❌ Error generate gambar: {e}")
