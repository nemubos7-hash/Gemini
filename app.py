import os  
import io  
import time  
import streamlit as st  
from typing import List, Optional  
  
from google import genai  
from google.genai import types  
  
# ================== UI & TITLE ==================  
st.set_page_config(page_title="Veo Generator (Flow Style)", layout="wide")  
st.title("🎬 Veo Generator — Flow Style")  
st.caption("① Inputs → ② Guardrails & Config → ③ Render • Batch multi-prompt, Image→Video multi • 16:9/9:16 • negativePrompt • seed")  
  
# ================== API KEY ==================  
API_KEY = None  
# Ambil dari Secrets jika ada  
try:  
    API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")  
except Exception:  
    API_KEY = None  
# Fallback ENV  
API_KEY = API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")  
  
with st.sidebar:  
    st.header("🔑 API Key")  
    key_in = st.text_input("Gemini API Key (opsional, override Secrets/ENV)", type="password")  
    if key_in:  
        API_KEY = key_in  
  
if not API_KEY:  
    st.warning("Masukkan API key di sidebar, atau set GEMINI_API_KEY di Secrets/ENV.")  
    st.stop()  
  
# Init client  
try:  
    client = genai.Client(api_key=API_KEY)  
except Exception as e:  
    st.error(f"Gagal inisialisasi client: {e}")  
    st.stop()  
  
# ================== MODEL MAPS ==================  
VIDEO_MODEL_LABELS = {  
    "Veo 3 (Quality)": "veo-3.0-generate-001",  
    "Veo 3 (Fast)": "veo-3.0-fast-generate-001",  
    "Veo 2": "veo-2.0-generate-001",  
}  
# Fallback kandidat nama model jika ada perbedaan naming di region/akun  
VIDEO_MODEL_FALLBACKS = {  
    "Veo 3 (Quality)": ["veo-3.0-generate-001"],  
    "Veo 3 (Fast)": ["veo-3.0-fast-generate-001"],  
    "Veo 2": ["veo-2.0-generate-001", "veo-2.0-preview-001", "veo-2.0"],  
}  
  
# ================== HELPERS ==================  
def build_video_config(aspect: str, resolution: str, negative: str, seed: int, person_generation: Optional[str] = None):  
    """Buat config yang kompatibel lintas-versi."""  
    if aspect == "9:16" and resolution == "1080p":  
        resolution = "720p"  
  
    base_snake = {  
        "aspect_ratio": aspect,  
        "resolution": resolution,  
    }  
    if negative.strip():  
        base_snake["negative_prompt"] = negative.strip()  
    if seed and int(seed) > 0:  
        base_snake["seed"] = int(seed)  
    if person_generation:  
        base_snake["person_generation"] = person_generation  
  
    if hasattr(types, "GenerateVideosConfig"):  
        try:  
            return types.GenerateVideosConfig(**base_snake)  
        except Exception:  
            pass  
  
    return dict(base_snake)  
  
def to_image_payload(uploaded) -> Optional[types.Image]:  
    if not uploaded:  
        return None  
    data = uploaded.read()  
    mime = uploaded.type or "image/png"  
    return types.Image(image_bytes=data, mime_type=mime)  
  
def poll_operation(op):  
    """Polling long-running operation sampai selesai."""  
    while True:  
        try:  
            op = client.operations.get(op)  
        except Exception:  
            pass  
        if getattr(op, "done", False):  
            return op  
        time.sleep(3)  
  
def download_video_file(video_ref, filename: str) -> bytes:  
    """Download file video, return bytes."""  
    file_obj = client.files.download(file=video_ref)  
    data = file_obj.bytes  # ambil bytes langsung  
  
    # Simpan juga ke file lokal  
    with open(filename, "wb") as f:  
        f.write(data)  
  
    return data  
  
def generate_with_fallback(model_label: str, prompt: str, cfg, image: Optional[types.Image] = None):  
    names = VIDEO_MODEL_FALLBACKS.get(model_label, [VIDEO_MODEL_LABELS[model_label]])  
    last_err = None  
    for name in names:  
        try:  
            return client.models.generate_videos(  
                model=name,  
                prompt=prompt,  
                image=image,  
                config=cfg,  
            ), name  
        except Exception as e:  
            last_err = e  
            try:  
                safe_cfg = build_video_config("16:9", "720p", negative="", seed=0)  
                return client.models.generate_videos(model=name, prompt=prompt, image=image, config=safe_cfg), name  
            except Exception as e2:  
                last_err = e2  
                continue  
    raise last_err  
  
# ================== LAYOUT FLOW ==================  
st.header("① Inputs")  
prompts_text = st.text_area(  
    "📝 Masukkan prompt (1 baris = 1 video). Untuk Image→Video, baris ke-N dipasangkan dengan gambar ke-N.",  
    height=160,  
)  
uploaded_images = st.file_uploader(  
    "🖼️ (Opsional) Upload beberapa gambar untuk Image→Video.",  
    type=["png", "jpg", "jpeg", "webp"],  
    accept_multiple_files=True  
)  
  
st.header("② Guardrails & Config")  
c1, c2, c3, c4 = st.columns(4)  
with c1:  
    model_label = st.selectbox("Model", list(VIDEO_MODEL_LABELS.keys()), index=0)  
with c2:  
    aspect = st.selectbox("Aspect Ratio", ["16:9", "9:16"], index=0)  
with c3:  
    resolution = st.selectbox("Resolution", ["720p", "1080p"], index=0)  
with c4:  
    seed = st.number_input("Seed (opsional)", min_value=0, step=1, value=0)  
  
neg = st.text_input("Negative Prompt (opsional)", value="low quality, blurry, watermark, noisy")  
person_generation = st.selectbox("Person Generation Policy", ["allow_all", "allow_adult", "dont_allow"], index=0)  
  
st.header("③ Render")  
btn_text = st.button("🚀 Generate dari Text (abaikan gambar)")  
btn_image = st.button("🚀 Generate dari Image (pasangkan dengan baris prompt)")  
  
# ================== ACTIONS ==================  
def run_text_to_video():  
    lines = [ln.strip() for ln in (prompts_text or "").splitlines() if ln.strip()]  
    if not lines:  
        st.error("Isi minimal 1 baris prompt.")  
        return  
    cfg = build_video_config(aspect, resolution, neg, seed, person_generation)  
    progress_all = st.progress(0)  
    for i, p in enumerate(lines, start=1):  
        block = st.container()  
        with block:  
            st.markdown(f"#### 🎬 Job {i}")  
            st.code(p)  
            pbar = st.progress(0, text="Menyiapkan…")  
  
        try:  
            op, model_used = generate_with_fallback(model_label, p, cfg, image=None)  
        except Exception as e:  
            with block:  
                st.error(f"Gagal mulai generate: {e}")  
            progress_all.progress(int(i/len(lines)*100))  
            continue  
  
        ticks = 0  
        try:  
            while not getattr(op, "done", False):  
                time.sleep(5)  
                ticks += 1  
                op = client.operations.get(op)  
                pbar.progress(min(100, ticks * 6), text="Rendering…")  
  
            resp = getattr(op, "response", None)  
            vids = getattr(resp, "generated_videos", []) if resp else []  
            if not vids:  
                with block:  
                    st.error("Response tidak berisi video.")  
            else:  
                vid = vids[0]  
                fname = f"text2video_{i:02d}.mp4"  
                data = download_video_file(vid.video, fname)  
                with block:  
                    st.video(data)  
                    st.caption(f"Model: {model_used}")  
                    st.download_button("⬇️ Download MP4", data=data, file_name=fname, mime="video/mp4")  
        except Exception as e:  
            with block:  
                st.error(f"Error saat proses/polling/unduh: {e}")  
  
        progress_all.progress(int(i/len(lines)*100))  
  
def run_image_to_video():  
    imgs = uploaded_images or []  
    if not imgs:  
        st.error("Upload minimal 1 gambar.")  
        return  
    prompt_lines: List[str] = [ln.strip() for ln in (prompts_text or "").splitlines() if ln.strip()]  
    cfg = build_video_config(aspect, resolution, neg, seed, person_generation)  
    progress_all = st.progress(0)  
    total = len(imgs)  
    for i, up in enumerate(imgs, start=1):  
        p = ""  
        if len(prompt_lines) == 1:  
            p = prompt_lines[0]  
        elif len(prompt_lines) >= i:  
            p = prompt_lines[i-1]  
        elif len(prompt_lines) > 1:  
            p = prompt_lines[-1]  
  
        block = st.container()  
        with block:  
            st.markdown(f"#### 🎬 (Image→Video) Job {i}/{total}")  
            st.image(up, width=280)  
            if p:  
                st.code(p)  
            pbar = st.progress(0, text="Menyiapkan…")  
  
        image_payload = to_image_payload(up)  
  
        try:  
            op, model_used = generate_with_fallback(model_label, p, cfg, image=image_payload)  
        except Exception as e:  
            with block:  
                st.error(f"Gagal mulai generate: {e}")  
            progress_all.progress(int(i/total*100))  
            continue  
  
        ticks = 0  
        try:  
            while not getattr(op, "done", False):  
                time.sleep(5)  
                ticks += 1  
                op = client.operations.get(op)  
                pbar.progress(min(100, ticks * 6), text="Rendering…")  
  
            resp = getattr(op, "response", None)  
            vids = getattr(resp, "generated_videos", []) if resp else []  
            if not vids:  
                with block:  
                    st.error("Response tidak berisi video.")  
            else:  
                vid = vids[0]  
                fname = f"image2video_{i:02d}.mp4"  
                data = download_video_file(vid.video, fname)  
                with block:  
                    st.video(data)  
                    st.caption(f"Model: {model_used}")  
                    st.download_button("⬇️ Download MP4", data=data, file_name=fname, mime="video/mp4")  
        except Exception as e:  
            with block:  
                st.error(f"Error saat proses/polling/unduh: {e}")  
  
        progress_all.progress(int(i/total*100))  
  
# ================== TRIGGERS ==================  
if btn_text:  
    run_text_to_video()  
if btn_image:  
    run_image_to_video()
