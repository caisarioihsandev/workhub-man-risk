# Workhub Manajemen Risiko — Flask/Jinja

Implementasi Workhub menggunakan Python, Flask, Jinja, dan SQLite.

## Menjalankan secara lokal

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app init-db
flask --app app run --debug
```

Buka `http://127.0.0.1:5000`.

## Fitur

- dashboard indikator otomatis;
- tambah, filter, perbarui, dan hapus pekerjaan;
- kategori monitoring perusahaan/divisi/cabang/unit, kajian risiko, dan AOI RMI;
- status, progres, PIC, tim, prioritas, dan tenggat;
- tautan dokumen Google Drive; dan
- disposisi melalui aplikasi email pengguna.

## Catatan keamanan

Proyek tidak menyediakan login email palsu. Untuk penggunaan internet/produksi, tambahkan autentikasi yang tervalidasi seperti Google OAuth/OIDC, batasi akun berdasarkan domain atau allowlist, gunakan HTTPS, ganti `SECRET_KEY`, nonaktifkan debug, dan gunakan database terkelola. Jangan memakai Flask development server untuk produksi.

## Menjalankan dengan Gunicorn

```bash
gunicorn -w 2 -b 0.0.0.0:8000 app:app
```
