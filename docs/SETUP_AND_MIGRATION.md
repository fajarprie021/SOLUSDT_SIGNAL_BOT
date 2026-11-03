# Panduan Memindahkan dan Menjalankan SOLUSDT Signal Bot

Dokumen ini menjelaskan langkah pemindahan source code ke komputer atau server lain, terutama di Windows. Jangan memindahkan folder `venv` dari komputer lama. Virtual environment menyimpan path absolut ke interpreter Python sehingga dapat rusak ketika username, lokasi instalasi Python, atau lokasi project berubah.

## 1. Persyaratan sistem

- Windows 10/11 atau environment server yang dapat menjalankan Python.
- Python 3.11 atau lebih baru. Python 3.14 juga dapat digunakan.
- Git untuk mengambil source dari GitHub.
- Koneksi internet HTTPS untuk mengambil data publik Binance.
- Tidak diperlukan Binance API key karena aplikasi memakai endpoint market-data publik.

Cek instalasi Python dan Git:

```powershell
python --version
py --version
git --version
```

Jika `python` mengarah ke Microsoft Store atau tidak ditemukan, gunakan Python Launcher:

```powershell
py --version
```

Untuk deployment Streamlit Cloud, Python dan Git lokal tidak perlu tersedia di server; dependency dipasang dari `requirements.txt`.

## 2. Ambil source code

Clone repository ke folder tujuan:

```powershell
git clone https://github.com/fajarprie021/SOLUSDT_SIGNAL_BOT.git
Set-Location .\SOLUSDT_SIGNAL_BOT
```

Jika source dipindahkan melalui ZIP, ekstrak hanya source code. Jangan ikut menyalin folder berikut:

- `venv/`
- `.venv/`
- `__pycache__/`
- `paper_trading.db`

Database lokal sengaja diabaikan oleh Git. Database tersebut berisi state paper trading dari mesin sebelumnya dan tidak diperlukan untuk instalasi baru.

## 3. Buat virtual environment baru

Buat environment dari interpreter Python yang benar-benar tersedia di komputer tujuan:

```powershell
py -3.14 -m venv .\venv
```

Jika `py -3.14` tidak tersedia, gunakan:

```powershell
python -m venv .\venv
```

Aktifkan environment:

```powershell
.\.\venv\Scripts\Activate.ps1
```

Jika PowerShell menolak script karena execution policy, jalankan perubahan untuk user saat ini:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Kemudian aktifkan ulang environment.

Verifikasi bahwa Python berasal dari project, bukan instalasi global:

```powershell
Get-Command python
python --version
python -c "import sys; print(sys.executable)"
```

`Get-Command python` dan `sys.executable` harus menunjuk ke `venv\\Scripts\\python.exe`. Jika prompt menampilkan `(venv)` tetapi `Get-Command python` masih menunjuk ke `WindowsApps\\python.exe`, environment belum benar-benar aktif atau alias Python Windows mengambil alih. Gunakan executable environment secara eksplisit:

```powershell
.\\venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\venv\\Scripts\\python.exe test_strategy_b.py
```

Alternatifnya, tutup terminal, buka terminal baru dari root project, lalu aktifkan ulang:

```powershell
.\\venv\\Scripts\\Activate.ps1
Get-Command python
```

Output executable harus menunjuk ke pola berikut:

```text
F:\AI\SOLUSDT_SIGNAL_BOT\venv\Scripts\python.exe
```

Pada komputer lain, drive dan username tentu dapat berbeda. Yang penting path menunjuk ke folder project tujuan.

## 4. Install dependency

Upgrade pip lalu install dependency yang tercatat:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Dependency utama yang digunakan aplikasi:

- `streamlit` untuk dashboard.
- `streamlit-autorefresh` untuk refresh otomatis.
- `pandas` untuk pengolahan candle dan indikator.
- `plotly` untuk chart.
- `requests` untuk koneksi API Binance.

Jika muncul `ModuleNotFoundError`, jangan install secara acak ke Python global. Pastikan environment aktif, lalu ulangi:

```powershell
python -m pip install -r requirements.txt
```

Cek package yang terpasang:

```powershell
python -m pip list
```

## 5. Periksa file source dan syntax

Jalankan compile seluruh source utama:

```powershell
python -m compileall app.py data indicators paper_trading strategies
```

Untuk file multi-timeframe dan trend filter:

```powershell
python -m py_compile data\multi_timeframe_data.py strategies\trend_filter.py
```

Jika `python` mengeluarkan pesan seperti `did not find executable at ...Python314...`, environment tersebut dibuat dari instalasi Python lama. Hapus dan buat ulang environment:

```powershell
deactivate
Remove-Item -Recurse -Force .\venv
py -3.14 -m venv .\venv
.\.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Jangan memperbaiki `pyvenv.cfg` secara manual sebagai solusi utama. Recreate environment lebih aman dan memastikan launcher, pip, dan path interpreter konsisten.

## 6. Jalankan test dan koneksi

Test koneksi market data:

```powershell
python test_connection.py
```

Test multi-timeframe:

```powershell
python test_multi_timeframe_data.py
```

Test trend filter jika file tersedia:

```powershell
python test_trend_filter.py
```

Test dashboard Streamlit:

```powershell
python -m streamlit run test_dashboard.py
```

Buka URL lokal yang ditampilkan, biasanya `http://localhost:8501`. Hentikan server dengan `Ctrl+C`.

## 7. Jalankan aplikasi utama

```powershell
python -m streamlit run app.py
```

Sebelum menjalankan, pastikan:

- Folder kerja adalah root project.
- `requirements.txt` sudah terinstall.
- Koneksi HTTPS tidak diblokir firewall, proxy, atau antivirus.
- Endpoint Binance dapat diakses dari jaringan tersebut.

Aplikasi akan mencoba endpoint Binance Futures dan fallback public market-data jika endpoint Futures mengembalikan HTTP 451. HTTP 451 biasanya berarti akses dibatasi berdasarkan lokasi jaringan/server.

## 8. Catatan database dan paper trading

- `paper_trading.db` dibuat otomatis saat aplikasi berjalan.
- Database menyimpan saldo virtual, posisi, dan trade history.
- Database tidak boleh dianggap sebagai backup source code.
- Pada Streamlit Cloud, filesystem bersifat ephemeral; database dapat hilang ketika instance restart atau redeploy.
- Real order execution tidak aktif. Aplikasi hanya melakukan paper trading.

Untuk memulai sesi paper trading baru secara lokal, gunakan tombol **RESET FORWARD SESSION** di sidebar aplikasi.

## 9. Deploy ke Streamlit Community Cloud

1. Pastikan perubahan sudah di-push ke branch `main` GitHub.
2. Buka [https://share.streamlit.io/](https://share.streamlit.io/).
3. Login dengan GitHub.
4. Buat app baru dari repository `fajarprie021/SOLUSDT_SIGNAL_BOT`.
5. Pilih branch `main`.
6. Isi file utama dengan `app.py`.
7. Deploy.

Streamlit Cloud akan menjalankan instalasi dari `requirements.txt`. Tidak perlu meng-upload `venv`, `paper_trading.db`, atau secrets untuk versi aplikasi saat ini.

Jika deployment gagal:

1. Buka **Manage app** lalu lihat **Logs**.
2. Untuk error `ModuleNotFoundError`, cek nama package di `requirements.txt`.
3. Untuk error `451`, periksa fallback endpoint dan lakukan **Reboot app**.
4. Untuk error import lokal, pastikan folder package (`data`, `indicators`, `paper_trading`, `strategies`) dan file init-nya ikut ter-push.
5. Setelah perubahan, push commit baru lalu pilih **Redeploy**.

## 10. Checklist pemindahan

- [ ] Source diambil dari repository yang benar.
- [ ] `venv` lama tidak disalin.
- [ ] Python terdeteksi dan versinya sesuai.
- [ ] Virtual environment baru dibuat di komputer tujuan.
- [ ] `python -c "import sys; print(sys.executable)"` menunjuk ke environment project.
- [ ] `pip install -r requirements.txt` berhasil.
- [ ] `compileall` atau `py_compile` berhasil.
- [ ] Test koneksi Binance berhasil.
- [ ] Test multi-timeframe berhasil jika fitur tersebut digunakan.
- [ ] Dashboard test dapat dibuka.
- [ ] `app.py` dapat dijalankan.
- [ ] Untuk Streamlit Cloud, `requirements.txt` dan source sudah di-push.
- [ ] `venv`, cache, secrets, dan database lokal tidak ikut dipublish.
