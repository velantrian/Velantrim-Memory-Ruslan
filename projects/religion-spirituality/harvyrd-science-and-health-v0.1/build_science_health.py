from pathlib import Path
from io import BytesIO
import argparse,base64,json,re,html as H,hashlib
from PIL import Image
from bs4 import BeautifulSoup
from fontTools.ttLib import TTFont
from fontTools import subset
from weasyprint import HTML
import markdown

ACTIONS={'OMIT':'За рамкой рассказа','COMPRESS':'Сжато','CONTEXT':'Сохранён контекст','REVIEW':'Требует отдельного решения или сверки','UNREAD':'Не исследовано в этом томе'}
def esc(s):return H.escape(str(s))
def md(s):return markdown.markdown(s)
def build(name):
 p=Path('/workspace')/(name+'-book');cfg=json.loads((p/'book_config.json').read_text());assets=p/'assets'
 parts=[json.loads(f.read_text()) for f in sorted((p/'parts').glob('part*.json'))]
 chapters=[c for b in parts for c in b['chapters']];units=[u for b in parts for u in b['units']]
 assert [int(c['number']) for c in chapters]==list(range(1,cfg['chapter_count']+1))
 assert sorted(int(u['number']) for u in units)==list(range(1,cfg['unit_count']+1))
 for c in chapters:
  assert all(c.get(x) for x in ['title','deck','body','source_refs'])
  assert all(r['url'].startswith('https://') for r in c['source_refs'])
 images={}
 for n in cfg['assets']:
  im=Image.open(assets/(n+'.png')).convert('RGB');im.thumbnail((1800,2400));im.save(assets/(n+'.jpg'),quality=88,optimize=True)
  images[n]='data:image/jpeg;base64,'+base64.b64encode((assets/(n+'.jpg')).read_bytes()).decode()
 style=Path('/workspace/scripture_series_base.css').read_text().replace('ТОРА · ПЯТИКНИЖИЕ',cfg['short_title'].upper()).replace('Ð','D')
 style+='''
 .cover h1{font-size:36pt}.cover-title .subtitle b{font-size:21pt;letter-spacing:.8px}.cover-title{padding:12mm 16mm 10mm}.cover-title .series{margin-bottom:4mm}.cover-title .gold-line{margin:4mm 0}.cover-title .subtitle{margin-bottom:4mm}.cover-title .cover-small{font-size:7.5pt}.front h2{font-size:25pt}.front .prose p:first-child{font-size:11.4pt;line-height:1.6}.front .scope{font-size:8.5pt}.front .scope span{font-size:7.7pt}.cast,.unit-map{break-before:page}.cast-grid{display:grid;grid-template-columns:1fr 1fr;gap:4mm}.cast-card{padding:4mm;border-radius:3mm;background:#e4efea;break-inside:avoid}.cast-card:nth-child(4n+2){background:#eeebf4}.cast-card:nth-child(4n+3){background:#f5ead6}.cast-card:nth-child(4n){background:#e3edf2}.cast-card h3{margin:0 0 2mm;font-size:10.5pt}.cast-card p{font-size:9pt;line-height:1.5;margin:0}.references{font-size:6.7pt;line-height:1.35;padding-top:2mm;margin-top:2mm}.references a{display:inline}.part-label{font-size:7.4pt;line-height:1.4;letter-spacing:.5px}.contents .toc-line{font-size:9.5pt}.unit{padding:0 0 3mm 4mm;border-left:.5mm solid #b6d4cc;margin-bottom:4mm;break-inside:avoid}.unit h3{margin:0 0 2mm;font-size:10.5pt}.unit p{font-size:9.2pt;line-height:1.6;margin:0}.book-omissions + .book-omissions{break-before:auto;padding-top:5mm}.book-omissions h2{font-size:20pt}.omission{font-size:8.5pt;line-height:1.45;margin-bottom:2.5mm;padding-bottom:2mm}.omission p{margin-bottom:1mm}.omission h3{font-size:9.2pt;margin-bottom:1.3mm}.source-entry{break-inside:avoid;font-size:8.5pt;line-height:1.5;margin-bottom:3mm}.source-entry b{font-family:Sans}.source-entry p{margin:1mm 0 0;color:#647b7c}.sources .source-group{columns:1}.chapter .prose{font-size:10.5pt;line-height:1.52}.chapter-top h2{font-size:21pt}.chapter figure img{max-height:82mm;object-fit:contain}.chapter figure{margin-bottom:5mm}.afterword{padding-top:8mm}.afterword h2{font-size:25pt}
 @media screen{.cast,.unit-map{padding-top:35px;margin-top:35px;border-top:1px solid #d9ded5}.cast-card h3,.unit h3{font-size:20px}.cast-card p,.unit p,.source-entry,.omission{font-size:16px}.cast-grid{gap:16px}.cast-card{padding:18px}.references{font-size:12px}.cover-title .subtitle b{font-size:29px}.cover-title .cover-small{font-size:13px}.contents .toc-line{font-size:16px}.part-label{font-size:13px}.front .scope,.front .scope span{font-size:14px}.chapter .prose{font-size:18px;line-height:1.75}.chapter figure img{max-height:none}.chapter-top h2{font-size:34px}.front h2,.afterword h2{font-size:36px}.cover h1{font-size:62px}.sources .source-group{columns:1}}
 @media screen and (max-width:600px){.cast-grid{grid-template-columns:1fr}.cover-title .subtitle b{font-size:25px}.chapter-top h2{font-size:29px}.chapter .prose{font-size:17px}.cover h1{font-size:52px}}
 '''
 style+='\n .cover-title{background:linear-gradient(180deg,#42262bf5,#563337de 74%,#56333785);border-bottom-color:#c8ad8780}.cover-small{color:#f1e9df}.cover-art{background:#4a2e30}\n .chapter .prose{line-height:1.48}.chapter .prose p{margin-bottom:2.7mm}.chapter figure img{max-height:52mm;object-fit:contain}.chapter figure{margin-bottom:3mm}.chapter-top h2{font-size:20.5pt}.chapter .prose p:first-child:first-letter{color:#966d5a}.deck{color:#7b6c6f}.chapter-number{color:#d8c1b3}\n .cast-card{background:#eee5dc}.cast-card:nth-child(4n+2){background:#e7ede5}.cast-card:nth-child(4n+3){background:#f2e8d5}.cast-card:nth-child(4n){background:#ece5e8}.front .scope{background:linear-gradient(110deg,#f1e5da,#e7eee4);border-left-color:#ac8973}\n @media print{.page-wash{background:radial-gradient(ellipse at 0% 8%,rgba(196,143,120,.12),transparent 62%),radial-gradient(ellipse at 100% 92%,rgba(145,168,141,.11),transparent 62%),linear-gradient(135deg,#fffaf2,#fbf7f0 48%,#f2f5ed)}.contents .toc-line{margin-bottom:1.1mm;padding-bottom:1.1mm;font-size:9pt}.contents .part-label{margin:3.2mm 0 2.1mm}.contents h2{font-size:22pt;margin-bottom:4mm}.unit{padding-bottom:1.5mm;margin-bottom:2.5mm}.unit p{font-size:8.8pt;line-height:1.42}.unit h3{font-size:10pt;margin-bottom:1.3mm}.book-omissions h2{font-size:18pt}.book-omissions + .book-omissions{padding-top:3mm}.omission{font-size:8.1pt;line-height:1.32;margin-bottom:1mm;padding-bottom:.8mm}.omission p{margin-bottom:.7mm}.omission h3{font-size:8.8pt;margin-bottom:1mm}.limits{font-size:8.8pt;line-height:1.48}}\n @media screen{body{background:radial-gradient(ellipse at 0% 0%,rgba(196,143,120,.12),transparent 62%),radial-gradient(ellipse at 100% 100%,rgba(145,168,141,.11),transparent 62%),linear-gradient(135deg,#fffaf2,#fbf7f0 48%,#f2f5ed);background-size:100% 1050px;background-repeat:repeat-y}.chapter .prose{font-size:18px;line-height:1.75}.chapter figure img{max-height:none}.chapter-top h2{font-size:34px}}\n'
 style+='\n .comparison{break-before:page;font-size:10.3pt;line-height:1.6}.comparison h2{font-size:25pt}.cover-title{background:linear-gradient(180deg,#173832f5,#244b42dc 74%,#244b4280)}.chapter-top h2,.front h2,.contents h2,.cast h2,.afterword h2,.comparison h2{color:#234b40}.deck{color:#687d72}.chapter-number{color:#c7d8cb}.chapter .prose p:first-child:first-letter{color:#a67152}.front .scope{background:linear-gradient(110deg,#e7eee4,#f2e7d9);border-left-color:#a7b59a} @media print{.page-wash{background:radial-gradient(ellipse at 0% 8%,rgba(114,163,139,.12),transparent 62%),radial-gradient(ellipse at 100% 92%,rgba(201,145,111,.1),transparent 62%),linear-gradient(135deg,#fffaf2,#f9f7ed 48%,#f0f5ee)}} @media screen{.comparison{padding-top:35px;margin-top:35px;border-top:1px solid #d9ded5;font-size:18px}.comparison h2{font-size:34px}body{background:radial-gradient(ellipse at 0% 0%,rgba(114,163,139,.12),transparent 62%),radial-gradient(ellipse at 100% 100%,rgba(201,145,111,.1),transparent 62%),linear-gradient(135deg,#fffaf2,#f9f7ed 48%,#f0f5ee);background-size:100% 1050px;background-repeat:repeat-y}}\n'
 style+='\n .cover-title{background:linear-gradient(180deg,#183b48f5,#245064de 74%,#24506470)}.chapter-top h2,.front h2,.contents h2,.cast h2,.afterword h2{color:#214b5c}.deck{color:#6d7e83}.chapter-number{color:#cad9d8}.chapter .prose p:first-child:first-letter{color:#a97b50}.front .scope{background:linear-gradient(110deg,#e5efef,#f4e8d7);border-left-color:#9dafb1} @media print{.page-wash{background:radial-gradient(ellipse at 0% 8%,rgba(106,160,174,.13),transparent 62%),radial-gradient(ellipse at 100% 92%,rgba(215,172,112,.12),transparent 62%),linear-gradient(135deg,#fffaf0,#fbf8ef 48%,#eff5f4)}} @media screen{body{background:radial-gradient(ellipse at 0% 0%,rgba(106,160,174,.13),transparent 62%),radial-gradient(ellipse at 100% 100%,rgba(215,172,112,.12),transparent 62%),linear-gradient(135deg,#fffaf0,#fbf8ef 48%,#eff5f4);background-size:100% 1050px;background-repeat:repeat-y}}\n'
 style+='\n .cover-title{background:linear-gradient(180deg,#302e48f5,#4d405adf 74%,#4d405a75)}.chapter-top h2,.front h2,.contents h2,.cast h2,.afterword h2{color:#4d4059}.deck{color:#82747e}.chapter-number{color:#d9cedc}.chapter .prose p:first-child:first-letter{color:#a57d55}.front .scope{background:linear-gradient(110deg,#eee7f0,#f3eadb);border-left-color:#b4a1bb}.cast-card{background:#eee7ec}.cast-card:nth-child(4n+2){background:#e7ede5}.cast-card:nth-child(4n+3){background:#f3eadb}.cast-card:nth-child(4n){background:#e8e8f0} @media print{.page-wash{background:radial-gradient(ellipse at 0% 8%,rgba(155,132,173,.12),transparent 62%),radial-gradient(ellipse at 100% 92%,rgba(207,165,107,.12),transparent 62%),linear-gradient(135deg,#fffaf2,#faf6f0 48%,#f3eff6)}} @media screen{body{background:radial-gradient(ellipse at 0% 0%,rgba(155,132,173,.12),transparent 62%),radial-gradient(ellipse at 100% 100%,rgba(207,165,107,.12),transparent 62%),linear-gradient(135deg,#fffaf2,#faf6f0 48%,#f3eff6);background-size:100% 1050px;background-repeat:repeat-y}}\n'
 style+=' .cover-title{background:linear-gradient(180deg,#173b35f7,#2d5349e8 74%,#2d534980)}.cover-art{object-fit:contain;background:#193b34}.chapter-top h2,.front h2,.contents h2,.cast h2,.afterword h2{color:#31584e}.deck{color:#72847c}.chapter-number{color:#ccdcd4}.chapter .prose p:first-child:first-letter{color:#ad9068}.front .scope{background:linear-gradient(110deg,#e7efea,#f5edde);border-left-color:#a6bbaf}.cast-card{background:#e8eeea}.cast-card:nth-child(4n+2){background:#eee9e0}.cast-card:nth-child(4n+3){background:#f3eddf}.cast-card:nth-child(4n){background:#e8eeee} @media print{.page-wash{background:radial-gradient(ellipse at 0% 8%,rgba(119,163,145,.12),transparent 62%),radial-gradient(ellipse at 100% 92%,rgba(207,177,133,.12),transparent 62%),linear-gradient(135deg,#fffcf5,#f9f8ef 48%,#edf4ef)}} @media screen{body{background:radial-gradient(ellipse at 0% 0%,rgba(119,163,145,.12),transparent 62%),radial-gradient(ellipse at 100% 100%,rgba(207,177,133,.12),transparent 62%),linear-gradient(135deg,#fffcf5,#f9f8ef 48%,#edf4ef);background-size:100% 1050px;background-repeat:repeat-y}}'
 style+=' .cover-title{background:linear-gradient(180deg,#263b52f7,#36556ee8 74%,#36556e88)}.cover-art{background:#283f52}.cover-title .subtitle b{font-size:19pt}.chapter-top h2,.front h2,.contents h2,.cast h2,.afterword h2{color:#355975}.deck{color:#788797}.chapter-number{color:#ccd9e3}.chapter .prose p:first-child:first-letter{color:#bb906b}.front .scope{background:linear-gradient(110deg,#e8eef5,#f7e9db);border-left-color:#aec0d0}.cast-card{background:#e8edf3}.cast-card:nth-child(4n+2){background:#f3e9df}.cast-card:nth-child(4n+3){background:#eeedf1}.cast-card:nth-child(4n){background:#e9efeb} @media print{.page-wash{background:radial-gradient(ellipse at 0% 8%,rgba(125,157,192,.12),transparent 62%),radial-gradient(ellipse at 100% 92%,rgba(221,171,130,.12),transparent 62%),linear-gradient(135deg,#fffaf3,#faf8f2 48%,#eff3f8)}} @media screen{body{background:radial-gradient(ellipse at 0% 0%,rgba(125,157,192,.12),transparent 62%),radial-gradient(ellipse at 100% 100%,rgba(221,171,130,.12),transparent 62%),linear-gradient(135deg,#fffaf3,#faf8f2 48%,#eff3f8);background-size:100% 1050px;background-repeat:repeat-y}.cover-title .subtitle b{font-size:29px}}'
 cover=f'''<header class="cover"><img class="cover-art" src="{images['cover']}" alt="{esc(cfg['cover_alt'])}"><div class="cover-title"><div class="series">H A R V Y R D</div><h1>Суть<br>писаний</h1><div class="gold-line"></div><p class="subtitle"><b>{esc(cfg['short_title'].upper())}</b><br>{esc(cfg['subtitle'])}</p><p class="cover-small">{esc(cfg['cover_line'])}<br>Иллюстрированное чтение избранных смыслов · Черновик v0.1</p></div></header>'''
 front=f'''<section class="front"><div class="eyebrow">Перед чтением</div><h2>{esc(cfg['intro_title'])}</h2><div class="prose">{md(cfg['intro'])}</div><aside class="scope"><b>{esc(cfg['scope_title'])}</b><p>{esc(cfg['scope_body'])}</p><span>Полный черновик нашей сборки — не полный текст оригинала и не построчный аудит.</span></aside></section>'''
 cast='<section class="cast"><div class="eyebrow">Короткая опора для чтения</div><h2>'+esc(cfg['cast_title'])+'</h2><div class="cast-grid">'+''.join(f'<div class="cast-card"><h3>{esc(t)}</h3><p>{esc(s)}</p></div>' for t,s in cfg['cast'])+'</div></section>'
 toc=[]
 for start in range(0,len(chapters),20):
  subset_chapters=chapters[start:start+20];nums={int(c['number']) for c in subset_chapters};lines=[]
  for b in parts:
   cs=[c for c in b['chapters'] if int(c['number']) in nums]
   if cs:
    lines.append(f'<div class="part-label">Часть {b["part"]}. {esc(b["part_title"])}</div>')
    lines.extend(f'<a class="toc-line" href="#chapter-{c["number"]}"><span>{c["number"]}</span><b>{esc(c["title"])}</b></a>' for c in cs)
  toc.append('<section class="contents"><div class="eyebrow">Маршрут чтения</div><h2>'+esc(cfg['toc_title'])+'</h2>'+''.join(lines)+'</section>')
 body=[]
 for b in parts:
  for c in b['chapters']:
   n=c['number'];art=''
   if n in cfg['artmap']:
    asset,caption=cfg['artmap'][n];art=f'<figure><img src="{images[asset]}" alt="{esc(caption)}"><figcaption>{esc(caption)} · символическая иллюстрация</figcaption></figure>'
   refs=' · '.join(f'<a href="{esc(r["url"])}">{esc(r["label"])}</a>' for r in c['source_refs'])
   body.append(f'<article class="chapter" id="chapter-{n}"><div class="chapter-top"><div class="chapter-number">{esc(n)}</div><div class="eyebrow">Часть {b["part"]} · {esc(cfg["short_title"])}</div><h2>{esc(c["title"])}</h2><p class="deck">{esc(c["deck"])}</p></div>{art}<div class="prose">{md(c["body"])}</div><div class="references">Опорные места: {refs} · <a href="#omissions-{b["part"]}">Отбор и сокращения</a></div></article>')
 maps=[]
 map_group=10
 for start in range(0,len(units),map_group):
  rows=''.join(f'<div class="unit"><h3>{int(u["number"]):02}. {esc(u["name"])}</h3><p>{esc(u["coverage"])}</p></div>' for u in units[start:start+map_group])
  maps.append('<section class="unit-map"><div class="eyebrow">Что представлено из оригинала</div><h2>Карта выбранных текстов</h2>'+rows+'</section>')
 omissions=[]
 for b in parts:
  rows=[]
  for o in b['omissions']:
   assert o['action'] in ACTIONS
   rows.append(f'<div class="omission"><div class="action">{esc(ACTIONS[o["action"]])} · {esc(o["category"])}</div><h3><a href="{esc(o["url"])}">{esc(o["passage"])}</a></h3><p>{esc(o["reason"])}</p><p class="context">{esc(o["retained_context"])}</p></div>')
  omissions.append(f'<section class="book-omissions" id="omissions-{b["part"]}"><div class="eyebrow">Что сжато и что оставлено за рамкой</div><h2>Часть {b["part"]}. {esc(b["part_title"])}</h2>'+''.join(rows)+'</section>')
 sources=[];seen=set()
 for b in parts:
  for r in b['sources']:
   if r['url'] not in seen:sources.append(r);seen.add(r['url'])
 closing=f'<section class="afterword"><div class="eyebrow">Вместо последней точки</div><h2>{esc(cfg["closing_title"])}</h2><div class="prose">{md(cfg["closing"])}</div></section>'
 refs='<section class="sources"><div class="eyebrow">Текстовая основа и действительный объём чтения</div><h2>Вернуться к источнику</h2>'+md(cfg['source_intro'])+'<div class="source-group">'+''.join(f'<div class="source-entry"><b><a href="{esc(r["url"])}">{esc(r["title"])}</a></b><p>{esc(r["read_scope"])}</p></div>' for r in sources)+'</div><p class="edition">HARVYRD · '+esc(cfg['short_title'])+' · '+esc(cfg['subtitle'])+'<br>Полный иллюстрированный черновик v0.1. Для просмотра владельцем. Не опубликовано.</p></section>'
 comparison=''
 if (p/'nihongi_comparison.json').exists():
  nj=json.loads((p/'nihongi_comparison.json').read_text());comparison='<section class="comparison"><div class="eyebrow">Рядом с основным рассказом</div><h2>'+esc(nj['title'])+'</h2><div class="prose">'+''.join(md(x) for x in nj['paragraphs'])+'</div><div class="references">'+ ' · '.join('<a href="'+esc(r['url'])+'">'+esc(r['label'])+'</a>' for r in nj['source_refs'])+'</div></section>'
 content=cover+front+cast+''.join(toc)+''.join(body)+comparison+closing+''.join(maps)+''.join(omissions)+'<section class="limits"><div class="eyebrow">О сокращении и его границах</div><h2>Как читать эту версию</h2>'+md(cfg['limits'])+'</section>'+refs
 charset=''.join(sorted(set(BeautifulSoup(content,'html.parser').get_text()+cfg['short_title'].upper()+''.join(chr(i) for i in range(32,256)))))
 def embed_font(m):
  font=TTFont(m.group(1));opts=subset.Options();opts.layout_features=['*'];ss=subset.Subsetter(options=opts);ss.populate(text=charset);ss.subset(font);out=BytesIO();font.save(out)
  return "url('data:font/ttf;base64,"+base64.b64encode(out.getvalue()).decode()+"')"
 style=re.sub(r"url\('(/usr/share/fonts/[^']+)'\)",embed_font,style)
 out='<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HARVYRD · '+esc(cfg['short_title'])+' · '+esc(cfg['subtitle'])+'</title><style>'+style+'</style></head><body><div class="page-wash" aria-hidden="true"></div>'+content+'</body></html>'
 prefix=cfg['file_prefix'];htmlfile=p/(prefix+'_v0.1_Illustrated.html');pdffile=p/(prefix+'_v0.1_Illustrated.pdf');textfile=p/(prefix+'_v0.1_Full_Text.md')
 htmlfile.write_text(out);HTML(string=out,base_url=str(p)).write_pdf(pdffile)
 text=['# HARVYRD — Суть писаний','# '+cfg['short_title']+': '+cfg['subtitle'],'Полный черновик авторского чтения избранных смыслов v0.1. Не полный текст оригинала. Не опубликовано.','## '+cfg['intro_title'],cfg['intro'],'### '+cfg['scope_title'],cfg['scope_body'],'## '+cfg['cast_title']]
 for t,s in cfg['cast']:text.extend(['### '+t,s])
 for b in parts:
  text.append('# Часть '+str(b['part'])+'. '+b['part_title'])
  for c in b['chapters']:text.extend(['## '+c['number']+'. '+c['title'],c['deck'],c['body'],'Опорные места: '+' · '.join(f'[{r["label"]}]({r["url"]})' for r in c['source_refs'])])
 if (p/'nihongi_comparison.json').exists():
  text.extend(['# '+nj['title'],*nj['paragraphs'],'Опорные места: '+' · '.join(f'[{r["label"]}]({r["url"]})' for r in nj['source_refs'])])
 text.extend(['## '+cfg['closing_title'],cfg['closing'],'# Карта выбранных текстов'])
 for u in units:text.extend(['## '+str(u['number'])+'. '+u['name'],u['coverage']])
 text.append('# Что сжато и что оставлено за рамкой')
 for b in parts:
  text.append('## Часть '+str(b['part'])+'. '+b['part_title'])
  for o in b['omissions']:text.extend(['### '+o['passage']+' — '+ACTIONS[o['action']],o['reason'],o['retained_context'],f'[Место в источнике]({o["url"]})'])
 text.extend(['# Как читать эту версию',cfg['limits'],'# Источники',cfg['source_intro']])
 for r in sources:text.extend([f'## [{r["title"]}]({r["url"]})',r['read_scope']])
 textfile.write_text('\n\n'.join(text)+'\n')
 count=sum(len(b['omissions']) for b in parts)
 register={'status':'предварительный отбор для согласования владельцем','complete_original_work_register':False,'selected_passage_groups':len(units),'literary_chapters':len(chapters),'records':count,'parts':[{k:b[k] for k in ['part','part_title','units','omissions','sources','caveats']} for b in parts]}
 (p/'selection_register.json').write_text(json.dumps(register,ensure_ascii=False,indent=2)+'\n')
 manifest={'version':'v0.1','title':cfg['short_title'],'literary_chapters':len(chapters),'selected_passage_groups':len(units),'scope':cfg['manifest_scope'],'translation_base':cfg['translation_base'],'english_source_read':True,'early_manuscripts_checked':False,'critical_edition_checked':False,'owner_approved':False,'published_github':False,'published_notion':False,'published_google_docs':False,'new_illustrations':len(images),'selection_records':count,'artifacts':{f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [htmlfile,pdffile,textfile]}}
 (p/'edition_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 visible=BeautifulSoup(out,'html.parser').body.get_text(' ',strip=True)
 for c in chapters:
  for para in BeautifulSoup(md(c['body']),'html.parser').find_all('p'):assert para.get_text(' ',strip=True) in visible
 print(cfg['short_title'],':',len(chapters),'глав,',len(units),'исходных единиц,',count,'записей отбора',flush=True)
 for f in [pdffile,htmlfile,textfile]:print(str(f),f.stat().st_size,flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('books',nargs='*',default=['science-health']);args=parser.parse_args()
 for name in args.books:build(name)
