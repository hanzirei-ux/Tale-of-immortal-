# Tale-of-immortal-

## Tale of Immortal Android LiteAPK Mod Menu v0.3.2 — Read-only Catalog Exporter

**SOURCE IMPLEMENTED · HOST TESTED · COMPILED — NOT DEVICE VERIFIED.** Pengguna melaporkan v0.3.1 sudah berfungsi di ponsel. v0.3.2 menambahkan Export ALL item IDs (read-only), Cancel, progress dan Save JSONL lewat pemilih file Android ke menu Items / Recipes yang sama.

- [Unduh DEX-only patch kecil (55,467 bytes)](development/liteapk-v0.3.2/TaleOfImmortal_ModMenu_v0.3.2_ReadOnlyCatalogExporter_BinaryPatch.zip)
- [Progres](development/liteapk-v0.3.2/PROGRESS.md), [source/build](development/liteapk-v0.3.2/source), [laporan teknis](development/liteapk-v0.3.2/source/PATCH_REPORT.md)
- [Pemasangan Apktool M dan rollback](development/liteapk-v0.3.2/source/README_ID.txt), [checklist ponsel](development/liteapk-v0.3.2/source/TEST_CHECKLIST.txt)
- [Rencana collector lengkap berikutnya](development/liteapk-v0.3.2/source/docs/CATALOG_COLLECTOR_NEXT.md)

Ganti hanya DEX helper di slot yang sama. **Pertahankan libtoimodmenu.so v0.3.1** (SHA-256 ab57ba9bbe67c9b59f288b23eb92cacc7273c086ea7519e57cde741b8cc2f729). Native/hooks/gameplay/JNI tidak diubah; protokol tetap 4 / 19 methods. Source dan binary v0.3.1 tetap menjadi rollback.

SHA-256 ZIP v0.3.2: `069fa832cf0db3164bf32135f21cd4faafe2e9ad0dd6d73d471ebb9ccb4717ca`.

Katalog saat ini belum lengkap: ALL hanya mencakup item non-hidden yang diekspos jalur native ConfItemProps, bukan seluruh skill/Manual. Nama unresolved, kategori kurang dan sekitar 11 Manual yang dilaporkan pengguna tetap menjadi batas collector awal. Field bahasa/rarity/description/key yang tidak tersedia dicatat null. Belum ada JSONL Android atau hasil device test exporter yang diklaim.

## Tale of Immortal Android LiteAPK Mod Menu v0.3.1 — Stability Hotfix

**COMPILED — NOT DEVICE TESTED.** Perbaikan pada build v0.3: fallback terjemahan item yang hilang, alasan penolakan kontrol yang spesifik, binding combat pemain saat refresh data, dan menu landscape yang lebih ringkas dengan warna terang tetap. Currency dan Capacity Editor dipertahankan.

- [Unduh binary patch kecil (312,574 bytes)](development/liteapk-v0.3.1/TaleOfImmortal_ModMenu_v0.3.1_StabilityHotfix_BinaryPatch.zip)
- [Progres pengembangan](development/liteapk-v0.3.1/PROGRESS.md)
- [Source dan build](development/liteapk-v0.3.1/source)
- [Laporan teknis dan hasil validasi](development/liteapk-v0.3.1/source/PATCH_REPORT.md)
- [Petunjuk Apktool M](development/liteapk-v0.3.1/source/README_ID.txt) dan [checklist ponsel](development/liteapk-v0.3.1/source/TEST_CHECKLIST.txt)

SHA-256 ZIP: `ebb7b51e5815a3c2ff029e4a1dd567ab44452d80f7a6f171f51ef45d50d2b112`.
DEX dan SO baru berasal dari revisi source yang sama; protokol 4 dengan 19 signature JNI yang cocok. Uji host dan validasi DEX/ELF lulus. Status APPLIED berarti policy diterima dan dibaca ulang, bukan bukti efek gameplay. Pengujian ponsel, save/load dan stabilitas sesi tetap diperlukan.

Patch berisi helper DEX dan library mod proyek ini, petunjuk, checksum dan lisensi. APK asli, libil2cpp, metadata/aset game, classes.dex utama, dan save pengguna tidak dipublikasikan. V60 di reports/ merupakan arsip proyek berbeda. Tidak ada APK lengkap bertanda tangan yang dibuat dalam milestone hotfix ini.

## Rollback v0.3.0

Direktori dan binary v0.3 dipertahankan. User melaporkan game/menu v0.3 dapat terbuka; hotfix v0.3.1 belum diuji di ponsel.

- [Binary v0.3.0 (281,242 bytes)](development/liteapk-v0.3.0/TaleOfImmortal_ModMenu_v0.3.0_Binary_Patch.zip)
- [Source v0.3.0](development/liteapk-v0.3.0/source)
- [Laporan v0.3.0](development/liteapk-v0.3.0/source/PATCH_REPORT.md)
