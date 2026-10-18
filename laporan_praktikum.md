# Laporan Praktikum BI Pertemuan 5

## Tujuan bisnis

Sebagai asumsi studi kasus pembelajaran, tujuan bisnis ditetapkan sebagai berikut:

Meningkatkan penjualan coffee shop melalui pertumbuhan aktivitas pembelian, peningkatan nilai penjualan, dan pengelolaan gerai serta produk berdasarkan data.

Analisis menggunakan data Januari sampai Juni 2023 sebagai dasar evaluasi. Target peningkatan numerik belum ditetapkan, sehingga hasil analisis digunakan untuk mengidentifikasi peluang dan menyusun tindakan yang dapat diuji.

## Hubungan tujuan dan indikator

| Aspek tujuan bisnis | Indikator atau analisis | Pertanyaan bisnis |
| --- | --- | --- |
| Pertumbuhan aktivitas pembelian | Transaksi tercatat per bulan dan distribusi per jam | Apakah aktivitas pembelian meningkat, dan kapan aktivitas paling tinggi? |
| Peningkatan nilai penjualan | Total penjualan dan pertumbuhan penjualan bulanan | Apakah penjualan meningkat dibandingkan bulan sebelumnya? |
| Peningkatan nilai penjualan per transaksi tercatat | Rata-rata nilai transaksi | Apakah nilai penjualan per transaksi tercatat meningkat? |
| Pengelolaan gerai | Perbandingan penjualan, transaksi, dan rata-rata nilai transaksi antar gerai | Gerai mana yang memerlukan perhatian, dan indikator apa yang perlu ditingkatkan? |
| Pengelolaan produk | Penjualan menurut kategori dan produk | Kategori dan produk mana yang memberikan kontribusi penjualan terbesar? |

Transaksi tercatat digunakan sebagai ukuran aktivitas pembelian yang tersedia dalam dataset. Indikator ini tidak menyatakan jumlah pelanggan unik atau frekuensi kunjungan setiap pelanggan.

## Status audit

- Status: LULUS AUDIT DASAR.
- Baris awal dan akhir: 149.116.
- Nilai kosong: 0.
- Baris duplikat dan ID berulang: 0.
- Spasi `product_detail` yang diperbaiki: 1.952.
- Produk dengan variasi harga: 15.
- Total unit terjual: 214.470.
- Total nilai penjualan: 698.812,33.

Variasi harga tidak otomatis dianggap salah karena dataset tidak memuat aturan harga baku, periode promosi, ukuran, atau konteks perubahan harga. Audit mencatatnya sebagai informasi untuk ditelusuri, bukan menghapus transaksi.

## Definisi empat indikator

| Indikator | Definisi | Cakupan |
| --- | --- | --- |
| Total penjualan | Jumlah `sales`, yaitu `transaction_qty * unit_price` | Periode dan gerai yang terpilih |
| Transaksi tercatat | Jumlah `transaction_id` unik | Periode dan gerai yang terpilih |
| Rata-rata nilai transaksi | Total penjualan dibagi transaksi tercatat | Periode dan gerai yang terpilih |
| Pertumbuhan bulan terakhir | `(penjualan bulan terakhir - penjualan bulan sebelumnya) / penjualan bulan sebelumnya * 100%` | Bulan terakhir terhadap bulan sebelumnya pada gerai yang sama |

## Angka kontrol dashboard

| Filter | Total penjualan | Transaksi tercatat | Rata-rata nilai transaksi | Growth Juni terhadap Mei |
| --- | ---: | ---: | ---: | ---: |
| Semua gerai | 698.812,33 | 149.116 | 4,69 | 6,23% |
| Astoria | 232.243,91 | 50.599 | 4,59 | 5,06% |

## Ringkasan bulanan semua gerai

| Bulan | Penjualan | Transaksi | Growth | Rata-rata |
| --- | ---: | ---: | ---: | ---: |
| Jan | 81.677,74 | 17.314 | Belum tersedia | 4,72 |
| Feb | 76.145,19 | 16.359 | -6,77% | 4,65 |
| Mar | 98.834,68 | 21.229 | 29,80% | 4,66 |
| Apr | 118.941,08 | 25.335 | 20,34% | 4,69 |
| Mei | 156.727,76 | 33.527 | 31,77% | 4,67 |
| Jun | 166.485,88 | 35.352 | 6,23% | 4,71 |

## Temuan grafik

- Perbandingan gerai: Hell's Kitchen memiliki penjualan tertinggi, yaitu 236.511,17 dengan 50.735 transaksi tercatat. Astoria berada di 232.243,91 dan Lower Manhattan 230.057,25.
- Kategori terbesar pada filter semua gerai adalah Coffee dengan penjualan 269.952,45 atau 38,63% dari total penjualan.
- Produk teratas berdasarkan nilai penjualan adalah Sustainably Grown Organic Lg (product_id 61) dengan penjualan 21.151,75. Peringkat ini berdasarkan nilai penjualan, bukan unit, laba, atau jumlah pelanggan.
- Jam dengan transaksi tercatat terbesar adalah 10:00 dengan 18.545 transaksi. Hal ini belum membuktikan antrean panjang karena dataset tidak memuat durasi layanan atau catatan antrean.

## Insight

Pada filter semua gerai periode Januari sampai Juni 2023, penjualan Juni meningkat 6,23% dibandingkan Mei, dari 156.727,76 menjadi 166.485,88. Transaksi tercatat juga naik dari 33.527 menjadi 35.352, dan rata-rata nilai transaksi naik dari 4,67 menjadi 4,71. Perubahan ini searah dengan tujuan bisnis: aktivitas pembelian dan nilai penjualan sama-sama meningkat. Dataset belum membuktikan penyebab kenaikan tersebut, sehingga pemeriksaan lanjutan dapat menelusuri kontribusi berdasarkan gerai, kategori, dan produk.

## Rekomendasi berdasarkan tujuan bisnis

| Temuan data | Tindakan yang diusulkan | Evaluasi hasil |
| --- | --- | --- |
| Aktivitas tertinggi terjadi pada jam 10:00 dengan 18.545 transaksi tercatat | Tinjau kecukupan staf dan persediaan pada jam tersebut menggunakan catatan operasional gerai | Bandingkan transaksi dan penjualan per jam sebelum dan sesudah penyesuaian |
| Coffee menyumbang 38,63% penjualan; Sustainably Grown Organic Lg memiliki nilai penjualan produk tertinggi | Prioritaskan pemeriksaan ketersediaan produk berkontribusi tinggi dan uji penawaran produk pelengkap | Pantau penjualan produk, unit terjual, dan rata-rata nilai transaksi tercatat |
| Penjualan Hell's Kitchen sebesar 236.511,17, Astoria 232.243,91, dan Lower Manhattan 230.057,25 | Bandingkan transaksi, nilai transaksi, jam operasional, dan bauran produk sebelum menentukan tindakan tiap gerai | Pantau penjualan dan pertumbuhan setiap gerai pada periode pembanding yang sama |

Rekomendasi tersebut merupakan usulan untuk diuji. Keberhasilan tindakan dinilai melalui perubahan indikator pada periode pembanding yang setara; kenaikan penjualan saja belum membuktikan peningkatan laba atau dampak tindakan tertentu.

## Exit ticket

- Indikator yang mudah disalahartikan: rata-rata nilai transaksi, karena `transaction_id` belum dipastikan sebagai seluruh isi struk pelanggan dan bukan pelanggan unik.
- Pertanyaan bisnis yang belum dapat dijawab: apakah laba meningkat, karena dataset tidak memuat biaya barang, biaya operasional, atau margin.

## Berkas bukti

- `audit_prepare_coffee.py`
- `app.py`
- `coffee_analytics.py`
- `data_prepared/audit_report.json`
- `data_prepared/monthly_summary.csv`
- `data_prepared/coffee_sales_prepared.csv`
- `screenshots/dashboard_semua_gerai.png`
- `screenshots/dashboard_astoria.png`

## Pengembangan dashboard

Dashboard dikembangkan menjadi tujuh tampilan: Ringkasan, Tren, Gerai, Produk, Waktu, Keputusan, serta Data & Audit. Filter mencakup tanggal, gerai, kategori, tipe produk, produk tertentu, hari, dan jam. Perbandingan periode menggunakan filter dimensi yang sama.

Analisis tambahan meliputi pertumbuhan transaksi dan nilai transaksi, kontribusi produk, Pareto penjualan, harga rata-rata tertimbang, heatmap aktivitas, serta usulan keputusan yang mengikuti data terpilih. Simulasi target menggunakan kenaikan transaksi dan nilai per transaksi secara gabungan; angka target awal merupakan contoh asumsi pembelajaran.

Ekspor tersedia dalam bentuk CSV transaksi terfilter, CSV agregasi, Excel ringkasan enam sheet, laporan analisis Markdown, dan hasil audit JSON. Perhitungan bulan parsial, pembanding nol atau tidak tersedia, serta filter tanpa data memiliki penanganan tersendiri. Definisi perhitungan dan cara menjalankan dicatat di `README.md`.

## Verifikasi dashboard lengkap

Sebanyak 18 pengujian perhitungan dan interaksi Streamlit lulus. Pemeriksaan browser dilakukan pada desktop 1440 x 1000 dan ponsel 390 x 844. Seluruh tujuh tampilan desktop serta Ringkasan, Produk, Waktu, dan Keputusan pada ponsel berhasil ditampilkan tanpa error browser atau luapan halaman horizontal. Angka KPI pada ponsel tidak terpotong.

Unduhan Excel memiliki enam sheet: Indikator, Bulanan, Gerai, Produk, Kategori, dan Jam. Penjualan pada sheet Indikator sesuai angka kontrol 698.812,33. Ekspor CSV seluruh cakupan berisi 149.116 baris, dan laporan keputusan memuat hasil analisis serta asumsi simulasi.

| Bukti terbaru | Tampilan |
| --- | --- |
| `screenshots/dashboard_lengkap_1.png` | Ringkasan |
| `screenshots/dashboard_lengkap_2.png` | Tren |
| `screenshots/dashboard_lengkap_3.png` | Gerai |
| `screenshots/dashboard_lengkap_4.png` | Produk |
| `screenshots/dashboard_lengkap_5.png` | Waktu |
| `screenshots/dashboard_lengkap_6.png` | Keputusan |
| `screenshots/dashboard_lengkap_7.png` | Data & Audit |
| `screenshots/dashboard_mobile_ringkasan.png` | Ringkasan pada ponsel |
| `screenshots/dashboard_mobile_produk.png` | Produk pada ponsel |
| `screenshots/dashboard_mobile_waktu.png` | Waktu pada ponsel |
| `screenshots/dashboard_mobile_keputusan.png` | Keputusan pada ponsel |
| `screenshots/verification.json` | Hasil pemeriksaan browser dan unduhan |
