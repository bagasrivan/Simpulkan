"""Simpulkan: titik masuk aplikasi. Hanya alur halaman; logika ada di modul lain."""

import os

import streamlit as st
from dotenv import load_dotenv

import config
import ui
from rag import PDFLimitError, build_vectorstore, generate_answer, retrieve

load_dotenv()  # baca GOOGLE_API_KEY dari file .env (kalau ada)


def get_server_key():
    """API key milik server: dari environment/.env, atau Streamlit Secrets."""
    key = os.getenv("GOOGLE_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GOOGLE_API_KEY")
    except Exception:  # tidak ada file secrets
        return None


st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="📖",
    initial_sidebar_state="expanded",
)
ui.load_css()
ui.render_header()

SERVER_KEY = get_server_key()
limited = bool(SERVER_KEY)  # batas pemakaian hanya jika memakai key server

has_doc = "vectorstore" in st.session_state
st.session_state.setdefault("question_count", 0)

# ---------- Sidebar ----------
with st.sidebar:
    uploaded = None
    if has_doc:
        st.subheader("Dokumen")
        uploaded = st.file_uploader(
            "Ganti dokumen", type="pdf", key="up_side", label_visibility="collapsed"
        )
    st.subheader("Pengaturan")
    if SERVER_KEY:
        api_key = SERVER_KEY  # tidak pernah ditampilkan ke browser
    else:
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Ambil gratis di https://aistudio.google.com/apikey",
        )
    with st.expander("Pengaturan lanjutan"):
        tip = config.SETTINGS_HELP
        chat_model = st.text_input(
            "Model chat", value=config.DEFAULT_CHAT_MODEL, help=tip["chat_model"]
        )
        embed_model = st.text_input(
            "Model embedding", value=config.DEFAULT_EMBED_MODEL, help=tip["embed_model"]
        )
        chunk_size = st.slider(
            "Ukuran potongan teks",
            300,
            2000,
            config.DEFAULT_CHUNK_SIZE,
            100,
            help=tip["chunk_size"],
        )
        # Overlap tidak boleh >= ukuran potongan, jadi batasnya ikut ukuran potongan.
        max_overlap = min(400, (chunk_size // 2) // 50 * 50)
        chunk_overlap = st.slider(
            "Tumpang tindih potongan",
            0,
            max_overlap,
            min(config.DEFAULT_CHUNK_OVERLAP, max_overlap),
            50,
            help=tip["chunk_overlap"],
        )
        top_k = st.slider(
            "Jumlah potongan yang diambil",
            1,
            8,
            config.DEFAULT_TOP_K,
            help=tip["top_k"],
        )

if not api_key:
    st.info("Masukkan Gemini API Key di sidebar untuk mulai.")
    st.stop()

# ---------- Halaman awal & upload ----------
if not has_doc:
    ui.render_hero()
    uploaded = st.file_uploader(
        "Pilih atau seret file PDF",
        type="pdf",
        key="up_main",
        label_visibility="collapsed",
    )

if uploaded and st.session_state.get("file_name") != uploaded.name:
    if limited and uploaded.size > config.MAX_PDF_MB * 1024 * 1024:
        st.error(
            f"File terlalu besar. Batasnya {config.MAX_PDF_MB} MB. "
            "Coba kompres PDF atau unggah sebagian halamannya saja."
        )
        st.stop()
    with st.spinner("Membaca dan mengindeks PDF..."):
        try:
            vs, n_pages, n_chunks = build_vectorstore(
                uploaded.getvalue(),
                api_key,
                embed_model,
                chunk_size,
                chunk_overlap,
                max_pages=config.MAX_PDF_PAGES if limited else None,
            )
        except PDFLimitError as e:
            st.error(f"{e} Coba unggah sebagian halamannya saja.")
            st.stop()
        except Exception as e:
            st.error(
                f"PDF tidak bisa diproses: {e}. Pastikan file tidak terkunci "
                "dan bukan hasil scan berupa gambar, lalu coba lagi."
            )
            st.stop()
    st.session_state.vectorstore = vs
    st.session_state.file_name = uploaded.name
    st.session_state.doc_info = (n_pages, n_chunks)
    st.session_state.messages = []
    st.rerun()

if "vectorstore" not in st.session_state:
    st.stop()

ui.render_docbar(st.session_state.file_name, *st.session_state.doc_info)

# ---------- Chat ----------
reached_limit = limited and (
    st.session_state.question_count >= config.MAX_QUESTIONS_PER_SESSION
)
pending = st.session_state.pop("pending_q", None)
if reached_limit:
    pending = None


def set_pending(q):
    st.session_state.pending_q = q


if not st.session_state.messages and not pending and not reached_limit:
    st.markdown('<p class="hint">Coba tanyakan:</p>', unsafe_allow_html=True)
    for i, s in enumerate(config.SUGGESTIONS):
        st.button(s, key=f"sug_{i}", on_click=set_pending, args=(s,))

for m in st.session_state.messages:
    avatar = "🙋" if m["role"] == "user" else "📖"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(ui.fmt_answer(m["content"]), unsafe_allow_html=True)
        if m.get("sources"):
            ui.render_sources(m["sources"], m["content"])

if reached_limit:
    st.info(
        f"Batas {config.MAX_QUESTIONS_PER_SESSION} pertanyaan per sesi sudah tercapai. "
        "Muat ulang halaman untuk memulai sesi baru."
    )

question = (
    st.chat_input("Tanya sesuatu tentang isi PDF...", disabled=reached_limit)
    or pending
)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🙋"):
        st.markdown(ui.fmt_answer(question), unsafe_allow_html=True)

    with st.chat_message("assistant", avatar="📖"):
        try:
            with st.spinner("Mencari di dokumen..."):
                sources = retrieve(st.session_state.vectorstore, question, top_k)
                answer = generate_answer(question, sources, api_key, chat_model)
        except Exception as e:
            st.error(
                f"Gagal mendapat jawaban: {e}. Coba lagi sebentar lagi. Kalau "
                "terus gagal, cek nama model di Pengaturan lanjutan."
            )
            st.session_state.messages.pop()
            st.stop()
        st.markdown(ui.fmt_answer(answer), unsafe_allow_html=True)
        ui.render_sources(sources, answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
    st.session_state.question_count += 1