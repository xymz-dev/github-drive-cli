# GHUP (GitHub Uploader) for Termux 🚀

**GHUP** adalah aplikasi CLI (Command Line Interface) berbasis Python 3 yang dirancang khusus untuk **Termux** (Android) serta lingkungan Linux. Aplikasi ini memungkinkan pengguna untuk mengunggah, mengunduh, dan mengelola file maupun folder di repository GitHub secara langsung melalui terminal menggunakan **GitHub REST API** dan **Personal Access Token (PAT)**, dengan antarmuka yang elegan berkat pustaka **Rich**.

---

## 📑 Daftar Isi
1. [Arsitektur & Penjelasan Modul](#1-arsitektur--penjelasan-modul)
2. [Cara Kerja Sistem (Workflow)](#2-cara-kerja-sistem-workflow)
3. [Panduan Instalasi Rinci di Termux](#3-panduan-instalasi-rinci-di-termux)
4. [Autentikasi & Login](#4-autentikasi--login)
5. [Daftar Lengkap Perintah (Commands & Help)](#5-daftar-lengkap-perintah-commands--help)
6. [Fitur Unggulan & Bonus](#6-fitur-unggulan--bonus)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Arsitektur & Penjelasan Modul

Struktur kode GHUP dirancang secara **modular** agar mudah dikembangkan (*maintainable* dan *extensible*):

- **`main.py`**: Berfungsi sebagai *entry point* utama aplikasi CLI. Menggunakan framework **Typer** untuk memparsing argumen dan opsi command line, serta memanggil modul sub-perintah yang sesuai.
- **`config.py`**: Mengelola konfigurasi lokal yang disimpan di `data/config.json`. Menyimpan token, active repository, branch default, retry count, timeout, dan preferensi tema. Dilindungi dengan izin akses file terbatas (`chmod 600`).
- **`auth.py`**: Menangani proses autentikasi interaktif (`ghup login`). Meminta PAT secara aman menggunakan `getpass` (masked input) dan memverifikasinya melalui endpoint GitHub `/user`.
- **`github_api.py`**: Modul penghubung komunikasi HTTP ke **GitHub REST API** menggunakan pustaka `requests`. Menangani autentikasi header, pengambilan isi repository (`contents`), upload file (`PUT`), hapus file (`DELETE`), list branch, dan rate limit. Dilengkapi otomatisasi inisialisasi branch pada repository kosong.
- **`uploader.py`**: Menangani logika inti pengunggahan file dan folder:
  - Pembacaan file secara rekursif (termasuk opsi `--flat`).
  - Kompresi folder ke format ZIP (`--zip`).
  - Upload paralel berkinerja tinggi menggunakan `ThreadPoolExecutor` untuk banyak file sekaligus.
  - Mekanisme *retry* otomatis jika koneksi jaringan terputus.
  - Pengunduhan file (`download`).
- **`commands/`**: Folder yang berisi kumpulan sub-perintah:
  - `repo.py`: Perintah terkait repository (`list`, `use`, `current`).
  - `branch.py`: Perintah terkait branch (`list`, `use`).
  - `upload.py`: Perintah file operations (`upload`, `download`, `ls`, `delete`, `rename`, `move`, `copy`, `mkdir`).
  - `system.py`: Perintah sistem & manajemen (`login`, `info`, `history`, `config`, `doctor`, `version`, `self-update`).
- **`utils.py`**: Menyediakan konsol Rich, banner ASCII, formatter ukuran file human-readable, dan pencatatan riwayat aktivitas (`logs/ghup.log` & `data/history.json`).

---

## 2. Cara Kerja Sistem (Workflow)

### A. Alur Autentikasi (`ghup login`)
1. Pengguna menjalankan `ghup login`.
2. Program meminta input *Personal Access Token* (PAT) GitHub secara tersembunyi (`getpass`).
3. GHUP mengirim HTTP `GET` ke `https://api.github.com/user` dengan header `Authorization: token <PAT>`.
4. Jika status HTTP `200 OK`, GitHub mengembalikan data profil pengguna (username). Token dan username kemudian disimpan ke file `data/config.json`.

### B. Alur Upload File (`ghup upload`)
1. Pengguna menjalankan perintah seperti `ghup upload /sdcard/Download/folder --folder Backup`.
2. GHUP membaca file lokal menjadi byte stream (`rb`).
3. GHUP mengecek apakah file tersebut sudah ada di repository GitHub pada path tujuan guna mendapatkan nilai `sha`.
4. Konten file dikonversi ke format **Base64**.
5. GHUP mengirim HTTP `PUT` ke endpoint konten repository GitHub. Jika repository masih baru/kosong (belum ada branch/commit), GHUP otomatis menginisialisasi repository tanpa error `Branch not found`.
6. **Progress Bar** interaktif dari pustaka `Rich` menampilkan status proses. Jika koneksi gagal, sistem melakukan **retry otomatis**.
7. Setiap aktivitas dicatat ke `logs/ghup.log` dan `data/history.json`.

---

## 3. Panduan Instalasi Rinci di Termux

### Langkah 1: Persiapan Termux & Dependensi Sistem
Buka aplikasi **Termux** di perangkat Android Anda, kemudian jalankan pembaruan paket dan instal dependensi dasar (`git` dan `python`):
```bash
pkg update && pkg upgrade -y
pkg install -y git python libffi openssl
```

### Langkah 2: Mengunduh (Clone) Repository GHUP
Masuk ke folder Download Anda lalu clone project (atau jalankan installer jika file sudah ada):
```bash
cd ~/storage/downloads
cd ghup
```

### Langkah 3: Menjalankan Skrip Installer (`install.sh`)
```bash
bash install.sh
```
*Installer ini akan otomatis mendeteksi Termux, menginstal dependensi Python (`requests`, `rich`, `typer`) secara aman, dan mendaftarkan perintah global `ghup`.*

---

## 4. Autentikasi & Login

Sebelum melakukan operasi ke GitHub, buat Personal Access Token (PAT) di GitHub dengan scope **`repo`** (atau izin *Contents: Read and write* pada Fine-grained tokens), lalu jalankan:
```bash
ghup login
```

---

## 5. Daftar Lengkap Perintah (Commands & Help)

Anda dapat melihat bantuan umum kapan saja dengan mengetik:
```bash
ghup --help
```

Berikut adalah daftar lengkap seluruh perintah, sub-perintah, opsi, dan contoh penggunaannya:

### ⚙️ 1. Manajemen Repository (`ghup repo`)
Untuk melihat bantuan sub-perintah repo:
```bash
ghup repo --help
```
* **`ghup repo list`**: Menampilkan daftar seluruh repository publik dan privat akun Anda beserta visibilitas dan default branch-nya.
* **`ghup repo use <owner/repo>`**: Menetapkan repository aktif yang akan digunakan untuk operasi upload/download selanjutnya.
  * *Contoh:* `ghup repo use xymz-dev/github-drive-bot`
* **`ghup repo current`**: Menampilkan repository yang sedang aktif saat ini.

### 🌿 2. Manajemen Branch (`ghup branch`)
Untuk melihat bantuan sub-perintah branch:
```bash
ghup branch --help
```
* **`ghup branch list`**: Menampilkan daftar branch yang tersedia di repository aktif.
* **`ghup branch use <branch_name>`**: Menetapkan branch default yang digunakan (misal `main`, `master`, atau `dev`).
  * *Contoh:* `ghup branch use main`

### 📤 3. Upload & File Operations (Root Commands)
* **`ghup upload <target>`**: Mengunggah file, folder, atau glob pattern ke repository aktif.
  * *Opsi:*
    * `-f, --folder <nama>`: Menaruh file/folder ke sub-folder tertentu di GitHub.
    * `-z, --zip`: Mengkompres folder menjadi file ZIP sebelum di-upload.
    * `--flat`: Meratakan struktur folder (mengunggah semua file langsung tanpa sub-folder).
    * `-b, --branch <nama>`: Target branch spesifik.
  * *Contoh:*
    ```bash
    ghup upload /sdcard/Download/file.txt --folder Dokumen
    ghup upload /sdcard/Download/my-folder/ --zip
    ghup upload /sdcard/Download/my-folder/ --flat
    ```
* **`ghup download <remote_path>`**: Mengunduh file dari repository GitHub ke perangkat lokal.
  * *Opsi:* `-o, --output <filename>`
  * *Contoh:* `ghup download Dokumen/file.txt -o hasil.txt`
* **`ghup ls [path]`**: Menampilkan daftar file dan folder di repository atau sub-path tertentu.
  * *Contoh:* `ghup ls` atau `ghup ls Dokumen/`
* **`ghup delete <remote_path>`**: Menghapus file di repository GitHub.
  * *Contoh:* `ghup delete Dokumen/lama.txt`
* **`ghup rename <old_path> <new_path>`**: Mengganti nama file remote di repository.
  * *Contoh:* `ghup rename lama.txt baru.txt`
* **`ghup move <src> <dest>`**: Memindahkan file remote ke path lain.
* **`ghup copy <src> <dest>`**: Menyalin file remote ke path lain.
* **`ghup mkdir <folder_path>`**: Membuat folder remote di GitHub (menambahkan placeholder `.gitkeep`).
  * *Contoh:* `ghup mkdir Backup/Database`

### 🛠️ 4. Sistem, Diagnostik, & Manajemen (`ghup system`)
* **`ghup login`**: Autentikasi akun GitHub dengan Personal Access Token.
* **`ghup info`**: Menampilkan informasi akun, repository aktif, branch aktif, jumlah file root, dan sisa rate limit API GitHub.
* **`ghup history`**: Menampilkan riwayat aktivitas terakhir (upload, delete, rename, download, dll).
* **`ghup config [key] [value]`**: Melihat atau mengubah pengaturan konfigurasi (seperti `retry_count`, `timeout`, dll).
  * *Contoh:* `ghup config` atau `ghup config retry_count 5`
* **`ghup doctor`**: Menjalankan diagnostik otomatis untuk memeriksa koneksi internet, validitas token, dan status GitHub API.
* **`ghup version`**: Menampilkan versi GHUP.
* **`ghup self-update`**: Memeriksa dan memperbarui GHUP.

---

## 6. Fitur Unggulan & Bonus

- **Upload Paralel (`ThreadPoolExecutor`)**: Memungkinkan pengunggahan banyak file secara bersamaan dengan kecepatan maksimal.
- **Auto-Retry & Empty Repo Handler**: Jika koneksi terputus, GHUP otomatis mengulang (*retry*). Jika repository baru/kosong, GHUP otomatis menginisialisasi branch tanpa error.
- **Rich Terminal UI**: Menampilkan banner, tabel berwarna, dan progress bar interaktif.
- **Logging & History**: Setiap aksi tercatat di `logs/ghup.log` dan riwayat interaktif `ghup history`.

---

## 7. Troubleshooting

- **Error `Command not found: ghup`**: Pastikan instalasi melalui `bash install.sh` selesai dengan sukses. Anda juga bisa menjalankan `python3 ~/.ghup/main.py`.
- **Error `401 Unauthorized` / `Resource not accessible`**: Token PAT Anda belum memiliki izin `Contents: Read and write`. Perbarui izin token di GitHub lalu jalankan `ghup login` kembali.
- **Error `Branch not found`**: Teratasi otomatis oleh sistem *fallback* GHUP pada versi terbaru. Pastikan Anda telah menjalankan `bash install.sh` untuk memperbarui.
