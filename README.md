# Tale-of-immortal-

## v0.3.6 — DEX-first Full Catalog schema

**SOURCE IMPLEMENTED / HOST TESTED / COMPILED — NOT DEVICE VERIFIED.** Full native table collection remains **PARTIALLY IMPLEMENTED / BLOCKED_NATIVE**. This is an actual DEX-only update over v0.3.2; keep the proven existing SO.

- [Download DEX-only patch (68,221 bytes)](development/liteapk-v0.3.6/TaleOfImmortal_ModMenu_v0.3.6_FullCatalog_DEXOnly_BinaryPatch.zip)
- [Raw replacement classes2.dex](development/liteapk-v0.3.6/classes2.dex)
- [Progress](development/liteapk-v0.3.6/PROGRESS.md), [source/build](development/liteapk-v0.3.6/source), [technical report](development/liteapk-v0.3.6/source/PATCH_REPORT.md)
- [Apktool M install/rollback](development/liteapk-v0.3.6/source/README_ID.txt), [phone checklist](development/liteapk-v0.3.6/source/TEST_CHECKLIST.txt)
- [Exact native blocker](development/liteapk-v0.3.6/source/docs/NATIVE_COLLECTOR_BLOCKER_V036.md)

New: Export Full Catalog, progress, per-field evidence, metadata definitions, 3,284-ID protection, JSON Schema and parser/merge with independent Realm/Type/Subtype/Grade/Rarity/Level columns. The old exporter remains byte-identical in host tests. 80 Python tests, Java/native suites, actual DEX/ELF/JNI and 3,284-ID host replay passed.

**The existing JNI4 interface still transmits only ID, display name, raw type and level for non-hidden items.** Actual Realm/rarity/language/description/skill/manual values are not newly collected by this DEX. Unsupported fields remain null/UNKNOWN; schema rows are not runtime data. No new native SO or full APK is supplied. See the blocker report before expecting those tables.

ZIP SHA-256: `75d988db79166ba07a0b3aa5499931d25e6f4866689e1566acef4a72e88acfae`.

Prior v0.3.1/v0.3.2 source and patches remain intact below. No proprietary game binary, metadata, raw AssetBundle, save or private phone dump is published.

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
