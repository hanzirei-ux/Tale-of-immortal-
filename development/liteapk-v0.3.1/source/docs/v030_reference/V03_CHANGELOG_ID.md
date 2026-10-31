# Tale of Immortal — v0.3 Source Fix / Uji Selanjutnya

**Status: SOURCE SUDAH DIPERBAIKI, ARM64 SO & DEX v0.3 BELUM DIBANGUN DI LINGKUNGAN INI.**

Jangan memakai ulang file `libtoimodmenu.so` dan `toimodmenu.dex` v0.2 sebagai pengganti v0.3. File binary v0.2 sengaja **tidak** disertakan dalam paket source fix ini.

## Perbaikan kode

1. **Teks UI gelap** — seluruh tombol, spinner, input, serta item list menggunakan foreground terang dan latar gelap berkontras. Header dipisah menjadi beberapa baris agar tidak bertabrakan pada landscape.
2. **Item Browser** — `All Types` tanpa mengetik nama akan memuat daftar item asli 40 per halaman; tersedia kategori, tombol Next/Previous, pilihan item dengan satu sentuhan, jumlah item, dan scroll.
3. **Pencarian/autocomplete** — pencarian otomatis di belakang layar dengan debounce 330ms; nama yang diawali kata pencarian tampil lebih dulu, disusul nama yang mengandung kata tersebut. ID item juga dapat dicari. Tidak harus menekan Search.
4. **Inventory Capacity** — `propGridNum` tidak lagi diperlakukan seperti stat yang dapat ditambah melalui `DynInt.set_baseValue` karena nilainya ter-clamp menjadi 52. Jalur baru memanggil perintah GM `beibao_N` dengan N 1–500 setelah konfirmasi backup, kemudian membaca `propGridNum` lagi. **Makna persis beibao_N dan efek permanennya belum diverifikasi**; uji dengan N=10 dan cek kapasitas di UI inventory setelah refresh dan save/load.
5. **Diagnostik kesalahan** — `MANAGED_EXCEPTION` sekarang menyertakan nama metode IL2CPP yang bermasalah bila tersedia, bukan hanya `NullReferenceException`. Penyebab NRE asli belum dipastikan; screenshot stack trace diperlukan bila terulang.
6. **Pengamanan katalog** — validasi kategori, query, offset; pemotongan per halaman, escape karakter yang mengganggu parser, dan pencegahan request katalog bertumpuk berlebihan.
7. **Cakupan** — NPC Editor tetap dikecualikan. Hook combat/EXP yang dilaporkan bekerja di v0.2 tidak diubah selain code path yang disebutkan.

## Keterbatasan saat ini

- Tidak ada Android SDK/NDK, R8/D8, dan smali toolchain di lingkungan pengembangan ini, sehingga tidak bisa mengeluarkan **binary v0.3 baru** atau APK terpasang dari sini.
- Java source lulus tes parser, tetapi belum lulus kompilasi terhadap `android.jar`.
- C++ native source lolos pemeriksaan sintaks (`g++ -Werror`) dan tes host; bukan bukti runtime Android.
- Nama item berasal dari konfigurasi game dan dapat berupa key lokalisasi (`item_name...`) sampai resolver bahasa game ditambahkan.
- `beibao_N` adalah jalur eksperimen terkontrol, bukan klaim pasti berhasil menambah slot.
- `NullReferenceException` sekarang mempunyai konteks error yang lebih jelas; akar error perlu screenshot/log saat runtime.
- APK hasil rebuild harus ditandatangani kembali dan mungkin membutuhkan uninstall yang berisiko pada save; backup dulu.

## Bangun 2 binary pengganti

Dari root source ini pada mesin dengan Android NDK r27c, Java 17, dan platform 35:

```bash
export ANDROID_NDK_ROOT=/lokasi/android-ndk-r27c
bash scripts/build_android.sh
mkdir -p out
cp patch/lib/arm64-v8a/libtoimodmenu.so out/libtoimodmenu.so
python3 tools/fetch_java_tools.py /tmp/toi-java-tools
python3 tools/build_menu_dex_only.py --java-tools /tmp/toi-java-tools --android-jar /lokasi/android-sdk/platforms/android-35/android.jar
python3 tools/build_v03_package.py
```

Atau gunakan `.github/workflows/build-v03.yml` dalam repository **private** jika tidak ingin instal toolchain lokal. Jalankan `workflow_dispatch`, lalu unduh artifact `TOI-v03-compiled-updates`.

Artifact yang dibuat berupa `TOI_v0.3.0_Compiled_Replace_v0.2.zip` yang hanya mencakup `toimodmenu.dex` dan `libtoimodmenu.so` BARU.

## Pasang pada APK v0.2 yang telah berhasil diuji

- **JANGAN ganti** `classes.dex` v0.2 yang sudah bisa membuka Mod Menu.
- Ganti helper DEX v0.2 dengan `toimodmenu.dex` baru. Nama dalam APK tetap `classes2.dex` bila dulu ditempatkan di sana, atau `classes3.dex` jika sebelumnya menggunakan itu.
- Ganti `lib/arm64-v8a/libtoimodmenu.so` dengan native library v0.3.
- Simpan, align dan tanda tangani APK baru melalui Apktool M. Jangan hapus data/save game.

Pada PC/Termux Python 3, tersedia `tools/apply_v03_to_v02_apk.py` untuk mengganti kedua binary dengan pemeriksaan SHA-256. Outputnya **unsigned**:

```bash
python3 tools/apply_v03_to_v02_apk.py Existing_v02_Modded.apk TOI_v0.3.0_Compiled_Replace_v0.2.zip New_v03_unsigned.apk
```

Script ini menolak APK yang tidak cocok dengan hash v0.2 sebelumnya, dan menjaga file lain tetap utuh.

## Pengujian pertama di HP

1. Backup save terlebih dahulu dan buat salinan APK v0.2 yang bekerja.
2. Periksa keterbacaan label, input, tombol, dan pilihan kategori pada berbagai layar.
3. Buka Items > All Types tanpa teks; gulir 40 item, pilih dan tekan Next. Pilih Manuals lalu verifikasi tipenya.
4. Ketik beberapa huruf awal nama atau nomor item; lihat saran otomatis. Pastikan ID yang dipilih mengisi field item.
5. Di Inventory, catat angka kapasitas dan `propGridNum` sebelum tes. Jalankan `Add Slots` dengan nilai **10** saja. Reopen inventory, cek UI, save/load, dan periksa apakah perubahan tetap ada.
6. Ulangi stat HP yang sebelumnya menimbulkan `NullReferenceException`; catat metode yang sekarang ditampilkan di error jika masih terjadi.
7. Cek ulang God Mode, damage, defense, EXP, dan cultivation agar perilaku v0.2 tidak berubah.
8. Jangan menganggap hasil tes host berarti berfungsi pada device sebelum langkah 1–7 dijalankan.
