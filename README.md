# iOS Photo Mover

Aplikasi Windows untuk memindahkan dan mengorganisir foto dari perangkat iOS ke komputer Windows melalui kabel USB.

## Fitur

1. **Koneksi iOS ke PC**: Terhubung ke perangkat iOS melalui kabel USB
2. **Pemilihan Foto**: Pilih foto yang ingin dipindahkan dengan mudah
3. **Pengaturan Pengurutan**: 
   - **Month_Year**: Mengurutkan berdasarkan Bulan-Tahun (contoh: `2024-01`)
   - **Date_Month_Year**: Mengurutkan berdasarkan Tanggal-Bulan-Tahun (contoh: `2024-01-15`)
4. **Folder Unknown**: Foto tanpa tanggal akan dipindahkan ke folder "Unknown" yang dapat dikonfigurasi
5. **Path yang Dapat Dikonfigurasi**: Pilih lokasi output dan folder Unknown sesuai kebutuhan

## Instalasi

### Prasyarat

1. **Python 3.8 atau lebih baru** - [Download Python](https://www.python.org/downloads/)
2. **iTunes atau Apple Mobile Device Support** - Diperlukan untuk koneksi ke perangkat iOS
3. **Perangkat iOS** dengan kabel USB

### Langkah Instalasi

1. Clone atau download repository ini
2. Buka terminal/command prompt di folder project
3. Install dependencies:
```bash
pip install -r requirements.txt
```

**Catatan**: `pymobiledevice3` memerlukan beberapa dependensi sistem. Jika mengalami masalah:

- **Windows**: Pastikan Anda telah menginstall [iTunes](https://www.apple.com/itunes/) atau [Apple Mobile Device Support](https://support.apple.com/downloads)
- Jika masih ada masalah, coba install dengan:
```bash
pip install pymobiledevice3[usbmuxd]
```

## Penggunaan

1. **Jalankan aplikasi**:
```bash
python main.py
```

2. **Hubungkan perangkat iOS**:
   - Sambungkan iPhone/iPad ke PC menggunakan kabel USB
   - Buka kunci perangkat iOS Anda
   - Jika diminta, pilih "Trust This Computer" di perangkat iOS

3. **Koneksi di aplikasi**:
   - Klik tombol "Connect to iOS Device"
   - Tunggu hingga status berubah menjadi "Connected"

4. **Load foto**:
   - Klik tombol "Load Photos from Device"
   - Foto akan muncul di daftar

5. **Pilih foto**:
   - Centang foto yang ingin dipindahkan (klik kotak di kolom pertama)
   - Gunakan "Select All" atau "Deselect All" untuk memilih semua/tidak ada

6. **Konfigurasi**:
   - Pilih mode pengurutan: **Month_Year** atau **Date_Month_Year**
   - Pilih "Output Base Path" - folder utama tempat foto akan disimpan
   - Pilih "Unknown Folder Path" - folder untuk foto tanpa tanggal

7. **Pindahkan foto**:
   - Klik tombol "Move Selected Photos"
   - Konfirmasi aksi
   - Proses akan berjalan dan progress ditampilkan di log

## Struktur Folder Output

### Mode Month_Year:
```
Output Base Path/
├── 2024-01/
│   ├── IMG_001.jpg
│   └── IMG_002.jpg
├── 2024-02/
│   └── IMG_003.jpg
└── Unknown/
    └── IMG_004.jpg
```

### Mode Date_Month_Year:
```
Output Base Path/
├── 2024-01-15/
│   ├── IMG_001.jpg
│   └── IMG_002.jpg
├── 2024-01-20/
│   └── IMG_003.jpg
└── Unknown/
    └── IMG_004.jpg
```

## Konfigurasi

Aplikasi menyimpan konfigurasi di file `config.json`. Anda dapat:
- Mengubah konfigurasi melalui UI
- Klik "Save Configuration" untuk menyimpan pengaturan
- Konfigurasi akan otomatis dimuat saat aplikasi dibuka

## Troubleshooting

### Perangkat tidak terdeteksi
- Pastikan kabel USB terhubung dengan baik
- Pastikan perangkat iOS dalam keadaan terbuka (unlocked)
- Pastikan Anda telah memilih "Trust This Computer" di perangkat iOS
- Pastikan iTunes atau Apple Mobile Device Support terinstall
- Coba cabut dan sambungkan kembali kabel USB

### Error saat install pymobiledevice3
- Pastikan Python 3.8+ terinstall
- Coba update pip: `python -m pip install --upgrade pip`
- Install dengan: `pip install pymobiledevice3[usbmuxd]`

### Foto tidak muncul
- Pastikan perangkat terhubung dan terpercaya
- Coba klik "Load Photos from Device" lagi
- Beberapa perangkat iOS mungkin menyimpan foto di lokasi berbeda

### Error saat memindahkan foto
- Pastikan path output dan unknown folder valid
- Pastikan ada ruang disk yang cukup
- Periksa log untuk detail error

## Catatan Penting

- **Backup**: Disarankan untuk membuat backup foto sebelum memindahkan
- **Original Files**: Aplikasi ini **menyalin** foto dari perangkat, bukan menghapus. Foto asli tetap ada di perangkat iOS
- **File Duplikat**: Jika file dengan nama yang sama sudah ada, aplikasi akan menambahkan nomor (contoh: `IMG_001_1.jpg`)

## Lisensi

Aplikasi ini dibuat untuk penggunaan pribadi.

## Kontribusi

Jika menemukan bug atau ingin menambahkan fitur, silakan buat issue atau pull request.

