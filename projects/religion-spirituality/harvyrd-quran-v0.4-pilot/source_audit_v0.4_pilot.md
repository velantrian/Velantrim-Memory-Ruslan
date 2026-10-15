# Отчёт о проверке источников — v0.4 pilot

## Первичный текст и переводы

Для последовательного пилота были открыты арабские страницы Quran.com и русская версия Эльмира Кулиева по 1:1–7 и 2:1–29. Независимая русская версия Османова на Quran-for-all использована для сопоставления этих двух отрывков. По контрольным отрывкам арабский текст и русская версия Кулиева отдельно проверены по прямым страницам каждого заданного аята (включая 49:11–13 по отдельным страницам 11, 12 и 13). Переводческие варианты не сведены к одному эквиваленту там, где они меняют редакционный статус: особенно 2:177 (al-baʾs) и 2:26 (fawqahā). Проверка не является полной колляцией всех русских переводов и не заменяет рецензию арабиста. [8] [9] [10] [11]

Quranic Arabic Corpus использовался как лингвистический и морфологический справочник для отдельных терминов и неоднозначных мест. Это источник разметки и переводческих сопоставлений, а не единственный авторитетный тафсир. [11]

## Контекст и толкования

Шесть control dossiers используют в дополнение к арабскому тексту названные страницы тафсира и лексико-грамматические источники; каждая ссылка перечислена в листе `Control cases` и файле `control_verse_dossiers_v0.4_pilot.md`. Переданный workflow-результат сохраняет варианты чтения и источники. Тафсирный исторический рассказ в 49:6 помечен как традиционное сообщение, а не независимо проверенный исторический факт. Для 5:32 рядом проверен 5:33 только как граница контекста; 5:33 не включён в контрольный смысл 5:32.

## Правила повторного использования

Quran.com Terms and Conditions ограничивают использование содержимого сайта личными некоммерческими целями. Условия Quran Foundation Developer APIs отдельно запрещают продажу/перераспространение API-контента без письменной коммерческой лицензии. Это не означает, что права на печатную/коммерческую публикацию переводов в этом проекте установлены. В книге не воспроизводятся длинные переводные цитаты: используются авторские парафразы, ссылки и краткие лингвистические метки. Публичное/коммерческое переиздание остаётся не очищенным по правам. [12] [13]

Quranic Arabic Corpus публикует разметку под GNU GPL и требует указания источника и ссылки; здесь используются точечные ссылки, а массив данных не копируется и не распространяется. [14]

Иллюстрации унаследованы из каталога `assets/` версии v0.3 и использованы как художественные изображения, не как исторические документы. Точные исходные промпты, авторство генерации и отдельные лицензии в прежней поставке не документированы. Это ограничение отражено в книге; перед коммерческой печатью нужна проверка происхождения и прав на весь набор.

В PDF встроены шрифты Noto Serif, Noto Sans и Noto Naskh Arabic из локального пакета Debian; пакет сообщает лицензию SIL Open Font License 1.1. Созданный документ не становится объектом лицензии шрифта. [15]

## Предлагаемый псевдоним

Проверены открытые веб-результаты, страницы поиска WorldCat по точным написаниям `Harvyrð` и `Harvyrd`, запросы TMview по точной и упрощённой форме и публичный интерфейс WIPO. Интерфейс TMview позволил отправить запросы, но воспроизводимые итоговые протоколы/юридическое заключение не получены; WIPO остановился на challenge, не позволяющем зафиксировать итог. Это не доказывает отсутствие похожих книг или знаков и не является проверкой юридической уникальности. Статус имени остаётся PROPOSED; перед публичной фиксацией нужны полноценная проверка реестров и решение владельца. Имя Harvyrð не представляется настоящим древнеисландским словом или исторической фамилией. [16] [17]

## Источники

[8]: https://quran.com/al-fatihah "Quran.com, Al-Fatihah"
[9]: https://quran.com/al-baqarah/1-29/translations/quran.ru.kuliev "Quran.com, Al-Baqarah 2:1–29, Arabic and Kuliev Russian"
[10]: https://quran-for-all.com/translations/ru_osmanov "Quran-for-all, Osmanov Russian translation"
[11]: https://corpus.quran.com/documentation "Quranic Arabic Corpus documentation"
[12]: https://quran.com/terms-and-conditions "Quran.com Terms and Conditions"
[13]: https://api-docs.quran.foundation/legal/developer-terms/ "Quran Foundation Developer Terms of Service"
[14]: https://corpus.quran.com/download "Quranic Arabic Corpus data and terms of use"
[15]: https://openfontlicense.org/ "SIL Open Font License 1.1"
[16]: https://search.worldcat.org/search?q=Harvyr%C3%B0 "WorldCat exact query: Harvyrð"
[17]: https://search.worldcat.org/search?q=Harvyrd "WorldCat exact query: Harvyrd"
[18]: https://www.britannica.com/topic/Quran "Encyclopaedia Britannica, Quran"
[19]: https://quran.com/al-baqarah/177/translations/quran.ru.kuliev "Quran.com 2:177"
[20]: https://quran.com/an-nisa/135/translations/quran.ru.kuliev "Quran.com 4:135"
[21]: https://quran.com/al-maidah/32/translations/quran.ru.kuliev "Quran.com 5:32"
[22]: https://quran.com/al-maidah/89/translations/quran.ru.kuliev "Quran.com 5:89"
[23]: https://quran.com/al-hujurat/6/translations/quran.ru.kuliev "Quran.com 49:6"
[24]: https://quran.com/al-hujurat/11-13/translations/quran.ru.kuliev "Quran.com 49:11–13"

**Дополнительные прямые источники контрольных случаев:**
- `2_177`: https://quran.com/al-baqarah/177/translations/quran.ru.kuliev; https://quran.com/al-baqarah/177; https://corpus.quran.com/translation.jsp?chapter=2&verse=177; https://corpus.quran.com/wordbyword.jsp?chapter=2&verse=177
- `4_135`: https://quran.com/an-nisa/135/translations/quran.ru.kuliev; https://quran.com/an-nisa/135; https://corpus.quran.com/translation.jsp?chapter=4&verse=135; https://corpus.quran.com/wordbyword.jsp?chapter=4&verse=135
- `5_32`: https://quran.com/al-maidah/32/translations/quran.ru.kuliev; https://quran.com/al-maidah/32; https://corpus.quran.com/translation.jsp?chapter=5&verse=32
- `5_89`: https://quran.com/al-maidah/89/translations/quran.ru.kuliev; https://quran.com/al-maidah/89; https://corpus.quran.com/translation.jsp?chapter=5&verse=89; https://corpus.quran.com/wordbyword.jsp?chapter=5&verse=89
- `49_6`: https://quran.com/al-hujurat/6/translations/quran.ru.kuliev; https://quran.com/al-hujurat/6; https://corpus.quran.com/translation.jsp?chapter=49&verse=6; https://corpus.quran.com/wordbyword.jsp?chapter=49&verse=6
- `49_11_13`: https://quran.com/al-hujurat/11/translations/quran.ru.kuliev; https://quran.com/al-hujurat/12/translations/quran.ru.kuliev; https://quran.com/al-hujurat/13/translations/quran.ru.kuliev; https://quran.com/al-hujurat/11-13

Встроенные источники v0.3 [1]–[7] сохранены вместе с унаследованным текстом. Коммерческое использование переводов и прежних иллюстраций не очищено юридически; отдельное разрешение до печати не установлено.
