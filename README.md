# 📖 Simpulkan

**Tanya PDF-mu. Setiap jawaban ada sumber halamannya.**

Simpulkan adalah chatbot dokumen berbasis RAG (Retrieval-Augmented Generation). Unggah satu file PDF, ajukan pertanyaan dalam bahasa Indonesia atau Inggris, dan dapatkan jawaban yang dilengkapi penanda sitasi `[1]`, `[2]` yang menunjuk ke halaman dan potongan teks asli di dokumen.

> Tambahkan screenshot aplikasi di sini, misalnya `docs/screenshot.png`:
>
> `![Tampilan Simpulkan](docs/screenshot.png)`

**Demo:** _tambahkan tautan Streamlit Community Cloud di sini setelah deploy_

## Fitur

- **Tanya-jawab dari isi PDF.** Jawaban hanya disusun dari potongan dokumen yang relevan.
- **Sitasi per jawaban.** Penanda `[n]` di teks mengarah ke kartu sumber berisi nomor halaman dan kutipan aslinya, sehingga jawaban bisa diverifikasi.
- **Jujur saat tidak tahu.** Prompt memerintahkan model menjawab "tidak ditemukan di dokumen" kalau informasinya memang tidak ada.
- **Saran pertanyaan awal.** Tiga tombol pertanyaan siap pakai untuk memulai.
- **Pengaturan lanjutan dengan tooltip.** Model, ukuran potongan teks, tumpang tindih, dan jumlah potongan yang diambil bisa diubah, masing-masing dengan penjelasan singkat.
- **API key aman di sisi server.** Pengguna tidak perlu memasukkan key sendiri, dan key tidak pernah dikirim ke browser.
- **Batas pemakaian.** Maksimal 20 MB, 50 halaman, dan 30 pertanyaan per sesi (hanya saat memakai key milik server).

## Cara kerja

```
PDF ──► PyPDFLoader ──► potongan teks ──► embedding Gemini ──► indeks FAISS
                                                                   │
pertanyaan ──► embedding ──► pencarian kemiripan (top-k) ◄─────────┘
                                   │
                                   ▼
        prompt (aturan + sumber bernomor + pertanyaan) ──► Gemini ──► jawaban + sitasi
```

1. **Load:** `PyPDFLoader` membaca PDF per halaman.
2. **Chunking:** `RecursiveCharacterTextSplitter` memotong teks dengan tumpang tindih.
3. **Embedding:** tiap potongan diubah menjadi vektor oleh model embedding Gemini.
4. **Vector DB:** vektor disimpan di FAISS (di memori, per sesi).
5. **Retrieval:** pertanyaan di-embed, lalu `k` potongan paling mirip diambil dan diberi nomor.
6. **Generation:** potongan bernomor dimasukkan ke prompt dengan aturan sitasi, lalu dikirim ke model chat Gemini.

## Teknologi

| Bagian | Pilihan |
|---|---|
| Antarmuka | Streamlit |
| Orkestrasi RAG | LangChain |
| Model | Gemini API (chat dan embedding) |
| Vector store | FAISS (`faiss-cpu`) |
| Pembaca PDF | pypdf |

## Struktur proyek

```
simpulkan/
├── app.py            alur halaman (upload, chat, sidebar)
├── config.py         nilai bawaan, batas pemakaian, teks bantuan
├── prompts.py        prompt untuk LLM
├── rag.py            indexing, retrieval, dan generasi jawaban
├── ui.py             komponen tampilan (header, kartu sumber, format sitasi)
├── styles.css        seluruh CSS
├── requirements.txt
└── .streamlit/
    └── config.toml   tema Streamlit
```

`rag.py` tidak berisi kode Streamlit, jadi fungsinya bisa diuji atau dipakai ulang di luar aplikasi.

## Menjalankan di komputer sendiri

**Prasyarat:** Python 3.10 atau lebih baru dan Gemini API key (gratis di [Google AI Studio](https://aistudio.google.com/apikey)).

```bash
# 1. Masuk ke folder proyek
cd simpulkan

# 2. Buat dan aktifkan virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Pasang dependensi
pip install -r requirements.txt

# 4. Siapkan API key
cp .env.example .env            # lalu isi GOOGLE_API_KEY di file .env

# 5. Jalankan
streamlit run app.py
```

Aplikasi terbuka di `http://localhost:8501`.

Isi `.env`, satu baris tanpa tanda kutip dan tanpa spasi di sekitar `=`:

```
GOOGLE_API_KEY=isi_api_key_kamu_di_sini
```

> **Jangan commit `.env` ke repositori.** File itu sudah masuk `.gitignore`. Jika key terlanjur bocor, hapus dan buat key baru.

Jika `GOOGLE_API_KEY` tidak ditemukan, kolom input key akan muncul di sidebar sebagai cadangan.

## Deploy ke Streamlit Community Cloud

1. Push proyek ke GitHub (tanpa `.env`).
2. Di [share.streamlit.io](https://share.streamlit.io), pilih repositori dan file utama `app.py`.
3. Di **Advanced settings → Secrets**, isi:
   ```toml
   GOOGLE_API_KEY = "api-key-kamu"
   ```
4. Deploy.

Pasang batas kuota di akun Google AI Studio supaya key tidak terkuras jika tautan dibagikan luas.

## Konfigurasi

Semua nilai bawaan ada di `config.py`:

| Pengaturan | Bawaan | Keterangan |
|---|---|---|
| `DEFAULT_CHAT_MODEL` | `gemini-3.8-flash` | Model penyusun jawaban |
| `DEFAULT_EMBED_MODEL` | `models/gemini-embedding-001` | Model embedding |
| `DEFAULT_CHUNK_SIZE` | 1000 | Panjang potongan teks (karakter) |
| `DEFAULT_CHUNK_OVERLAP` | 150 | Tumpang tindih antar potongan |
| `DEFAULT_TOP_K` | 4 | Jumlah potongan yang diambil |
| `MAX_PDF_MB` | 10 | Batas ukuran file (key server) |
| `MAX_PDF_PAGES` | 50 | Batas jumlah halaman (key server) |
| `MAX_QUESTIONS_PER_SESSION` | 30 | Batas pertanyaan per sesi (key server) |

Nama model Gemini bisa berubah seiring waktu. Jika muncul error "model not found", ganti nama model di **Pengaturan lanjutan** atau di `config.py` sesuai daftar terbaru di Google AI Studio.

Untuk mengubah perilaku bot, misalnya gaya jawaban atau aturan sitasi, edit `prompts.py`.

## Batasan yang perlu diketahui

- **PDF hasil scan (gambar) tidak terbaca.** Belum ada OCR.
- **Satu dokumen per sesi.** Mengunggah dokumen baru menggantikan yang lama.
- **Indeks tidak disimpan.** FAISS berjalan di memori, jadi dokumen perlu diproses ulang setiap sesi baru.
- **Pertanyaan yang meminta ringkasan seluruh dokumen** hanya melihat beberapa potongan teratas, sehingga hasilnya bisa tidak lengkap.
- **Batas pertanyaan bersifat ringan.** Memuat ulang halaman membuka sesi baru.
- **Privasi.** Isi dokumen dikirim ke layanan Gemini (Google). Jangan unggah dokumen rahasia.
- Kualitas jawaban bergantung pada kualitas teks PDF dan pada model. Selalu periksa kartu sumber untuk hal yang penting.

## Rencana pengembangan

- [ ] Penolakan otomatis saat skor kemiripan rendah, agar bot tidak mengarang
- [ ] Simpan indeks FAISS ke disk
- [ ] Dukungan beberapa PDF sekaligus
- [ ] Memori percakapan untuk pertanyaan lanjutan
- [ ] Evaluasi retrieval dengan set tanya-jawab kecil
- [ ] OCR untuk PDF hasil scan

## Lisensi
---

Dibuat oleh Bagaskara Ridho Vandio.