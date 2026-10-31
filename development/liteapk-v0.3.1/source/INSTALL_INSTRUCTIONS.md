TALE OF IMMORTAL LiteAPK — MOD MENU v0.3.1 STABILITY HOTFIX
Status: COMPILED — NOT DEVICE TESTED
Target: arm64-v8a; Xiaomi 11T Android 14. Android 11 ARM64 tetap menjadi target kompatibilitas, belum diuji.

ISI
APK_ROOT/classes2.dex
APK_ROOT/lib/arm64-v8a/libtoimodmenu.so
Keduanya baru dikompilasi dari revisi source yang sama, protokol Java/native 4.
Ini patch kecil untuk APK v0.2/v0.3 yang sudah berjalan, bukan APK mandiri.

PERBAIKAN
- Key terjemahan hilang (termasuk item_name1041161 dan item_name1041162)
  mendapat fallback bahasa/key asli. Indexing tidak dihentikan oleh key hilang.
  Exception selain kasus KeyNotFound localization yang cocok tetap dilaporkan.
- Setiap kontrol melaporkan ID, nama, nilai, rentang, capability dan hasil native.
  Defense x16 valid; Spiritual x150 memberi OUT_OF_RANGE (batas 0.1..100).
  APPLIED berarti policy diterima dan dibaca ulang, bukan bukti efek combat.
- Rollback checkbox tidak memanggil apply secara rekursif; sukses membersihkan
  pesan gagal sebelumnya. Hasil asynchronous lama tidak menimpa operasi baru.
- Target combat pemain yang masih valid dipertahankan saat data diperbarui.
  Pemeriksaan baseline, kepemilikan pemain dan pembatalan edit save tetap aktif.
- Menu lebih ringkas, warna terang tetap, hasil detail dapat dilipat.
- Diagnostics menyediakan status tiap hook/capability dan hasil terakhir 22 kontrol.
- Currency tujuh resource dan Capacity Editor tetap memakai implementasi v0.3.

PASANG DI APKTOOL M
1. Simpan APK v0.2/v0.3 yang berhasil dan backup save. Tutup game.
2. Ekstrak patch ini; buka salinan APK yang sudah memiliki menu melalui editor ZIP/APK.
3. Ganti DEX helper lama yang berisi org/npc/toibridge/ModMenu dan NativeBridge.
   Biasanya classes2.dex. Jika helper ada di classes3.dex atau slot lain, ganti
   di slot tersebut. Jangan menimpa DEX game yang berbeda dan jangan menyisakan
   dua salinan kelas helper. Jangan mengganti classes.dex utama v0.2.
4. Ganti lib/arm64-v8a/libtoimodmenu.so. Pasang DEX dan SO dari ZIP yang sama.
   APK_ROOT adalah petunjuk lokasi; jangan memasukkan folder APK_ROOT ke APK.
5. Simpan/repack dan sign menggunakan kunci yang sama dengan APK terpasang.
   Jika sertifikat berbeda, jangan langsung uninstall/hapus data; gunakan kunci
   yang benar agar save tidak hilang. Patch ini tidak membawa sertifikat APK.
6. Instal sebagai update, buka save, buka menu berjudul v0.3.1.
   Jika ada CONTROL_ID_MISMATCH/protokol salah, periksa kedua file pengganti.
7. Uji checklist. Jangan menilai efek cheat hanya dari APPLIED atau hooks=15.

PENGGUNAAN
- Combat: centang ON, masukkan nilai, Apply. Nilai diterima dibaca ulang dari native.
- Slider ringkas tersedia untuk cooldown/energy cost. Nilai lain dapat diketik langsung.
- Tap baris hasil bawah untuk membuka/menutup detail. Diagnostics -> Copy report
  menyalin laporan lengkap. Ketika ditolak, laporkan control ID, rentang, capability
  dan kode hasil, bukan hanya jumlah hook.
- Item: kategori + pencarian, tap hasil, quantity, Add item, Confirm.
  Terjemahan yang tidak tersedia menampilkan key internal dan ID asli.
- Currency: READ dulu; kontribusi pribadi terpisah dari treasury. City Token 10041
  terpisah dari Immortal Store Token 10051; token terakhir tidak diasumsikan sebagai
  Chi You Alliance Battle Contribution.
- Capacity: READ, lalu ADD 50 untuk uji awal. Perlindungan occupied dan bonus ring/plugin
  tetap ada. Save/load belum dikonfirmasi di perangkat.
- Load hanya memuat pengaturan runtime, tidak mengulang edit currency/item/capacity.
  Reset mematikan runtime controls; tidak membatalkan edit permanen.

Tidak ada libil2cpp, metadata, asset game, classes.dex utama atau save dalam ZIP ini.
Tidak ada APK lengkap dibangun/ditandatangani/diinstal selama hotfix ini.
SHA256SUMS.txt mencatat checksum komponen; CHANGELOG.txt menjelaskan perubahan.
