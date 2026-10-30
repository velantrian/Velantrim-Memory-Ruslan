# Qolasta: книга, которая живёт между рукописью и молитвой — HARVYRÐ v0.1

**Читательский путеводитель по Qolasta.** Полная PDF-редакция — 24 страницы; комплект также включает исходный DOCX, полный Markdown, пять оригинальных PNG-иллюстраций и исходный ZIP иллюстраций.

## Файлы

- `HARVYRD_Qolasta_reader_guide_ru.pdf` — показанная 24-страничная редакция.
- `HARVYRD_Qolasta_reader_guide_ru.docx` — редактируемый документ.
- `HARVYRD_Qolasta_reader_guide_ru.md` — полный текст; относительные ссылки на исходные иллюстрации сохранены.
- `HARVYRD_Qolasta_original_illustrations.zip` — исходный архив пяти авторских PNG.
- `illustrations/` — те же пять оригинальных PNG отдельными файлами.
- `assets/cover-preview.jpg` — облегчённое производное превью; оригинал обложки находится в `illustrations/01-cover.png`.
- `sources.md` и `edition_manifest.json` — библиография, ограничения и машиночитаемые сведения о файлах.
- `notion-parts/` — ZIP_STORED-части, предназначенные для восстановления Notion-копии файлов, превышающих лимит загрузки. Каждая часть меньше 4 MiB.
- `SHA256SUMS` — SHA-256 исходных файлов, иллюстраций, превью и каждой ZIP-части.

## Восстановление больших файлов из ZIP-частей

Имена частей уже содержат исходное имя и порядковый номер `part-001`, `part-002` и далее. Каждый валидный ZIP-архив хранит единственный несжатый элемент `payload.bin`. Скачайте все части нужного файла, не меняя имена, и выполните из корня этой папки:

```bash
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile

for original in (
    'HARVYRD_Qolasta_reader_guide_ru.pdf',
    'HARVYRD_Qolasta_reader_guide_ru.docx',
    'HARVYRD_Qolasta_original_illustrations.zip',
):
    parts = sorted(Path('notion-parts').glob(original + '.part-*.zip'))
    if not parts:
        raise SystemExit(f'No parts found for {original}')
    with open(original + '.restored', 'wb') as out:
        for part in parts:
            with ZipFile(part) as zf:
                out.write(zf.read('payload.bin'))
    print(f'Restored {original} from {len(parts)} ordered ZIP_STORED parts')
PY

sha256sum -c SHA256SUMS
cmp HARVYRD_Qolasta_reader_guide_ru.pdf.restored HARVYRD_Qolasta_reader_guide_ru.pdf
cmp HARVYRD_Qolasta_reader_guide_ru.docx.restored HARVYRD_Qolasta_reader_guide_ru.docx
cmp HARVYRD_Qolasta_original_illustrations.zip.restored HARVYRD_Qolasta_original_illustrations.zip
```

The checksum list covers package originals and part containers, not the README, manifest or checksum file itself. Each reconstructed output's SHA-256 is recorded in `edition_manifest.json` and matches its source.

## Editorial caveats

This is a reader's guide, not a translation or critical edition of the Qolasta and not a ritual manual. It avoids reproducing prayer formulas, reconstructing ritual sequences, or treating an open scan as permission to disclose community-restricted knowledge. Manuscript evidence, editorial choices, community practice and scholarly interpretation are kept distinct. The source set does not prove a single original order across manuscripts or uniform practice in every contemporary community. OCR, catalog, abstract and access limitations are noted in [`sources.md`](sources.md).

The illustrations are original visual metaphors, not photographs of manuscripts or depictions/reconstructions of rites.
