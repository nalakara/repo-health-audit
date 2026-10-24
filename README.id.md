[English](README.md) | **Bahasa Indonesia**

# Repo Health Audit

**Repo kamu terlihat selesai. Tapi sanggupkah ia lolos scorecard pembeli?**

Repo Health Audit adalah skill agent gratis yang menilai repository kode apa pun dari 0 sampai 100 di delapan dimensi kesehatan engineering, menunjukkan dengan tepat di mana poinmu bocor, dan memberikan daftar perbaikan yang diurutkan berdasarkan dampak. Jalankan sebelum pembeli, klien, atau reviewer menjalankan versi mereka.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)
![Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)
![Mode](https://img.shields.io/badge/mode-read--only-orange)
![Price](https://img.shields.io/badge/price-free-brightgreen)

## Masalah yang diselesaikan skill ini

Kebanyakan repo gagal bukan karena fiturnya. Mereka gagal karena hygiene yang tidak pernah dicek: tidak ada test, tidak ada CI, lockfile yang tidak pernah ter-commit, `.env.example` yang diam-diam sudah tidak cocok dengan kode, riwayat berisi empat commit raksasa. Dari dalam proyek, semua itu tidak terlihat, karena kamu sudah tahu cara kerja semuanya.

Sementara itu, pihak yang menilai kodemu dari luar, pembeli data training AI, klien, reviewer teknis, menilai persis hal-hal tersebut. Laporan mereka blak-blakan, dan ketika kamu membacanya, kesan pertama sudah terlanjur terbentuk.

Repo Health Audit memberimu skor dari luar itu lebih dulu, di mesinmu sendiri, selagi temuannya masih bisa kamu perbaiki.

## Yang kamu dapatkan

Setiap audit menghasilkan satu laporan berisi empat bagian:

1. **Skor total dan grade** dari 0 sampai 100, dengan kalibrasi bahwa 70 adalah garis di mana pembeli yang serius mulai memperhatikan.
2. **Skor delapan dimensi**, masing-masing didukung bukti terukur, bukan kesan.
3. **Lima sinyal buyer-fit** (builds and tests at HEAD, task capacity, genuine history, self-contained, not a demo) yang ditandai pass, warn, atau fail.
4. **Daftar perbaikan urut dampak skor**, jadi kamu selalu tahu perbaikan mana yang membeli poin terbanyak per jam kerja.

### Contoh run asli

Ini hasil tanpa edit dari repository publik nyata, dihasilkan skill ini saat berjalan di dalam DeepSeek Harness:

```text
Repo Health Audit: prompt-brew
Overall Score: 39.9 / 100    Grade: F

D Architecture and Robustness    51
B Test Coverage                   0
K History and Maintenance        40
F Docs and Onboarding            50
C Code Cleanliness               48
I Security Hygiene               78
E Dependency Health              70
H CI/CD Maturity                  0

Top fix: add a Vitest test suite (largest single gain, in Test Coverage)
```

Kejam? Iya. Berguna? Langsung. Setiap kelemahan disebutkan namanya, diukur, dan dipasangkan dengan perbaikan konkretnya. Cross-check: scanner yang sama, dijalankan di bawah Muse pada repository yang sama, mengembalikan metrics yang identik, dan kedelapan skor dimensi di atas bila dihitung dengan bobot rubric-nya berjumlah tepat 39,9. Rubric-nya tidak bergeser antar run dan antar agent.

## Cara kerjanya

Dua lapis, arsitektur yang sama dengan yang dipakai layanan penilaian profesional:

1. **Scanner mekanis** (`scripts/audit_repo.py`) mengukur apa yang bisa dihitung: LOC, rasio test, keberadaan CI, lockfile, kedisiplinan versi, celah dokumentasi env, god file, pola secret, dan bentuk riwayat git kamu. Hasilnya JSON. Hanya memakai Python standard library, nol dependency yang perlu diinstal.
2. **Judgment pass** oleh agent kamu, yang membaca rubric dan kodenya untuk menimbang apa yang tidak bisa ditimbang scanner: layering, penanganan error, kualitas logging, dan apakah test benar-benar menguji perilaku nyata. Setiap penilaian mengutip bukti di level file.

Pengukuran dulu, opini kemudian, dan keduanya tidak pernah dicampur.

## Delapan dimensi

| Kode | Dimensi | Bobot |
| --- | --- | --- |
| D | Architecture and Robustness | 0.18 |
| B | Test Coverage | 0.18 |
| K | History and Maintenance | 0.14 |
| F | Docs and Onboarding | 0.12 |
| C | Code Cleanliness | 0.12 |
| I | Security Hygiene | 0.10 |
| E | Dependency Health | 0.08 |
| H | CI/CD Maturity | 0.08 |

Band penilaian ada di `references/rubric.md`. Inventaris variabel lengkap di balik rubric, yang diekstrak dari laporan skor pembeli nyata yang diterbitkan (penilaian DataFactor adalah model referensinya, di-reverse-engineer dari dua laporan asli pada Oktober 2026), ada di `references/datafactor-variables.md`.

## Kenapa yang disimpan skornya, bukan cuma laporannya

- **Ini cermin, bukan vonis.** Jalankan ulang setelah perbaikan dan deltanya menunjukkan apakah pekerjaanmu benar-benar menggerakkan repo, atau cuma membuatnya lebih panjang.
- **Kodemu tidak pernah meninggalkan mesinmu.** Audit berjalan lokal dan read-only. Temuan secret dilaporkan sebagai path file dan jumlah hit, tidak pernah sebagai nilainya.
- **Tanpa lock-in, tanpa akun, tanpa token.** Kalau nanti kamu memilih mengirim repo ke penilai pihak ketiga, itu keputusanmu, dengan token scoped yang kamu hapus setelahnya (lihat catatan privasi di bawah).
- **Bekerja di tempat kamu sudah bekerja.** Satu paket, varian untuk setiap agent host utama, scripts dan references yang sama untuk semuanya.

## Terverifikasi di

- **Muse**: dibangun dan diuji di sini, dapat ditemukan sebagai skill native.
- **DeepSeek Harness (dsh)**: diinstal dari paket yang persis ini dan terverifikasi live pada Oktober 2026. Laporan prompt-brew-nya memakai metrics yang identik dengan run scanner sisi Muse pada repository yang sama, dan skor dimensinya rekonsiliasi dengan bobot rubric sampai ke desimal.

Paket juga tersedia untuk Gemini CLI dan Antigravity, Codex, Claude Code, dan ChatGPT (lihat Instalasi).

## Tata letak

- `SKILL.md` di root adalah format agent-skills standar (frontmatter YAML), dipakai oleh Gemini CLI dan Antigravity, Codex, DeepSeek Harness (dsh), Claude Code, dan agent kompatibel lainnya.
- `scripts/` dan `references/` dipakai bersama oleh semua varian.
- `claude/` berisi varian Muse: `SKILL.md` tanpa frontmatter plus descriptor `skill.yaml` yang dipakai Muse.
- `chatgpt/` berisi instruksi siap tempel untuk Custom GPT atau Project, dengan dua file dari `references/` diunggah sebagai knowledge.

## Instalasi

Clone repository ini dulu, lalu jalankan blok untuk platform kamu:

```bash
git clone https://github.com/nalakara/repo-health-audit.git
cd repo-health-audit
```

Gemini CLI dan Antigravity:

```bash
mkdir -p ~/.gemini/config/skills/repo-health-audit
cp SKILL.md ~/.gemini/config/skills/repo-health-audit/
cp -r scripts references ~/.gemini/config/skills/repo-health-audit/
```

Codex:

```bash
mkdir -p ~/.codex/skills/repo-health-audit
cp SKILL.md ~/.codex/skills/repo-health-audit/
cp -r scripts references ~/.codex/skills/repo-health-audit/
```

DeepSeek Harness (dsh) dan konsumen `.agents` lainnya:

```bash
mkdir -p ~/.agents/skills/repo-health-audit
cp SKILL.md ~/.agents/skills/repo-health-audit/
cp -r scripts references ~/.agents/skills/repo-health-audit/
```

Claude Code:

```bash
mkdir -p ~/.claude/skills/repo-health-audit
cp SKILL.md ~/.claude/skills/repo-health-audit/
cp -r scripts references ~/.claude/skills/repo-health-audit/
```

Muse:

```bash
mkdir -p ~/workspace/custom-skills/repo-health-audit
cp claude/SKILL.md claude/skill.yaml ~/workspace/custom-skills/repo-health-audit/
cp -r scripts references ~/workspace/custom-skills/repo-health-audit/
```

ChatGPT tidak punya jalur terminal: tempel `chatgpt/INSTRUCTIONS.md` ke Custom GPT atau Project dan unggah dua file dari `references/` sebagai knowledge.

## Penggunaan

Minta agent kamu mengaudit sebuah repository, berdasarkan path lokal atau URL GitHub:

> Audit repo ini: https://github.com/kamu/repo-kamu

Scanner-nya hanya butuh Python 3.11 atau lebih baru dan git, tidak ada yang lain. Setelah itu ambil daftar perbaikan dari urutan teratas, landaskan setiap perbaikan sebagai satu commit kecil tersendiri, lalu audit lagi. Melihat satu repo naik dari 30-an melewati 70, satu perbaikan terverifikasi setiap kalinya, itulah inti permainannya.

## Catatan kalibrasi

Bobot dan band adalah kalibrasi independen yang dicocokkan ke dua laporan referensi (skor 39,6 dan 33). Harapkan kecocokan kisaran dengan penilai eksternal mana pun, bukan kecocokan persis. Tren skor sebuah repository dari run ke run yang berulang adalah sinyal yang penting. Skill ini adalah cermin evaluasi diri, bukan valuasi lisensi dan bukan janji bahwa pembeli mana pun akan membayar kodemu.

## Catatan privasi

Jika layanan penilaian pihak ketiga meminta token GitHub, gunakan fine-grained token yang di-scope hanya ke repository terpilih, dengan masa berlaku terpendek yang ditawarkan, dan hapus token itu segera setelah penilaian selesai. Jangan pernah memberikan akses all-repositories hanya demi sebuah skor.

## Mulai sekarang

Pilih repo yang paling tidak kamu banggakan. Justru untuk repo seperti itulah skill ini dibuat. Audit repo itu, perbaiki item teratasnya, audit lagi. Kalau skornya membantumu melihat kodemu sendiri sebagaimana pembeli melihatnya, sebuah star membantu developer berikutnya menemukannya.
