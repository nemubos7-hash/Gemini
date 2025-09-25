import io
import time
import base64
import json
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Gemini Playground — AI Studio Style (Plus)", layout="wide")

# ----------------- Styles -----------------
st.markdown('''
<style>
:root {
  --card-bg: #0f1115;
  --border: #23262d;
}
.block-container {padding-top: 1.2rem; padding-bottom: 2.2rem; max-width: 1280px;}
.card {border:1px solid var(--border); border-radius:16px; padding:16px; background:#0b0d11; margin-bottom: 14px;}
.card-title {font-weight:700; font-size:1rem; opacity:.9; margin-bottom:.4rem;}
.small {opacity:.7; font-size:.85rem;}
pre, code, textarea {font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;}
.badge {display:inline-block; border:1px solid var(--border); padding:2px 8px; border-radius:999px; font-size:.75rem; opacity:.8;}
</style>
''', unsafe_allow_html=True)

# ----------------- Sidebar -----------------
with st.sidebar:
    st.header("🔑 API & Model")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AI...")
    base_model = st.selectbox("Text/Vision Model", ["gemini-1.5-flash", "gemini-1.5-pro"], index=0)
    st.markdown("---")
    st.subheader("🧭 System Instruction (opsional)")
    system_instruction = st.text_area("Arahan sistem", value="Kamu adalah asisten yang ringkas, jelas, dan membantu.", height=80)
    st.markdown("---")
    st.caption("Video generation memerlukan endpoint khusus (mis. Veo). App ini menyediakan antrean & export, dan akan mencoba panggilan jika endpoint tersedia di SDK.")

if not api_key:
    st.info("Masukkan API key di sidebar untuk mulai.", icon="🔐")
    st.stop()

client = genai.Client(api_key=api_key)

# Session states
if "video_jobs" not in st.session_state:
    st.session_state.video_jobs = []   # list of dicts
if "ivideo_jobs" not in st.session_state:
    st.session_state.ivideo_jobs = []  # image-to-video jobs
if "img_gen" not in st.session_state:
    st.session_state.img_gen = []      # list of generated images (bytes)

st.title("⚗️ Gemini Playground (AI Studio–like) — Plus")

tab_chat, tab_t2v, tab_i2v, tab_img, tab_jobs = st.tabs([
    "🧪 Chat/Vision",
    "🎬 Text → Video (multi)",
    "🖼️ Image → Video (multi)",
    "🖌️ Generate Image (Gemini 2.5 Flash Image)",
    "📦 Jobs / Export",
])

# ----------------- Chat/Vision -----------------
with tab_chat:
    colL, colR = st.columns([7,5], gap="large")
    with colL:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Prompt</div>', unsafe_allow_html=True)
        user_prompt = st.text_area(" ", placeholder="Tulis prompt kamu di sini...", label_visibility="collapsed", height=160)

        add_img = st.checkbox("➕ Tambah gambar (Vision)", value=False)
        img_bytes = None
        mime_override = ""
        if add_img:
            up = st.file_uploader("Upload gambar (opsional)", type=["png","jpg","jpeg","webp"])
            mime_override = st.text_input("MIME override (opsional)", placeholder="image/png")
            if up is not None:
                img_bytes = up.read()
                st.image(io.BytesIO(img_bytes), caption="Attachment", use_container_width=True)

        colA, colB = st.columns(2)
        with colA:
            temperature = st.slider("temperature", 0.0, 2.0, 0.9, 0.1)
        with colB:
            max_tokens = st.slider("max_output_tokens", 64, 4096, 1024, 64)

        if st.button("▶️ Jalankan", type="primary"):
            try:
                parts = []
                if img_bytes is not None:
                    mime = mime_override.strip() or "image/png"
                    parts.append(types.Part.from_bytes(img_bytes, mime_type=mime))
                if user_prompt.strip():
                    parts.append(types.Part.from_text(user_prompt))

                config = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    system_instruction=system_instruction or None,
                )
                resp = client.models.generate_content(model=base_model, contents=parts or [types.Part.from_text(user_prompt)], config=config)
                st.success("Sukses")
                st.markdown(resp.text or "_(kosong)_")
            except Exception as e:
                st.error(f"Error: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    with colR:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Tips</div>', unsafe_allow_html=True)
        st.write("- Gunakan Vision untuk analisis gambar.\n- Prompt panjang → pertimbangkan `max_output_tokens` lebih besar.\n- Atur `temperature` untuk kreativitas.")
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------- Text → Video (multi) -----------------
with tab_t2v:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Multi Prompt — Text → Video</div>', unsafe_allow_html=True)
    st.caption("Satu baris = satu video job. Pilih rasio 9:16 untuk vertical.")
    mp = st.text_area("Daftar prompt (1 baris = 1 video)", height=180, placeholder="Contoh:\nKucing oren menari di taman saat matahari terbenam, gaya cinematic\nKapibara mandi busa di bathtub modern, close-up ekspresi rileks")
    col1, col2, col3 = st.columns([2,2,2])
    with col1:
        ratio = st.selectbox("Aspect Ratio", ["16:9","9:16","1:1","4:3"], index=1)
    with col2:
        duration = st.slider("Durasi (detik)", 2, 60, 8, 1)
    with col3:
        seed = st.number_input("Seed (opsional)", min_value=0, value=0, step=1, help="Seed menstabilkan random sehingga hasil lebih konsisten.")
    mode = st.radio("Kualitas (opsional, tergantung endpoint)", ["preview","fast","quality"], index=0, horizontal=True)

    colA, colB = st.columns([1,1])
    with colA:
        if st.button("➕ Tambah ke Antrean"):
            lines = [x.strip() for x in mp.split("\n") if x.strip()]
            if not lines:
                st.warning("Isi minimal satu prompt.")
            else:
                for line in lines:
                    st.session_state.video_jobs.append({
                        "type": "text-to-video",
                        "prompt": line,
                        "ratio": ratio,
                        "duration": duration,
                        "seed": seed if seed>0 else None,
                        "mode": mode,
                        "status": "queued",
                        "result": None,
                    })
                st.success(f"Ditambahkan {len(lines)} job.")
    with colB:
        if st.button("▶️ Coba Jalankan Sekarang"):
            ran = 0
            for job in st.session_state.video_jobs:
                if job["status"] == "queued" and job["type"] == "text-to-video":
                    job["status"] = "running"
                    try:
                        # Placeholder for Veo/Vertex call
                        time.sleep(0.1)
                        job["result"] = {"message": "Video generation requires Veo/Vertex endpoints. Job prepared.", "ratio": job["ratio"]}
                        job["status"] = "done"
                    except Exception as e:
                        job["status"] = f"error: {e}"
                    ran += 1
            st.info(f"Dieksekusi {ran} job (simulasi).")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.video_jobs:
        st.markdown("#### Antrean Text→Video")
        for i, j in enumerate(st.session_state.video_jobs):
            if j["type"] != "text-to-video": continue
            st.write(f"**#{i+1}** [{j['status']}] — {j['prompt']}  \n*ratio:* {j['ratio']}, *durasi:* {j['duration']}s, *mode:* {j['mode']}, *seed:* {j.get('seed','-')}")
            if j["result"]:
                st.code(json.dumps(j["result"], ensure_ascii=False, indent=2), language="json")
        st.divider()

# ----------------- Image → Video (multi) -----------------
with tab_i2v:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Multi Prompt — Image → Video</div>', unsafe_allow_html=True)
    st.caption("Upload beberapa gambar dan masukkan daftar prompt (1 baris per gambar, urut sesuai daftar file).")
    files = st.file_uploader("Upload gambar (bisa banyak)", type=["png","jpg","jpeg","webp"], accept_multiple_files=True)
    prompts = st.text_area("Daftar prompt (1 baris/gambar)", height=140, placeholder="Baris 1 untuk gambar 1, baris 2 untuk gambar 2, dst.")
    col1, col2, col3 = st.columns([2,2,2])
    with col1:
        ratio2 = st.selectbox("Aspect Ratio", ["16:9","9:16","1:1","4:3"], index=1, key="ratio2")
    with col2:
        duration2 = st.slider("Durasi (detik)", 2, 60, 8, 1, key="dur2")
    with col3:
        seed2 = st.number_input("Seed (opsional)", min_value=0, value=0, step=1, key="seed2")

    if st.button("➕ Tambah ke Antrean (Image→Video)"):
        lines = [x.strip() for x in prompts.split("\n") if x.strip()]
        if not files:
            st.warning("Upload minimal satu gambar.")
        elif len(lines) and len(lines) != len(files):
            st.warning("Jumlah baris prompt harus sama dengan jumlah gambar (atau kosongkan prompt untuk default).")
        else:
            count = 0
            for idx, f in enumerate(files):
                prompt_line = lines[idx] if len(lines) else ""
                content = f.read()
                st.session_state.ivideo_jobs.append({
                    "type": "image-to-video",
                    "filename": f.name,
                    "image_bytes": content,
                    "prompt": prompt_line,
                    "ratio": ratio2,
                    "duration": duration2,
                    "seed": seed2 if seed2>0 else None,
                    "mode": "preview",
                    "status": "queued",
                    "result": None,
                })
                count += 1
            st.success(f"Ditambahkan {count} job.")
    if st.button("▶️ Coba Jalankan Sekarang (Image→Video)"):
        ran = 0
        for job in st.session_state.ivideo_jobs:
            if job["status"] == "queued" and job["type"] == "image-to-video":
                job["status"] = "running"
                try:
                    time.sleep(0.1)
                    job["result"] = {"message": "Image→Video memerlukan Veo/Vertex endpoints. Job prepared.", "ratio": job["ratio"]}
                    job["status"] = "done"
                except Exception as e:
                    job["status"] = f"error: {e}"
                ran += 1
        st.info(f"Dieksekusi {ran} job (simulasi).")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.ivideo_jobs:
        st.markdown("#### Antrean Image→Video")
        for i, j in enumerate(st.session_state.ivideo_jobs):
            if j["type"] != "image-to-video": continue
            st.write(f"**#{i+1}** [{j['status']}] — {j['filename']}  \n*prompt:* {j['prompt'] or '(default)'}  \n*ratio:* {j['ratio']}, *durasi:* {j['duration']}s, *seed:* {j.get('seed','-')}")
            if j["result"]:
                st.code(json.dumps(j["result"], ensure_ascii=False, indent=2), language="json")
        st.divider()

# ----------------- Generate Image (Gemini 2.5 Flash Image) -----------------
with tab_img:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Text → Image (Gemini 2.5 Flash Image)</div>', unsafe_allow_html=True)
    st.caption("Mencoba generate gambar. Tergantung ketersediaan model & quota akun.")
    prompt_img = st.text_area("Prompt gambar", value="An ultra-detailed adorable orange tabby cat wearing a red scarf, cinematic lighting, 8k look.", height=120)
    col1, col2 = st.columns(2)
    with col1:
        ar = st.selectbox("Aspect Ratio", ["1:1","16:9","9:16","4:3","3:4"], index=2)
    with col2:
        img_count = st.slider("Jumlah gambar", 1, 4, 1, 1)
    if st.button("🎨 Generate Image"):
        try:
            model_candidates = [
                "gemini-2.5-flash",
                "gemini-2.5-flash-image",
                "imagen-3.0-fast",
                "imagen-3.0",
            ]
            got = False
            last_err = None
            for mid in model_candidates:
                try:
                    cfg = types.GenerateContentConfig()
                    hint = f"(aspect ratio: {ar})"
                    resp = client.models.generate_content(model=mid, contents=f"{hint}\n{prompt_img}", config=cfg)
                    # Depending on SDK version, images may be streamed/returned differently.
                    # Here we simply show text if no binary media is included.
                    if hasattr(resp, "media") and resp.media:
                        shown = 0
                        for m in resp.media:
                            if getattr(m, "mime_type", "").startswith("image/"):
                                st.image(io.BytesIO(m.data), caption=f"{mid}", use_container_width=True)
                                shown += 1
                                if shown >= img_count:
                                    break
                        if shown > 0:
                            got = True
                            break
                    st.warning(f"Model {mid} membalas teks. Coba model lain...")
                except Exception as e:
                    last_err = e
                    continue
            if not got:
                if last_err:
                    st.error(f"Gagal generate image: {last_err}")
                else:
                    st.error("Tidak ada gambar yang dihasilkan. Pastikan model image generation aktif di akunmu (Imagen/Vision features).")
        except Exception as e:
            st.error(f"Error: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- Jobs / Export -----------------
with tab_jobs:
    st.markdown("### Export Antrean ke JSON")
    all_jobs = {
        "text_to_video": st.session_state.video_jobs,
        "image_to_video": [
            {k: (v if k != "image_bytes" else f"<{len(v)} bytes>") for k, v in j.items()}
            for j in st.session_state.ivideo_jobs
        ]
    }
    data = json.dumps(all_jobs, ensure_ascii=False, indent=2)
    st.code(data, language="json")
    st.download_button("💾 Download jobs.json", data=data.encode("utf-8"), file_name="jobs.json", mime="application/json")