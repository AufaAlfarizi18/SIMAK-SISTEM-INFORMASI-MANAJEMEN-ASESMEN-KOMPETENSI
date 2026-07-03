# SIMAK — Sistem Informasi Manajemen Asesmen Kompetensi

Web app sederhana berbasis **Python (Flask)** dengan penyimpanan data **JSON** (tanpa database).

## Fitur

| Kode | Fitur                              | Keterangan                                            |
|------|-------------------------------------|--------------------------------------------------------|
| A    | Autentikasi                         | Login/logout asesor, password ter-hash (Werkzeug)      |
| B    | Dashboard                           | Ringkasan statistik + jadwal terdekat                  |
| C    | Manajemen Data Peserta              | Tambah / ubah / hapus / cari peserta                    |
| D    | Jadwal Asesmen                      | Tambah / ubah / hapus jadwal, status terjadwal/selesai  |
| E    | Input Penilaian Kompetensi          | Form dinamis elemen & kriteria unjuk kerja, rekomendasi K/BK |
| F    | Rekap & Laporan Hasil               | Rekap keseluruhan + filter + detail cetak per peserta   |
| G    | Profil Asesor                       | Ubah biodata & ganti password                            |

## Struktur Folder

```
asesmen_app/
├── app.py                 # Backend Flask (semua route & logic)
├── requirements.txt
├── data/                  # "Database" berbasis JSON
│   ├── users.json         # Akun asesor
│   ├── peserta.json       # Data peserta
│   ├── jadwal.json        # Jadwal asesmen
│   └── penilaian.json     # Hasil penilaian kompetensi
├── templates/              # Halaman HTML (Jinja2)
└── static/
    └── style.css           # Tampilan/tema aplikasi
```

## Cara Menjalankan

1. Pastikan Python 3.9+ terpasang.
2. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi:
   ```bash
   python app.py
   ```
4. Buka browser ke: `http://localhost:5000`

## Akun Demo

- **Username:** `asesor1`
- **Password:** `asesor123`

Password ini otomatis dibuat (di-hash) saat aplikasi pertama kali dijalankan. Anda bisa menambah akun asesor lain langsung di `data/users.json`, atau menambahkan halaman registrasi jika diperlukan.

## Catatan Teknis

- Semua data disimpan sebagai file JSON di folder `data/` — cocok untuk skala kecil/demo. Untuk produksi/skala besar, sebaiknya migrasi ke database (SQLite/PostgreSQL).
- Ubah `app.secret_key` di `app.py` sebelum digunakan secara nyata.
- Fitur cetak laporan tersedia di halaman Detail Laporan (tombol "Cetak" akan memicu dialog print browser).
- Tidak ada dependensi frontend eksternal selain Google Fonts (CDN) — bisa dijalankan offline jika font dihapus/diganti font sistem.

## Pengembangan Lanjutan (opsional)

- Tambah role (admin vs asesor) untuk multi-pengguna.
- Ekspor laporan ke PDF/Excel.
- Upload bukti fisik/foto asesmen.
- Notifikasi email/WA untuk jadwal mendatang.
"# SIMAK-SISTEM-INFORMASI-MANAJEMEN-ASESMEN-KOMPETENSI" 
"# SIMAK-SISTEM-INFORMASI-MANAJEMEN-ASESMEN-KOMPETENSI" 
