# Coffee Shop Sales - Praktikum BI Pertemuan 5

Dashboard Streamlit untuk mengevaluasi pertumbuhan aktivitas pembelian, nilai penjualan, kinerja gerai, dan kontribusi produk. Sumber data adalah `Coffee Shop Sales.xlsx`, periode Januari-Juni 2023.

## Menjalankan di Windows

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe audit_prepare_coffee.py
.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.port 8501
```

Dashboard tersedia di `http://localhost:8501`. Jika virtual environment dan data siap analisis sudah tersedia, cukup jalankan perintah Streamlit.

## Tampilan analisis

| Tampilan | Isi |
| --- | --- |
| Ringkasan | KPI, pertumbuhan bulan terakhir, unit per transaksi, penjualan per hari terpilih, tren, kontribusi gerai, dan sinyal bisnis |
| Tren | Interval harian/mingguan/bulanan, rata-rata bergerak 7 hari, pertumbuhan penjualan dan komponennya, serta perbandingan harian dua periode |
| Gerai | Peringkat, aktivitas versus nilai transaksi, kontribusi, perubahan terhadap pembanding, tren tiap gerai, dan profil kategori/jam |
| Produk | Peringkat menurut penjualan/transaksi/unit, kontribusi kategori dan tipe, Pareto, pencarian, detail produk, variasi harga, dan harga tertimbang |
| Waktu | Distribusi jam/hari, rata-rata per kemunculan hari kalender, serta heatmap hari-jam dan gerai-jam |
| Keputusan | Usulan tindakan yang mengikuti filter, indikator evaluasi, simulasi target transaksi dan nilai transaksi, serta laporan Markdown |
| Data & Audit | Pencarian dan halaman transaksi, CSV terfilter, ringkasan Excel enam sheet, laporan analisis, serta audit sumber |

Filter global mencakup periode, gerai, kategori, tipe, produk, hari, dan jam. Pembanding menggunakan dimensi yang sama. `Periode sebelumnya` memiliki jumlah hari kalender yang sama: misalnya 1-30 Juni dibandingkan dengan 2-31 Mei. Rentang pembanding kustom boleh berbeda durasi; dashboard menyatakan bahwa perubahan tersebut membandingkan total periode.

## Aturan perhitungan

- Penjualan = `transaction_qty * unit_price`.
- Transaksi tercatat = jumlah `transaction_id` unik dalam cakupan.
- Nilai per transaksi = total penjualan / transaksi tercatat.
- Unit per transaksi = total unit / transaksi tercatat.
- Harga rata-rata tertimbang produk = penjualan produk / unit produk.
- Pertumbuhan bulanan hanya tersedia ketika kedua bulan kalender berturut-turut penuh, tanggal sumber tercakup, dan nilai pembanding di atas nol. Bulan di luar rentang terpilih tidak digunakan sebagai pembanding bulanan.
- Perubahan terhadap pembanding tidak dihitung jika rentang berada di luar sumber atau nilai pembanding nol.
- Penjualan per hari menggunakan hari kalender sesuai filter hari, termasuk tanggal tanpa transaksi. Angka ini tidak mengukur produktivitas per jam buka.
- Heatmap normalisasi membagi aktivitas masing-masing hari dengan jumlah kemunculan hari tersebut dalam rentang kalender terpilih.
- Simulasi = penjualan awal x `(1 + target transaksi / 100)` x `(1 + target nilai transaksi / 100)`. Contoh 5% dan 3% menghasilkan 8,15%, bukan 8%.

Mata uang tidak dinyatakan pada sumber. Transaksi tercatat belum dipastikan sebagai seluruh isi struk, bukan pelanggan unik, dan tidak dapat membuktikan pembelian produk secara bersamaan. Dataset tidak memuat biaya, laba, stok aktual, durasi layanan, atau riwayat promosi. Rekomendasi dan simulasi merupakan bahan uji keputusan.

## Struktur berkas

- `app.py`: antarmuka dan ekspor dashboard.
- `coffee_analytics.py`: filter, agregasi, pembanding, normalisasi, dan simulasi.
- `audit_prepare_coffee.py`: audit dan persiapan data sumber.
- `data_prepared/`: CSV dan JSON hasil audit.
- `tests/`: pengujian perhitungan dan interaksi Streamlit.
- `tools/verify_dashboard.py`: pemeriksaan browser desktop/mobile dan unduhan.
- `screenshots/`: bukti tampilan praktikum.
- `laporan_praktikum.md`: laporan praktikum dan tujuan bisnis.

## Verifikasi

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Pemeriksaan browser membutuhkan Playwright dan Google Chrome lokal, serta dashboard yang sedang berjalan:

```powershell
.venv\Scripts\python.exe -m pip install playwright
.venv\Scripts\python.exe tools/verify_dashboard.py
```

Angka kontrol seluruh data: penjualan 698.812,33; transaksi tercatat 149.116; unit terjual 214.470; pertumbuhan Juni terhadap Mei 6,23%.
