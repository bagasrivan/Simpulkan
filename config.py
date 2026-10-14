"""Nilai default dan teks tetap. Ubah di sini, bukan di app.py."""

APP_NAME = "Simpulkan"
TAGLINE = "Tanya Dokumen-mu. Setiap jawaban ada sumber halamannya."

DEFAULT_CHAT_MODEL = "gemini-3.8-flash"
DEFAULT_EMBED_MODEL = "models/gemini-embedding-001"

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150
DEFAULT_TOP_K = 4

# Batas pemakaian. Hanya berlaku saat aplikasi memakai API key milik server,
# supaya kuota pemilik aplikasi tidak terkuras.
MAX_PDF_MB = 20
MAX_PDF_PAGES = 50
MAX_QUESTIONS_PER_SESSION = 30

SUGGESTIONS = [
    "Simpulkan isi dokumen ini dalam 5 poin",
    "Apa topik utama dokumen ini?",
    "Sebutkan istilah penting beserta artinya",
]

# Panduan singkat untuk tiap pengaturan lanjutan (ditampilkan di sidebar).
SETTINGS_HELP = {
    "chat_model": "Model Gemini yang menyusun jawaban. Ganti jika muncul error 'model not found'. Berlaku di pertanyaan berikutnya.",
    "embed_model": "Model pengubah teks jadi vektor untuk pencarian. Biarkan bawaan. Berlaku saat unggah PDF.",
    "chunk_size": "Panjang tiap potongan teks. Kecil: lebih tepat. Besar: konteks lebih utuh. Berlaku saat unggah PDF.",
    "chunk_overlap": "Karakter yang dibagi antar potongan agar kalimat tidak terputus. Idealnya 10-20% dari ukuran potongan. Berlaku saat unggah PDF.",
    "top_k": "Jumlah potongan teks sebagai bahan jawaban. Kecil: fokus. Besar: lebih lengkap tapi lebih lambat. Berlaku di pertanyaan berikutnya.",
}