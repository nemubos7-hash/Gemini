import io
import time
import base64
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Gemini Playground — AI Studio Style", layout="wide")

# ----------------- Styles (AI Studio–ish) -----------------
st.markdown('''
<style>
:root {
  --card-bg: #0f1115;
  --border: #23262d;
}
/* Make it feel like a tidy IDE/playground */
.block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1200px;}
.sidebar .sidebar-content {background: var(--card-bg);}
/* Cards */
.card {border:1px solid var(--border); border-radius:16px; padding:16px; background:#0b0d11;}
.card-title {font-weight:700; font-size:1rem; opacity:.9; margin-bottom:.5rem;}
/* Prompt textarea */
textarea {font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;}
/* Tiny badge */
.badge {display:inline-block; border:1px solid var(--border); padding:2px 8px; border-radius:999px; font-size:.75rem; opacity:.8;}
/* Copy btn mimic */
.copy {cursor:pointer; border:1px solid var(--border); padding:4px 10px; border-radius:8px; font-size:.8rem;}
/* Tabs looks a bit tighter */
.stTabs [data-baseweb="tab-list"] {gap:.5rem;}
/* Tables monospace */
code, pre {font-size: .85rem;}
</style>
''', unsafe_allow_html=True)

# ----------------- Sidebar -----------------
with st.sidebar:
    st.header("🔑 API & Model")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AI...")
    model = st.selectbox("Model", ["gemini-1.5-flash", "gemini-1.5-pro"], index=0)
    st.markdown("---")

    st.subheader("⚙️ Generation Config")
    temperature = st.slider("temperature", 0.0, 2.0, 0.9, 0.1, help="Kontrol kreativitas")
    top_p = st.slider("top_p", 0.0, 1.0, 0.95, 0.05)
    top_k = st.slider("top_k", 0, 100, 40, 1)
    max_tokens = st.slider("max_output_tokens", 64, 4096, 1024, 64)
    st.markdown("---")

    st.subheader("🧭 System Instruction (opsional)")
    system_instruction = st.text_area(
        "Arahan sistem",
        value="Kamu adalah asisten yang ringkas, jelas, dan membantu.",
        height=90
    )
    st.markdown("---")
    if st.button("🔁 Reset Sesi"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []  # list of dicts: {"role": "user"/"model", "content": "..."}
if "attachments" not in st.session_state:
    st.session_state.attachments = []  # list of (bytes, mime)

st.title("⚗️ Gemini Playground (AI Studio–like)")

# ----------------- Tabs -----------------
tab_play, tab_json = st.tabs(["🧪 Playground", "📦 Request/Response"])

with tab_play:
    colL, colR = st.columns([7,5], gap="large")

    with colL:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Prompt</div>', unsafe_allow_html=True)
        user_prompt = st.text_area(" ", placeholder="Tulis prompt kamu di sini...", label_visibility="collapsed", height=180)

        att_col1, att_col2 = st.columns([1,3])
        with att_col1:
            add_img = st.checkbox("➕ Tambah gambar", value=False)
        img_bytes = None
        mime_override = ""
        if add_img:
            up = st.file_uploader("Upload gambar (opsional)", type=["png","jpg","jpeg","webp"])
            mime_override = st.text_input("MIME override (opsional)", placeholder="image/png")
            if up is not None:
                img_bytes = up.read()
                st.image(io.BytesIO(img_bytes), caption="Attachment", use_container_width=True)

        colA, colB = st.columns([1,1])
        with colA:
            run_btn = st.button("▶️ Jalankan", type="primary")
        with colB:
            clear_btn = st.button("🧹 Bersihkan Chat")
            if clear_btn:
                st.session_state.messages = []
                st.session_state.attachments = []

        st.markdown("</div>", unsafe_allow_html=True)

        if run_btn:
            if not api_key:
                st.warning("Masukkan API key di sidebar.", icon="🔐")
            elif not user_prompt and img_bytes is None:
                st.info("Isi prompt atau tambahkan gambar terlebih dahulu.", icon="📝")
            else:
                try:
                    client = genai.Client(api_key=api_key)
                    parts = []
                    if img_bytes is not None:
                        mime = mime_override.strip() or "image/png"
                        parts.append(types.Part.from_bytes(img_bytes, mime_type=mime))
                    if user_prompt.strip():
                        parts.append(types.Part.from_text(user_prompt))

                    config = types.GenerateContentConfig(
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k,
                        max_output_tokens=max_tokens,
                        system_instruction=system_instruction or None
                    )

                    resp = client.models.generate_content(
                        model=model,
                        contents=parts if parts else [types.Part.from_text(user_prompt)],
                        config=config
                    )

                    # Save turn
                    st.session_state.messages.append({"role": "user", "content": user_prompt})
                    if img_bytes:
                        st.session_state.attachments.append({"mime": mime_override.strip() or "image/png", "size": len(img_bytes)})
                    st.session_state.messages.append({"role": "model", "content": resp.text or ""})
                    st.session_state.last_response = getattr(resp, "raw", None) or getattr(resp, "candidates", None)

                except Exception as e:
                    st.error(f"Error: {e}")

        # Render conversation
        if st.session_state.messages:
            st.markdown("### Riwayat")
            for i, m in enumerate(st.session_state.messages):
                who = "👤" if m["role"] == "user" else "🤖"
                st.markdown(f"**{who} {m['role'].capitalize()}**")
                st.markdown(m["content"] or "_(kosong)_")
                st.markdown("---")

    with colR:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Hasil Terakhir</div>', unsafe_allow_html=True)
        last = None
        for m in reversed(st.session_state.messages):
            if m["role"] == "model":
                last = m["content"]
                break
        if last:
            st.markdown(last)
            if st.button("📋 Copy Hasil"):
                st.toast("Disalin ke clipboard (Ctrl/Cmd+C di area terpilih).")
        else:
            st.caption("Belum ada output.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab_json:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Request Preview</div>', unsafe_allow_html=True)
    preview = {
        "model": model,
        "config": {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": max_tokens,
            "system_instruction": (system_instruction[:120] + "…") if system_instruction else None,
        },
        "attachments_count": len(st.session_state.attachments),
        "turns": [{"role": m["role"], "content_len": len(m["content"])} for m in st.session_state.messages]
    }
    st.code(preview, language="json")

    st.markdown("---")
    st.markdown('<div class="card-title">Response Object (mentah)</div>', unsafe_allow_html=True)
    raw = st.session_state.get("last_response", None)
    if raw is not None:
        # We don't know exact python type – just render repr to give raw feel
        st.code(repr(raw)[:10000])
    else:
        st.caption("Belum ada response mentah untuk ditampilkan.")
    st.markdown("</div>", unsafe_allow_html=True)