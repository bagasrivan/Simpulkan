"""Komponen tampilan Streamlit: CSS, header, kartu sumber, format jawaban."""

import html
import re
from pathlib import Path

import streamlit as st

import config


def load_css():
    css = (Path(__file__).parent / "styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_header():
    st.markdown(
        f'<div class="wordmark">{config.APP_NAME}</div>'
        f'<p class="tagline">{config.TAGLINE}</p>',
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        '<div class="hero"><h2>Yuk, unggah Dokumen-mu!</h2>',
    )


def render_docbar(file_name, n_pages, n_chunks):
    st.markdown(
        f'<div class="docbar"><span>📄</span>'
        f"<b>{html.escape(file_name)}</b>"
        f'<span class="meta">{n_pages} halaman</span>'
        f'<span class="meta">{n_chunks} potongan teks</span></div>',
        unsafe_allow_html=True,
    )


def fmt_answer(text):
    """Escape HTML dari model/PDF, lalu ubah [n] jadi penanda stabilo."""
    safe = html.escape(text, quote=False)
    return re.sub(r"\[(\d+)\]", r'<span class="cite">\1</span>', safe)


def render_sources(sources, answer):
    """Tampilkan hanya sumber yang dikutip; kalau tidak ada, tampilkan semua."""
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
    shown = [s for s in sources if s["id"] in cited] or sources
    cards = "".join(
        f'<div class="src"><div class="src-h"><span class="cite">{s["id"]}</span>'
        f'Halaman {s["page"]}</div>'
        f'<div class="src-t"><span class="hl">'
        f'{html.escape(" ".join(s["text"].split()))}</span></div></div>'
        for s in shown
    )
    with st.expander(f"Lihat sumber ({len(shown)})"):
        st.markdown(cards, unsafe_allow_html=True)