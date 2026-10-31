TALE OF IMMORTAL LiteAPK — MOD MENU v0.3.2 READ-ONLY CATALOG EXPORTER
Status exporter: SOURCE IMPLEMENTED / HOST TESTED / COMPILED — NOT DEVICE VERIFIED
Baseline v0.3.1: pengguna melaporkan berhasil diuji di ponsel.

ISI PATCH
APK_ROOT/classes2.dex — helper baru, tetap memakai JNI protocol 4 (19 methods).
Library native TIDAK disertakan atau dibangun ulang. Pertahankan SO v0.3.1:
lib/arm64-v8a/libtoimodmenu.so
SHA-256 ab57ba9bbe67c9b59f288b23eb92cacc7273c086ea7519e57cde741b8cc2f729
Ukuran 711848 bytes.
Ini patch untuk instalasi v0.3.1 yang sudah berfungsi, bukan APK mandiri.

PASANG DENGAN APKTOOL M
1. Backup APK v0.3.1 yang berfungsi dan save. Tutup game.
2. Ekstrak ZIP ini. Buka salinan APK v0.3.1 lewat editor ZIP/APK Apktool M.
3. Ganti DEX helper yang berisi org/npc/toibridge/ModMenu dan NativeBridge.
   Biasanya classes2.dex. Jika helper berada di classes3.dex atau slot lain,
   pasang DEX baru di slot yang sama. Jangan menambahkan duplikat kelas helper.
   Folder APK_ROOT hanya petunjuk lokasi; jangan memasukkannya ke dalam APK.
4. Pertahankan classes.dex utama, libtoimodmenu.so v0.3.1, libil2cpp.so,
   library startup dan aset game. Patch ini tidak memerlukan perubahan manifest.
5. Simpan/repack dan sign dengan kunci yang sama dengan APK yang terpasang.
   Instal sebagai update. Jika sertifikat tidak cocok, gunakan kunci yang benar;
   jangan uninstall/hapus data tanpa memastikan backup save dapat dipulihkan.
6. Buka game/save, lalu menu. Header harus menampilkan TOI v0.3.2.
   Jika protocol mismatch, periksa bahwa SO v0.3.1 tetap terpasang.

EKSPOR / AMBIL FILE DI ANDROID 14
1. Load save pemain. Buka Items / Recipes.
2. Tekan Export ALL item IDs (read-only). Tetap di game selama proses berlangsung.
   Progress menunjukkan jumlah baris yang sudah ditulis dan total dari native.
   Browser, search, pilihan item dan Add Item tetap terpisah dari tombol ekspor.
3. Sukses menampilkan jumlah aktual dan lokasi toi_item_catalog_*.jsonl.
   File disimpan di app-specific external files/toi_catalog_exports; jika storage
   external tidak tersedia, dipakai internal files/toi_catalog_exports.
4. Tekan Save JSONL. Pilih lokasi lewat pemilih file Android, misalnya Downloads,
   dan konfirmasi simpan. Tunggu pesan Saved JSONL beserta jumlah bytes/URI.
   Buka aplikasi Files untuk mengirim file JSONL itu ke chat atau penyimpanan lain.
   Tidak perlu root, izin storage luas, atau membuka Android/data lewat file manager.
5. Membatalkan pemilih lokasi tidak menghapus ekspor asli. Save JSONL dapat diulang,
   termasuk setelah restart selama file app-specific terakhir masih tersedia.

PERILAKU AMAN
- Satu request catalog per halaman (maksimal 40 baris). Tidak ada AddItem, GM,
  perubahan stat, inventory, currency, atau save yang dilakukan tombol ekspor.
- Penulisan file di worker terpisah. Callback Unity dan native mailbox tetap asli.
- Cancel, pause/background, Activity ditutup, world/save reload, timeout,
  receipt salah, jumlah berubah dan ID duplikat menghentikan sesi.
- File .partial dibersihkan pada gagal/batal; orphan akibat process kill dibersihkan
  pada ekspor berikutnya. File lengkap lama tetap tersedia bila ekspor baru gagal.
- Simpan ke lokasi pilihan berlangsung terpisah dari ekspor. Jika proses aplikasi
  dibunuh saat menyalin, file tujuan bisa belum lengkap; hapus tujuan itu dan ulangi
  Save JSONL. File app-specific asli dipertahankan.
- EXP/combat/player stats/currency/capacity dan player-only hooks tidak diubah.
  Load pengaturan tetap tidak mengulang edit permanen.

BATAS CAKUPAN — PENTING
ALL berarti semua baris yang diekspos katalog native saat ini, bukan seluruh
configuration game. Native melewati item hide!=0. Browser saat ini belum lengkap,
masih ada nama unresolved/kategori kurang, dan sekitar 11 Manual dilaporkan pengguna.
Skill/manual template dan Manual instance membutuhkan collector terpisah.

Setiap baris JSONL mencatat ID, display_name, props_type, level, source_table,
snapshot_generation dan cakupan. Key item_name... yang terlihat dicatat sebagai
name_key dan fallback=true. Jika key asli atau status localization tidak dapat
terbukti dari transport empat kolom, nilainya null (unknown). English/Chinese,
rarity/grade/color, description dan subtype yang belum tersedia juga null.
Level TIDAK dianggap rarity. Nama/ID/warna yang hilang tidak direka.

ROLLBACK
Ganti kembali hanya DEX helper di slot yang sama dengan DEX dari patch v0.3.1
sebelumnya. SO v0.3.1 tetap. Sign dengan kunci yang sama dan instal sebagai update.
Tidak perlu menurunkan save atau mengulang cheat. JSONL terpisah dari save game.

SHA256SUMS.txt memverifikasi file patch. TEST_CHECKLIST.txt berisi uji ponsel.
Source, build dan laporan: development/liteapk-v0.3.2/ di repository proyek.
Tidak ada APK lengkap dibangun/ditandatangani/diinstal selama milestone ini.
