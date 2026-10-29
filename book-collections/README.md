# Коллекции книг

Единый раздел внутри репозитория памяти: издания, иллюстрации, индексы, сборочные материалы, происхождение и прямо связанные исследования. Статусы пилотов, ограничения охвата, PROPOSED / NOT RUN и вопросы прав не меняются.

[Подробный индекс HARVYRD](HARVYRD.md) · [Точные соответствия путей и хешей](MIGRATION_MANIFEST.json)

| Коллекция | Файлов исходного комплекта |
|---|---:|
| [cognition-catalogs](cognition-catalogs/) | 14 |
| [encyclopedia-of-cognition-v4.1](encyclopedia-of-cognition-v4.1/) | 6 |
| [harvyrd-advaita-vedanta-v0.1](harvyrd-advaita-vedanta-v0.1/) | 15 |
| [harvyrd-avesta-v0.1](harvyrd-avesta-v0.1/) | 17 |
| [harvyrd-bahai-v0.1](harvyrd-bahai-v0.1/) | 15 |
| [harvyrd-bhagavad-gita-v0.1](harvyrd-bhagavad-gita-v0.1/) | 9 |
| [harvyrd-bible-v0.1-pilot](harvyrd-bible-v0.1-pilot/) | 46 |
| [harvyrd-buddhist-schools-v0.1](harvyrd-buddhist-schools-v0.1/) | 17 |
| [harvyrd-confucian-v0.1](harvyrd-confucian-v0.1/) | 15 |
| [harvyrd-covenants-v0.1](harvyrd-covenants-v0.1/) | 15 |
| [harvyrd-daoism-v0.1](harvyrd-daoism-v0.1/) | 15 |
| [harvyrd-dhammapada-v0.1](harvyrd-dhammapada-v0.1/) | 13 |
| [harvyrd-granth-v0.1](harvyrd-granth-v0.1/) | 13 |
| [harvyrd-jain-v0.1](harvyrd-jain-v0.1/) | 13 |
| [harvyrd-mahabharata-v0.1-pilot](harvyrd-mahabharata-v0.1-pilot/) | 13 |
| [harvyrd-mormon-v0.1](harvyrd-mormon-v0.1/) | 15 |
| [harvyrd-mystical-v0.1](harvyrd-mystical-v0.1/) | 19 |
| [harvyrd-pearl-v0.1](harvyrd-pearl-v0.1/) | 15 |
| [HARVYRD/harvyrd-i-ching-v0.1](HARVYRD/harvyrd-i-ching-v0.1/) | 81 |
| [harvyrd-quran-v0.4-pilot](harvyrd-quran-v0.4-pilot/) | 45 |
| [harvyrd-ramayana-v0.1](harvyrd-ramayana-v0.1/) | 10 |
| [harvyrd-science-and-health-v0.1](harvyrd-science-and-health-v0.1/) | 55 |
| [harvyrd-shinto-v0.1](harvyrd-shinto-v0.1/) | 15 |
| [harvyrd-stoicism-v1](harvyrd-stoicism-v1/) | 5 |
| [harvyrd-torah-v0.1](harvyrd-torah-v0.1/) | 13 |
| [harvyrd-world-traditions-volume-i](harvyrd-world-traditions-volume-i/) | 3 |
| [harvyrd-world-traditions-volume-ii](harvyrd-world-traditions-volume-ii/) | 3 |
| [harvyrd-world-traditions-volume-iii](harvyrd-world-traditions-volume-iii/) | 8 |
| [harvyrd-world-traditions-volume-iv](harvyrd-world-traditions-volume-iv/) | 13 |
| [harvyrd-world-traditions-volume-v](harvyrd-world-traditions-volume-v/) | 11 |
| [zauchit](zauchit/) | 57 |

Каталоги cognition-catalogs описывают 12 книг, но не содержат 12 полных изданий. Заучит хранит базовую редакцию, expanded и complete-2026-10-19 отдельно; исследовательское досье — в [research-dossier](zauchit/research-dossier/), включая [дополнение о причинной атрибуции источника в мультисенсорном восприятии (29.10.2026)](zauchit/research-dossier/zauchit-multisensory-causal-inference-addendum-2026-10-29-v1.md) и [проект протокола бенчмарка DCA-01—03 (29.10.2026, v1; PROPOSED / NOT RUN)](zauchit/research-dossier/zauchit-delayed-credit-assignment-benchmark-protocol-2026-10-29-v1.md).

Общие QA и исторические storage controls остаются в [Encyclopedia_of_Cognition_Project](../Encyclopedia_of_Cognition_Project/README.md). Неоднозначные исследования и Athene остаются там до решения владельца; музыка — в [media/music](../media/music/README.md).

Датированные манифесты и чеки публикации являются историческими свидетельствами. Их старые пути/хеши не подменены: соответствия исходных и новых байтов зафиксированы в MIGRATION_MANIFEST.json. Исходные экспорты доступны в исходном Git-коммите; исправление URI в перенесённых DOCX/PDF — отдельная явно описанная навигационная производная, не новое издание по содержанию.

## HARVYRÐ — Чжоу и: «Книга перемен»

В [читательском издании v0.1](HARVYRD/harvyrd-i-ching-v0.1/README.md) сохранены PDF, DOCX, полный Markdown, обложка, архив и распакованные исходные иллюстрации, указатель источников, манифест редакции и SHA-256. Книга охватывает все 64 гексаграммы; её исторические ограничения и статус черновой ветки указаны отдельно. В таблице учтён полный комплект из 81 файла.

## Том V: «Лес, клятва и поднятое небо»

Добавлен [том V «Лес, клятва и поднятое небо»](harvyrd-world-traditions-volume-v/README.md): PDF, DOCX, Markdown и четыре иллюстрации в JPG/PNG — **11 исходных файлов** плюс README коллекции. Все 11 файлов — побайтовые копии; оригиналы сохранены. Теперь в разделе **31 коллекция**.

Первоначальные поля и записи MIGRATION_MANIFEST.json описывают историческую миграцию 29 коллекций и не пересчитывались. История исходного копирования отражена отдельно в `local_review_additions`; служебный README не входит в число исходных файлов. Том V опубликован в main после отдельного одобрения владельца; исходный коммит переноса — `d7e028a`.
