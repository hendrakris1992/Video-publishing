# Template prompt: ganti baju model di video (rekaman sendiri)

Status: **belum diuji** di alat mana pun (Higgsfield Genjutsu / Runway Aleph / Luma Modify Video). Anggap ini titik awal dan sesuaikan dengan dokumentasi model yang dipakai (console.higgsfield.ai, atau situs Runway). Batas durasi klip dan harga datang dari sumber pihak ketiga, cek di situs resmi masing-masing.

## Syarat sebelum mulai
- Video adalah **rekaman baru milik sendiri**, dan **modelnya sudah setuju** bajunya diganti dengan AI.
- Jangan pakai video dari akun orang lain atau unduhan TikTok.
- Aturan repo: gambar atau video buatan AI hanya kalau diminta eksplisit, dan setiap pemakaian kredit disetujui dulu. Jangan tambahkan klaim harga, diskon atau bahan yang belum disetujui.

## Persiapan input
- **Video:** file asli dari ponsel, satu baju per klip, pose dan latar sama. Potong jadi segmen pendek (mulai dari 3 sampai 5 detik), beri nama berurutan, misalnya `01_depan`, `02_samping`, `03_belakang`.
- **Referensi baju:** foto datar atau gantungan, depan **dan** belakang, cahaya merata, tanpa orang.
- **Satu perubahan per percobaan:** hanya baju atas, atau hanya bawahan.

## Template prompt (English)
```
Replace only the [top / bottoms] the woman is wearing with the garment in the
reference image. Keep her face, hair, body shape, pose, movement, the background,
the lighting and the camera framing exactly as in the original video.
The new garment: [color as the user states it], [cut and length as the user states it].
Match the reference garment's color, pattern, collar, sleeves and hem exactly.
Do not add logos, text, accessories or extra layers. Do not change anything else.
```
Isi tanda kurung hanya dengan kata-kata sendiri tentang baju itu, bukan tebakan.

Untuk segmen yang memperlihatkan punggung, tambahkan satu baris:
```
The back of the garment matches the back reference image.
```

## Daftar cek sebelum dipakai (tonton frame demi frame)
1. Warna dan pola sama dengan foto produk, termasuk di bawah cahaya berbeda.
2. Kerah, lengan, panjang, kancing atau saku sesuai produk asli.
3. Bagian belakang cocok dengan foto belakang, bukan karangan AI.
4. Wajah, rambut dan tangan tidak berubah, dan tidak ada kedipan atau lompatan di tepi baju.
5. Sambungan antar segmen halus, tanpa perbedaan warna, kain atau bentuk tubuh.
6. Latar, teks dan elemen lain tidak ikut berubah.
7. Tidak ada logo atau tulisan baru yang muncul di baju.

Kalau bagian belakang gagal, ulangi dengan foto belakang yang lebih jelas. Kalau tetap tidak sesuai produk asli, jangan dipakai untuk jualan.

## Sebelum diunggah
- Beri label konten buatan AI sesuai aturan platform (belum diverifikasi, cek di pengaturan TikTok atau Instagram).
- Pastikan warna, potongan dan detail di video tidak menyesatkan soal produk aslinya.
