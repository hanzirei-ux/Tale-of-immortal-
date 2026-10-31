TALE OF IMMORTAL LiteAPK MOD MENU v0.3.0 — BINARY PATCH
Status: COMPILED — NOT DEVICE TESTED
Target: ARM64 / arm64-v8a, khusus baseline LiteAPK yang sama dengan v0.2.

ISI PATCH
APK_ROOT/classes2.dex
APK_ROOT/lib/arm64-v8a/libtoimodmenu.so
Kedua file baru ini adalah pasangan API v3. Pasang keduanya bersama.
Ini patch untuk APK v0.2 yang sudah berfungsi, bukan APK mandiri.
classes.dex utama v0.2, libil2cpp.so, libandroidoyunclub.so, asset dan save tidak disertakan/diganti.

PERUBAHAN
- Teks terang, dropdown/input/tombol/dialog/slider lebih terbaca.
- Katalog item asli: daftar dapat digulir, 40 baris/halaman, pilih dengan tap,
  pencarian otomatis dengan prioritas prefix, nama Inggris/China jika tersedia.
- Recipe (Alchemy books): irisan ID formula asli dengan katalog item; menambah
  buku resep tidak otomatis mempelajari resep. Forge/Talisman belum difilter khusus.
- Capacity: READ/SET/ADD/SUBTRACT pada kapasitas efektif. Bonus tersimpan khusus
  pemain; jumlah item terpakai dilindungi; hasil dibaca ulang. Maksimum edit 2.000.
- Currency & Contribution: READ/SET/ADD/SUBTRACT untuk Spirit Stones, kontribusi
  pribadi, City Token, Immortal Store Token, dana/reputasi/faith sekte pemain.
- Hasil tiap operasi memiliki ID sendiri; pencarian tidak menimpa hasil edit.
- Diagnostik menyertakan operasi dan stack managed exception; ada tombol Copy.
- Kode hook combat/EXP dan aturan player-only v0.2 dipertahankan.

CARA PASANG DENGAN APKTOOL M
1. Simpan salinan APK v0.2 yang berhasil dan backup save. Jangan uninstall atau
   hapus data game. Tutup game sebelum mengganti APK.
2. Ekstrak ZIP ini. Buka salinan APK v0.2 melalui editor isi ZIP/APK Apktool M.
3. Ganti DEX helper lama yang berisi org/npc/toibridge/ModMenu dan NativeBridge.
   Biasanya classes2.dex. Jangan mengganti classes.dex utama.
   Jika helper lama berada di classes3.dex, ganti di nama itu dan jangan sisakan
   salinan helper lama. Jika classes2.dex berisi kelas game lain, jangan menimpanya;
   gunakan slot helper yang benar atau nama multidex berikutnya yang kosong.
   Jangan menaruh dua salinan kelas org/npc/toibridge di APK.
4. Ganti lib/arm64-v8a/libtoimodmenu.so dengan file dari APK_ROOT.
   Jangan menaruh direktori APK_ROOT itu sendiri di dalam APK.
5. Simpan/repack, lalu sign dengan kunci yang SAMA dengan APK v0.2 terpasang.
   ZIP patch ini tidak membawa kunci/certificate APK. Sertifikat LiteAPK asli
   belum dapat dipastikan dari ekstraksi; komponen DEX/SO tidak ditandatangani terpisah.
6. Instal sebagai pembaruan. Jika muncul konflik sertifikat, pertahankan aplikasi
   dan data yang ada; gunakan kunci v0.2 yang sama. Jangan menyelesaikannya dengan
   uninstall tanpa backup save yang sudah diperiksa.
7. Buka save, buka menu v0.3.0, lakukan READ terlebih dahulu. Centang backup
   acknowledgment untuk perubahan permanen. Uji jumlah kecil sebelum jumlah besar.

PENTING UNTUK CAPACITY
Setter base propGridNum pada baseline ini tidak melakukan penulisan. Patch memakai
bonus objData pemain yang diterapkan lewat getter khusus inventory milik pemain.
Game/plugin bag yang menggandakan kapasitas ikut diperhitungkan; perubahan ganjil
bisa ditolak bila penggandaan aktif. Reopen bag bila suatu tampilan belum refresh.
Gunakan save normal game lalu load ulang untuk menguji persistensi.
Reset runtime tidak menghapus bonus kapasitas atau saldo/item yang sudah diedit.
Jangan kembali ke library lama saat item melebihi kapasitas lama; kurangi isi bag
hingga muat dan pulihkan kapasitas secara eksplisit terlebih dahulu.

MATA UANG TERPISAH
Spirit Stones: item 10001. Kontribusi pribadi: item 10011 (bukan treasury).
City Token: item 10041. Immortal Store Token: item 10051, berbeda dari City Token.
Treasury money/faith: Int64; reputasi: Int32. READ sekte wajib sebelum APPLY.
Penghargaan kontribusi memakai jalur transaksi normal game dan bisa menaikkan
counter lifetime earned. Counter tersebut dilindungi dari overflow, bukan diedit
sebagai saldo. Achievement, totalSchoolMoney dan playerPostMoney bukan pilihan saldo.

Bila muncul APPLIED_WITH_WARNING, baca nilai aktual. Fungsi sekte asli dapat
mengubah saldo lalu gagal saat refresh UI. Jangan mengulang ADD otomatis.
Penanganan NullReference ditingkatkan, tetapi hilangnya semua exception belum
terbukti di perangkat. Salin detail melalui Diagnostics jika muncul lagi.

BUILD
Native: NDK r27c 27.2.12479018, Android API 23, C++17, arm64-v8a, 16 KiB alignment.
Java: Java 17, ECJ 3.38.0, Android platform 35, D8/R8 8.7.18, DEX min API 23.
Tidak ada APK lengkap dibangun/ditandatangani/dipasang dalam milestone ini.
Pengujian ponsel dan save/load dilakukan pengguna sesuai TEST_CHECKLIST.txt.
SHA-256 tiap komponen ada di SHA256SUMS.txt.
