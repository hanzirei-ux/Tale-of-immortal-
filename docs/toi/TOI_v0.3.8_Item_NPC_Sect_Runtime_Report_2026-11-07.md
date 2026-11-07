# Tale of Immortal Android — Laporan Implementasi Item Manager + NPC/Sect v0.3.8

**Tanggal audit:** 7 November 2026  
**Jenis:** laporan status implementasi dan tes perangkat, **bukan** rilis stabil atau klaim seluruh fitur sudah berfungsi.  
**Repository kerja:** hanzirei-ux/Tale-of-immortal- (fork dari organisasi Beta-Tester-mod).  
**Baseline:** LiteAPK v0.3.6 + overlay Item Manager v0.3.7 + NPC/Sect v0.3.8; **jangan disamakan dengan proyek V60 lama**.  
**Workflow Android:** [Run #42383178234](https://github.com/hanzirei-ux/Tale-of-immortal-/actions/runs/42383178234), kesimpulan **success** untuk build otomatis dan validasi file.  
**Hasil tes HP:** sejumlah fitur telah dicoba pada Xiaomi 11T / Android 14 berdasarkan screenshot pengguna. Build success tidak sama dengan runtime success.

## 1. Ringkasan status yang benar

| Area | Implementasi/source | Bukti di HP | Status saat ini |
| --- | --- | --- | --- |
| UI Mod Menu v0.3.8 | Dikompilasi | Menu terbuka; hooks=15, player=loaded | UI/loading lolos tes awal |
| Katalog Item | 3.309 item ID | Daftar/filter tampil; ada status item APPLIED | Sebagian berfungsi; tes item kategori lain masih perlu |
| Katalog Manual | 185 template manual pada build | Manual bisa dipilih | Browse berhasil, **create/add BLOCKED** |
| Native Manual generator | Jalur dengan pemeriksaan konfigurasi/payload ditulis | 'Checked native manual generator unavailable' | **Belum berfungsi di HP** |
| Demon/Gourd item | Jalur item bag/reward ditulis | 'Native item reward method unavailable' | **BLOCKED**, penyebab awal di binding reward |
| Artifact | Jalur factory, realm, quality, rate, readback ditulis | 'Checked native Artifact factory unavailable' | **BLOCKED** |
| NPC discovery | WorldInitNPCTool.GetAllUnits; 20 per halaman | 2.149 NPC pada save uji, offset 80 terbaca | **Read-only terkonfirmasi** |
| NPC stat READ/SET/ADD/SUB/MULTIPLY | Kode JNI/native ada | REJECTED saat unitID belum dimasukkan | Mutasi **belum dibuktikan** |
| NPC Realm +1 | GMFunc.UnitGradeUp satu langkah + readback | Belum ada tes terverifikasi | Eksperimental, tidak boleh dianggap selesai |
| Sect EXP growth | Hook positif AddExp/AddFixExp scoped NPC sekte; 1/2/5/10× | Belum ada hasil before/after yang membuktikan multiplier | **Dikodekan, belum teruji runtime** |
| Sect material/manual/AI | Ada riset metode native, **belum dikodekan** ke bonus Sect v0.3.8 | Belum ada tes | Belum implementasi |

**Penting:** tulisan UI 'COMPILED — RUNTIME UNTESTED' adalah label statis yang belum disesuaikan setelah tes perangkat. Jangan gunakan label itu sebagai pengganti hasil per fitur di tabel ini.

## 2. Riwayat build dan integrasi

- Source privat v0.3.7 + v0.3.8 digunakan melalui ZIP yang diverifikasi SHA-256, tanpa menaruh source bundle privat di repository publik.
- Build awal di repository organisasi tidak menghasilkan workflow run. Fork ke akun Hanzirei berhasil menjalankan Actions.
- Kendala pertama di fork: setup Android SDK meminta paket 'tools' yang tidak tersedia. Workflow diperbaiki memakai Android SDK runner.
- Kendala kedua: URL Drive preview menghasilkan HTML; pipeline diubah menggunakan gdown. Pemeriksaan signature ZIP dan SHA-256 kemudian lolos.
- Run #42383178234: checkout, Java 17, Android SDK/NDK, restore overlay, host policy tests, kompilasi ARM64 .so + classes2.dex, format/hash checks, artifact upload **semuanya success**.
- Artifact: TOI_NPC_Sect_v038_ANDROID_TEST_PATCH, ID 13578940257; dijadwalkan kedaluwarsa 14 November 2026. Berisi patch test DEX, SO ARM64 dan build_manifest.json. **Bukan APK lengkap.**
- SHA-256 hasil build: classes2.dex = f6b63b4da6554051d3065f43e18f7411686e0d768b8576f3c3b38e4bf737a927; libtoimodmenu.so = 4d76f286b8457baf775a7b53a3a0394c2a51b3c1d53d321368e8c88a74ced3c6.
- Keberhasilan compile/host tests bukan jaminan semua JNI, IL2CPP method atau perubahan save benar pada runtime.

## 3. Implementasi Item Manager / katalog

### 3.1 Yang ada

- Data katalog v0.3.7 yang dipakai build: **3.309 native Item IDs**, termasuk 25 item hidden, dan **185 manual templates**; namespace Item ID dan Manual BaseID dipisahkan. Angka tersebut adalah data snapshot/hasil verifikasi input, **bukan** jumlah item yang terbukti bisa ditambahkan ke save.
- Kategori, filter Realm/warna/subtype, pencarian nama/ID, pagination, dan rincian yang dapat dibaca. Ada katalog template manual yang masih berbeda dari manual instance yang siap digunakan.
- Jalur normal Add Item terintegrasi dengan native reward dan validasi, dengan setidaknya satu hasil 'item — APPLIED' pada screenshot. Perlu pemeriksaan inventory/simpan-muat untuk per item agar tidak overclaim.
- Source memiliki guard untuk item unik, hidden, non-stackable, konteks owner/map/sect, batas jumlah, serta receipt/readback.

### 3.2 Bug nyata berdasarkan Details screenshot pengguna

1. **Manual / Skill** — contoh Whirlwind Blade, manual #M1:12113: 'manual — BLOCKED', detail **Checked native manual generator unavailable**. Salah satu / beberapa class, constructor, factory, reward method, atau object allocation prasyarat tidak tersedia pada runtime. Belum diketahui mana yang hilang; bukan otomatis kesalahan pilihan G3/Red.
2. **Demon / Devil Demon** — contoh Transformation Elixir #2823004: 'item — BLOCKED', detail **Native item reward method unavailable**. Tombol mengakses jalur reward inventory/gourd; perlu audit spesifik method binding dan ketersediaan manager. Pesan ini **tidak membuktikan** Gourd belum dibuka.
3. **Artifact** — contoh Skydevourer's Cyan Seal #3031109 (G10, Red): 'artifact — BLOCKED', detail **Checked native Artifact factory unavailable**. Salah satu / beberapa binding ctor/initializer/rates/set_grade/reward/factory/object_new tidak tersedia; perlu log diagnostic per binding, bukan menonaktifkan guard.
4. Filter Currency pernah menampilkan 'No matching items' walau jumlah item katalog besar. Periksa hidden flag dan kategori, jangan ditafsirkan bahwa semua Currency ID hilang.

### 3.3 Perbaikan yang belum dilakukan

- Native diagnosis granular: laporkan **nama class/method, signature/metadata token, dan mengapa resolve gagal** untuk Manual/Demon/Artifact secara terpisah.
- Verifikasi signature/instance/static, overload, versi metadata vs LiteAPK runtime; validasi tanpa menebak token, alamat atau object layout.
- Pertahankan semua guard terhadap invalid payload, readback tak cocok, dan reward ambigu. **Jangan fallback ke raw ID acak atau menyatakan APPLIED saat hasil tak terverifikasi**.
- Regression: normal item add, inventory, currency, contribution, export/katalog, kategori Gear/Outfit/Mount dan fitur cheat lama.

## 4. Implementasi NPC editor

### 4.1 Sudah dikodekan

- **NPC list**: WorldInitNPCTool.GetAllUnits; dikirim sebagai teks berisi unitID instance, nama dari GetName bila tersedia, gradeID dan schoolID; 20 NPC per halaman.
- **Stat READ/SET/ADD/SUBTRACT/MULTIPLY**: mencari target baru lewat GMFunc.GetUnitsType(unitID), validasi identitas, mencegah edit player, allowlist stat, batas native DynInt, lalu readback set_baseValue. Kode ada, tetapi keberhasilan pada HP belum terkonfirmasi.
- **Realm +1**: mencoba GMFunc.UnitGradeUp terhadap satu instance saja, lalu cek ulang gradeID; jika Boolean/grade tidak meyakinkan, status tidak boleh diklaim sukses.
- Tidak ada write langsung ke story flags, gender/race, hubungan, membership ataupun gradeID mentah.

### 4.2 Hasil dan kekurangan di HP

- **CONFIRMED**: daftar NPC memunculkan **2.149 total** di save pengguna (angka dinamis, bukan konstan dunia game); tampak page 'offset 80; 20/page' dengan unitID, nama, grade, sect.
- **LIMIT UI**: hanya Next +20 / Prev -20 dan input ID manual. Tidak ada search by name, pilihan profil NPC aktif, scan wilayah saat ini atau filter anggota Sect. Memaksa mencari di ribuan entri terlalu lambat.
- **REJECTED** pada npc_info/npc_stat di screenshot sebelumnya selaras dengan kolom unitID kosong/tidak valid. Belum ada bukti bahwa setter stat berhasil ataupun gagal jika ID yang benar diberikan.
- **POTENTIAL**: heroine (termasuk Ao Yao/Five Blooms) boleh ditemukan via sistem NPC umum, tetapi belum ada validasi aman untuk breakthrough, story events dan save. Jangan jadikan heroine tes mutasi pertama.

### 4.3 Perbaikan UI yang disarankan

1. Buat **Search NPC by name** dari data daftar; klik hasil untuk mengisi unitID instance secara otomatis. Nama tidak boleh mengganti unitID sebagai identitas mutasi karena mungkin duplikat.
2. Tambahkan filter Sect/Realm, favorite, dan pencarian substring tanpa harus terus Next +20. Gunakan pemindaian bertahap/caching dengan invalidasi saat world berubah.
3. Riset **Use Opened NPC** dari profil yang sedang dilihat dan **Nearby NPC** berbasis data lokasi (harus verifikasi pointer/manager, jangan menganggap semua 2.149 berdekatan).
4. Saat target dipilih, tampilkan nama, unitID, Sect, grade saat ini dan minta konfirmasi ulang sebelum APPLY.

## 5. Implementasi Sect growth — jawaban tegas

**YA: fitur percepatan pertumbuhan anggota Sect baru meliputi bonus EXP kultivasi saja.**

Yang sudah dikodekan dalam v0.3.8:
- Pilihan **1× (OFF), 2×, 5×, 10×**.
- Hook positif di PropertyData.AddExp / AddFixExp yang sudah ada.
- Hanya untuk target NPC dengan relasi PropertyData–UnitInfoData yang konsisten dan schoolID sama dengan Sect pemain saat ini; player sendiri tidak dianggap NPC target.
- Hanya mengalikan **EXP positif yang benar-benar diberikan game**. Tidak menghasilkan EXP gratis per bulan dan tidak membuat NPC otomatis mengambil keputusan.
- Setting **runtime-only**; kembali OFF pada perubahan world/player atau sesi baru, tidak disimpan permanen.
- **Belum terbukti lewat tes gain EXP NPC dalam game**. Perlu before/after serta kontrol NPC luar Sect.

**BELUM diimplementasikan** pada v0.3.8:
- Mempercepat AI bulanan / pemilihan goal kultivasi / jeda progression.
- Bantuan mencari, membeli, membuat, atau membagikan material breakthrough.
- Mempermudah syarat breakthrough atau membantu kenaikan Realm otomatis.
- Menaikkan kualitas manual/skill NPC atau otomatis belajar/equip/replace manual.
- Bonus EXP mastery skill, bukan EXP Realm.
- Kebijakan khusus heroine, cabang Sect, jabatan serta event cerita.

**Jangan campur** dengan editor resource Sect (treasury/funds/reputation/faith/contribution) yang merupakan fitur lain dari baseline lama. Edit resource tidak berarti perkembangan NPC otomatis sudah dibuat. Temuan riset dalam 'TOI_Sect_NPC_Growth_Research_20261107.zip' adalah pemetaan kandidat hook/action, **bukan fitur runtime yang sudah aktif**.

## 6. Daftar masalah prioritas

| Prioritas | Masalah | Yang perlu diverifikasi |
| --- | --- | --- |
| P0 | Manual generator BLOCKED | Binding spesifik yang null/gagal, signature, metadata, reward path |
| P0 | Demon native item reward BLOCKED | Method target, overload, manager/bag Gourd, availability feature |
| P0 | Artifact factory BLOCKED | Detail salah satu method/object_new, bentuk payload, rate/grade readback |
| P1 | NPC sulit dicari | Nama, filter Sect, target profil aktif, unitID otomatis |
| P1 | NPC stat belum tervalidasi | READ NPC biasa → satu stat kecil → readback → reload |
| P1 | Sect EXP belum tervalidasi | Bandingkan EXP gain anggota dan nonanggota setelah 2× |
| P2 | NPC Realm +1 berisiko | Uji pada NPC biasa di save salinan setelah stat stabil |
| P2 | Sect materials/manual/AI belum ada | Desain implementasi incremental, dengan cooldown/limits |
| P2 | Status UI statis 'RUNTIME UNTESTED' | Ganti dengan status pengujian per fitur, bukan klaim global |

## 7. Rencana tes bertahap, aman untuk save

- **Batch A — read-only**: cari NPC biasa berdasarkan unitID dari daftar; READ attack/stat; cek data grade/sect; screenshot Details. Jangan gunakan heroine.
- **Batch B — Item Manager**: satu item biasa yang sudah APPLIED sebagai kontrol; tes manual, Demon, Artifact dalam mode diagnosis resolve saja terlebih dahulu; jangan mengulang Add jika hasil 'INVOKED_UNVERIFIED'.
- **Batch C — Sect**: aktifkan 2×, amati satu gain EXP positif pada NPC yang benar-benar anggota Sect; bandingkan gain vanilla dan NPC luar Sect; ganti world lalu cek otomatis OFF. Jangan langsung skip bulan banyak.
- **Batch D — NPC mutation**: setelah read-only akurat, backup save dan tes perubahan kecil satu stat; reload save; lanjut Realm +1 hanya pada save percobaan terpisah.
- Jika salah satu batch gagal, rollback ke pasangan DEX/SO stabil yang sudah dicadangkan; jangan gabungkan ulang versi V60/LiteAPK.

**Peringatan:** checkbox UI 'Save backup ready' **bukan backup otomatis**. Buat backup file save dan APK secara nyata sebelum melakukan mutasi permanen.

## 8. Ruang lingkup update berikutnya (usulan, bukan implementasi)

1. Versi diagnostik: pecahkan pesan generic BLOCKED menjadi nama binding yang gagal; tidak mengubah guard ataupun memaksa reward.
2. Tambahkan index dan search NPC dari daftar yang sudah terbaca; klik nama → unitID persis; pertahankan validasi identitas native.
3. Uji Sect EXP 2× pada anggota + nonanggota, dan NPC stat READ di perangkat lebih dulu.
4. Berikutnya kembangkan material breakthrough / NPC buy book / study / equip dan AI berkala dari riset secara terpisah. Pastikan NPC di luar current player Sect tidak terkena.
5. Setiap rilis harus menyebut baseline hash, ABI, perubahan DEX/SO, hasil test, known issues, dan prosedur rollback.

## 9. Sumber teknis dan batas pelaporan

- Paket privat sumber: TOI_v038_GitHub_SourceBundle_PRIVATE.zip (188.301 byte; SHA-256 8a84869f1687700009544ac412f3901c42be9d3792de1ad39284ae73ee0b4235).
- Implementasi overlay v0.3.8: native/game_runtime.cpp, native/npc_sect_policy.hpp, Java ModMenu.java, tools/build_v038.py; semua berasal dari bundle privat, tidak dipublikasikan lewat laporan ini.
- Item native v0.3.7: native/item_creation.cpp dan evidence/item_method_signatures_v037.json di bundle.
- Laporan riset: TOI_NPC_Research_20261107.zip, TOI_Sect_NPC_Growth_Research_20261107.zip; riset tidak sama dengan implementasi.
- Evidence runtime: screenshot pengguna pada percakapan 7 November 2026 termasuk pesan Details BLOCKED, NPC LIST, status item APPLIED.
- Evidence kompilasi: [Workflow Run #42383178234](https://github.com/hanzirei-ux/Tale-of-immortal-/actions/runs/42383178234).
- **Klasifikasi:** CONFIRMED = terlihat sukses di HP atau hasil log build; SOURCE = dikodekan tetapi belum terbukti di HP; BLOCKED = ditolak runtime; RESEARCH = desain/pemetaan tanpa implementasi.
- Tidak ada perubahan source game, native binary, APK, save, ataupun fitur gameplay dalam commit laporan ini.
