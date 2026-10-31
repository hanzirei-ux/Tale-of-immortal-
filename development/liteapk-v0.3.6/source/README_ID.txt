TALE OF IMMORTAL LiteAPK — v0.3.6 FULL CATALOG, DEX-ONLY UPDATE
SOURCE IMPLEMENTED / HOST TESTED / COMPILED — NOT DEVICE VERIFIED
Collector tambahan: PARTIALLY IMPLEMENTED, dibatasi interface native JNI4.
Baca COLLECTOR_LIMITS.txt agar schema metadata tidak dianggap sebagai data runtime.

ISI
APK_ROOT/classes2.dex — DEX helper baru, JNI protocol 4 / 19 native methods tetap.
Tidak ada APK lengkap atau library native baru. Pertahankan libtoimodmenu.so
v0.3.1 yang dipakai v0.3.2:
SHA-256 ab57ba9bbe67c9b59f288b23eb92cacc7273c086ea7519e57cde741b8cc2f729
Ukuran 711848 bytes. Pertahankan classes.dex utama, libil2cpp.so dan aset/libraries game.

PASANG MELALUI APKTOOL M
1. Backup APK yang berfungsi dan save. Tutup game.
2. Buka SALINAN APK instalasi v0.3.2 yang sudah berfungsi melalui editor ZIP/APK.
   Tidak perlu mengirim APK atau membangun APK lengkap dari proyek ini.
3. Ganti DEX helper lama yang berisi org/npc/toibridge/ModMenu dan NativeBridge.
   Biasanya classes2.dex. Jika helper berada pada classes3.dex/slot lain, pasang
   DEX pengganti pada slot yang sama. Jangan menyisakan dua salinan helper.
4. APK_ROOT hanya petunjuk lokasi; jangan menambahkan folder APK_ROOT ke APK.
   Native library, classes.dex utama dan manifest tetap memakai instalasi lama.
5. Simpan/repack, sign menggunakan kunci yang sama dengan instalasi yang ada,
   kemudian pasang sebagai update. Bila signature berbeda, gunakan kunci yang benar;
   jangan uninstall/hapus data tanpa backup save yang dapat dipulihkan.
6. Buka game/save. Header menu harus menampilkan TOI v0.3.6. Bila protocol mismatch,
   periksa bahwa SO v0.3.1/2 yang benar tetap dipakai.

PENGGUNAAN
- Items / Recipes: tombol Export ALL item IDs lama tetap tersedia, format v0.3.2.
- Tombol baru Export Full Catalog mengekspor seluruh cakupan yang dapat dibaca
  JNI4 dan menambahkan schema, status bukti per field, manifest dan pengecekan ID.
- Progress menampilkan persen, tabel ConfItemProps, jumlah item/records, dan warning
  tabel lain BLOCKED_NATIVE. Metadata schema bukan hasil pembacaan tabel-tabel itu.
- Tetap di game, sebaiknya idle di world map tanpa mengganti scene/save. Hide menu
  boleh; Cancel, background/pause, reload world/save dan Activity destroy membatalkan.
- Full export tidak di-commit bila 3284 ID referensi tidak lengkap. Jika mendapat
  REFERENCE_ID_GAP, gunakan ekspor Item IDs lama untuk memeriksa perbedaan.
  Jangan memaksa menambah ID palsu atau menghapus item untuk menyesuaikan count.
- Sukses menunjukkan COMPLETE_SUPPORTED_SCOPE, item/record count dan lokasi JSONL.
- Save JSONL -> pilih Downloads/lokasi melalui UI Android -> tunggu pesan Saved.
  File dapat dibagikan lewat Files tanpa root atau permission storage luas.
- File disimpan mula-mula pada app-specific toi_catalog_exports. Save JSONL juga
  dapat mengambil file lengkap terakhir setelah restart selama file masih ada.

FILE / PARSER
Output full berupa JSONL dengan jenis record berbeda: item, item_type,
metadata_contract, dan catalog_manifest. Tabel yang belum dibaca dinyatakan
BLOCKED_NATIVE, tidak diisi row palsu. Status field: VERIFIED_RUNTIME,
VERIFIED_METADATA, VERIFIED_JOIN, INFERRED, UNKNOWN. Status adalah bukti asal data,
bukan klaim bahwa build v0.3.6 telah diuji di ponsel.

Pada komputer/Termux dengan Python, gunakan tools/normalize_full_catalog.py dari
source GitHub untuk menghasilkan items.jsonl, item_types.jsonl, realms.jsonl,
grades.jsonl, rarity.jsonl, localization.jsonl, books.jsonl, skill_templates.jsonl,
manual_templates.jsonl, manual_instances.jsonl, metadata_contracts.jsonl, manifest
serta items.csv. Section blocked tetap kosong dan ditandai pada manifest.
Kolom filter Realm | Type | Subtype | Grade | Rarity | Level tetap terpisah.
Tambahkan --baseline dump-v032.jsonl untuk merge; nilai baru UNKNOWN tidak menghapus
nilai lama yang terkonfirmasi. Konflik verified dihentikan, bukan ditimpa diam-diam.

KEAMANAN / PRESERVASI
Tidak ada perubahan inventory, stat, currency, save, skill learning atau Manual
creation dari tombol ekspor. Hooks gameplay/player-only dan editor lama tidak diubah.
File partial dibersihkan bila gagal/batal; orphan process kill dibersihkan pada
ekspor berikutnya. File lengkap lama tetap ada jika ekspor berikutnya gagal.
Jika proses dibunuh saat Save JSONL menyalin ke provider, hapus tujuan yang parsial
lalu ulangi Save; file app-specific asli dipertahankan.

ROLLBACK
Ganti kembali hanya DEX helper pada slot yang sama menggunakan patch v0.3.2.
Native SO tetap. Sign dengan kunci yang sama, instal sebagai update. Tidak perlu
menghapus save atau mengulang modifikasi permanen.

SHA256SUMS.txt memverifikasi file patch. Checklist ponsel ada di TEST_CHECKLIST.txt.
Source/report/build: development/liteapk-v0.3.6/ di repository proyek.
Tidak ada APK lengkap dibuat, ditandatangani atau diuji pada perangkat di milestone ini.
