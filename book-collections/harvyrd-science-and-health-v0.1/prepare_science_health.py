from pathlib import Path
import re,json
P=Path('/workspace/science-health-book');s=(P/'sources/science_health_gutenberg3458.txt').read_text(encoding='utf-8-sig')
markers=list(re.finditer(r'(?m)^([ivxlcdm]+|\d+):1\s+',s));pages={}
for i,m in enumerate(markers):pages[m.group(1)]=pages.get(m.group(1),'')+s[m.start():markers[i+1].start() if i+1<len(markers) else s.find('*** END OF THE PROJECT GUTENBERG',m.start())]
plan=[
(1,'Предисловие: замысел духовного чтения',['vi','vii']),
(2,'Молитва и внутренний ответ',list(range(1,5))),
(3,'Тишина и молитва Господня',list(range(15,18))),
(4,'Искупление и пример Христа',list(range(18,24))),
(5,'Причастие и следование',list(range(32,36))),
(6,'Брак и достоинство женщины',list(range(57,65))),
(7,'Христианская наука и спиритизм',list(range(70,77))),
(8,'Животный магнетизм и нравственная ответственность',list(range(100,106))),
(9,'Духовное учение перед богословием и медициной',list(range(107,116))),
(10,'Физиология: спор с материальным объяснением',list(range(165,173))),
(11,'Шаги истины и свобода',list(range(201,207))+list(range(224,228))),
(12,'Духовное творение',list(range(255,262))),
(13,'Наука бытия: Бог и человек',list(range(268,276))),
(14,'Ответы на возражения',list(range(341,349))),
(15,'Практика: прощение и учение об исцелении',list(range(362,371))),
(16,'Передача учения и ответственность учителя',list(range(443,450))),
(17,'Вопросы и ответы об основах',list(range(465,478))),
(18,'Бытие как духовное истолкование',list(range(501,508))+list(range(521,525))),
(19,'Апокалипсис и язык глоссария',list(range(558,567))+list(range(579,585))),
(20,'Плоды: вступление и первые три свидетельства',[])]
rows=[]
for n,title,ps in plan:
 keys=list(map(str,ps));assert all(x in pages for x in keys),(n,keys)
 body='\n\n'.join(pages[x] for x in keys)
 if n==20:
  fruit=s[s.rfind('CHAPTER XVIII - FRUITAGE'):]
  headings=list(re.finditer(r'(?m)^[A-Z][A-Z ,;\u2019\x27-]{5,}$',fruit))
  headings=[m for m in headings if m.group().strip() not in ['SOLOMON','FRUITAGE']]
  print('Свидетельства:',[m.group() for m in headings[:4]])
  body=fruit[:headings[4].start()] if headings[0].group().startswith('CHAPTER') else fruit[:headings[3].start()]
 (P/'sources'/f'unit{n:02}_primary.txt').write_text('Источник: https://www.gutenberg.org/cache/epub/3458/pg3458-images.html\nСтраницы электронной копии: '+', '.join(keys)+'\n\n'+body+'\n')
 rows.append({'number':n,'name':title,'pages':keys,'url':'https://www.gutenberg.org/cache/epub/3458/pg3458-images.html'})
for i in range(4):
 text='\n\n'.join((P/'sources'/f'unit{n:02}_primary.txt').read_text() for n in range(i*5+1,i*5+6))
 (P/'sources'/f'part{i+1}_primary.txt').write_text(text)
(P/'reading_plan.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
selected={str(x) for _,_,ps in plan for x in ps}
(P/'sources/coverage.json').write_text(json.dumps({'selected_pages':sorted(selected,key=lambda x:(not x.isdigit(),int(x) if x.isdigit() else x)),'unselected_numeric_pages':[int(x) for x in pages if x.isdigit() and x not in selected],'note':'Граница заявленного чтения — указанные страницы, а не весь текст. Сохранённая полная копия не означает полного исследования. Римская пагинация предисловия относится именно к этой электронной копии.'},ensure_ascii=False,indent=2)+'\n')
print('Групп:',len(rows),'выбрано страниц:',len(selected),'всего пронумерованных страниц:',len(pages))
