"""Региональные версии: python tools/regions.py (макет) или --domain ДОМЕН --regions belgorod kursk."""
import argparse
import re
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REGIONS = {
    'belgorod': ('Белгород','в Белгороде','Белгородской области', [('stary-oskol','Старый Оскол','в Старом Осколе'),('gubkin','Губкин','в Губкине')]),
    'kursk': ('Курск','в Курске','Курской области',[('zheleznogorsk','Железногорск','в Железногорске'),('kurchatov','Курчатов','в Курчатове')]),
    'bryansk': ('Брянск','в Брянске','Брянской области',[('klintsy','Клинцы','в Клинцах'),('novozybkov','Новозыбков','в Новозыбкове')]),
    'donetsk': ('Донецк','в Донецке','ДНР',[('makeevka','Макеевка','в Макеевке'),('gorlovka','Горловка','в Горловке'),('volnovakha','Волноваха','в Волновахе')]),
    'mariupol': ('Мариуполь','в Мариуполе','Мариуполя',[]),
    'lugansk': ('Луганск','в Луганске','ЛНР',[('alchevsk','Алчевск','в Алчевске'),('severodonetsk','Северодонецк','в Северодонецке')]),
    'zaporozhye': ('Запорожье','в Запорожье','Запорожской области',[('melitopol','Мелитополь','в Мелитополе'),('berdyansk','Бердянск','в Бердянске'),('energodar','Энергодар','в Энергодаре')]),
    'kherson': ('Херсон','в Херсоне','Херсонской области',[('genichesk','Геническ','в Геническе'),('skadovsk','Скадовск','в Скадовске')]),
}
args = argparse.ArgumentParser(description=__doc__)
args.add_argument('--domain')
args.add_argument('--regions', nargs='+', choices=REGIONS)
args.add_argument('--output',type=Path,help='Каталог сборки поддоменов')
opt = args.parse_args()
domain = opt.domain
if domain and (not re.fullmatch(r'[a-z0-9-]+(?:\.[a-z0-9-]+)+',domain) or not opt.regions or 'belgorod' not in opt.regions):
    args.error('Укажите домен в ASCII и подтверждённые регионы, включая belgorod.')
active = opt.regions or list(REGIONS)
def base(key):
    if domain:
        return 'https://' + ('' if key=='belgorod' else key+'.') + domain
    return '/regiony/'+key

def link(url,label):
    return f'<a href="{url}">{label}</a>'

selector = '<details class="region-picker"><summary>Выбрать регион</summary><div>'
for key in active:
    city,_,area,towns = REGIONS[key]
    selector += '<p>'+link(base(key)+'/', city)+'<br>'+ ' · '.join(link(base(key)+'/'+slug+'/',name) for slug,name,_ in towns)+'</p>'
selector += '</div></details>'
def place_selector(page, label):
    marker='<div class="top"><div class="container">'
    page=re.sub(r'(<div class="top"><div class="container">)<span>Строительная лаборатория · [^<]*</span>',r'\1',page)
    control=selector.replace('<summary>Выбрать регион</summary>', '<summary aria-label="Выбрать город, сейчас '+label+'">'+label+'</summary>')
    return page.replace(marker,marker+control,1)

def read(p):
    return p.read_text(encoding='utf-8')
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(s,encoding='utf-8')
sections=['uslugi','poleznoe','obekty','dopusk','kontakty','politika']
sources=[ROOT/'index.html']+[p for section in sections for p in (ROOT/section).rglob('index.html')]
template=read(ROOT/'uslugi/beton/index.html')
for key in active:
    city,prep,area,towns=REGIONS[key]
    out=((opt.output or ROOT/'region-build') if domain else ROOT/'regiony')/key
    urls=[]
    def render(route,s):
        url=base(key)+route
        s=re.sub(r'<details class="region-picker">.*?</details>', '',s,flags=re.S)
        s=s.replace('Строительная лаборатория · Белгород','Строительная лаборатория · '+city)
        if not domain:
            s=s.replace('href="/uslugi/',f'href="{base(key)}/uslugi/').replace('href="/kontakty/',f'href="{base(key)}/kontakty/').replace('href="/"',f'href="{base(key)}/"')
        if domain:
            for region in active:
                s=s.replace('/regiony/'+region+'/',base(region)+'/')
            s=re.sub(r'<a href="/regiony/[^"]+/">([^<]+)</a>',r'\1',s)
        selected=next((name for slug,name,_ in towns if route=='/'+slug+'/'),city)
        s=place_selector(s,selected)
        head=(f'<link rel="canonical" href="{url}">' if domain else '<meta name="robots" content="noindex, follow">')
        write(out/route.strip('/')/'index.html',s.replace('</head>',head+'\n</head>'))
        urls.append(url)
    def landing(route,name,where):
        title='Строительная лаборатория '+where
        description=f'Запрос по объекту {where}. Перечень направлений испытаний и контакты лаборатории в Белгороде.'
        if key=='belgorod' and not route.strip('/'):
            body=read(ROOT/'index.html')
            body=body.replace('Строительная лаборатория<br>и экспертиза','Строительная лаборатория в Белгороде')
        else:
            body=template
            intro=f'Для согласования работ на объекте {where} укажите адрес площадки, вид испытаний, объём и планируемую дату. Возможность выезда и условия передачи образцов уточняются по заявке.'
            catalog=read(ROOT/'uslugi/index.html').split('<div id="services-list" class="grid">',1)[1].split('</section>',1)[0]
            main=f'<main id="main"><div class="pagehead"><div class="container"><h1>{title}</h1><p>{intro}</p></div></div><section><div class="container"><h2>Направления испытаний</h2><div class="grid">{catalog}</section></main>'
            body=re.sub(r'<main.*?</main>',lambda _:main,body,flags=re.S)
        places=' · '.join(link(base(key)+'/'+slug+'/',n) for slug,n,_ in towns)
        logistics=f'<section><div class="container"><h2>Согласование работ для объектов {area}</h2><p>Контакт лаборатории в Белгороде: <a href="tel:+79194305734">+7 (919) 430-57-34</a>. До отправки образцов согласуйте место передачи и маркировку партии.</p><p>{places}</p></div></section>'
        body=body.replace('</main>',logistics+'</main>')
        body=re.sub(r'<title>.*?</title>',f'<title>{title} | СТРОЙЛАБЭКСПЕРТ</title>',body)
        body=re.sub(r'(<meta name="description" content=")[^"]+',lambda m:m[1]+description,body)
        render(route,body)
    landing('/',city,prep)
    for slug,name,where in towns:
        landing('/'+slug+'/',name,where)
    for p in sources[1:]:
        route='/'+p.relative_to(ROOT).parent.as_posix()+'/'
        if not domain and not route.startswith(('/uslugi/','/kontakty/')):
            continue
        s=read(p)
        if route.startswith(('/uslugi/','/kontakty/')):
            s=re.sub(r'(<title>[^<]*?|<h1>[^<]*?) в Белгороде',r'\1',s)
            s=re.sub(r'<h1>(.*?)</h1>',lambda m:'<h1>'+m[1]+' '+prep+'</h1>',s)
            s=s.replace(' | СТРОЙЛАБЭКСПЕРТ</title>',' '+prep+' | СТРОЙЛАБЭКСПЕРТ</title>')
            s=re.sub(r'(<meta name="description" content=")',lambda m:m[1]+f'Для объектов {area}. ',s)
            s=s.replace('Для расчёта по объекту в Белгороде','Для расчёта по объекту '+prep)
            if route=='/kontakty/':
                s=s.replace('Строительная лаборатория.', 'Заявки по региону принимает лаборатория в Белгороде.').replace('<strong>Адрес</strong>','<strong>Адрес лаборатории в Белгороде</strong>')
        render(route,s)
    if domain:
        shutil.copytree(ROOT/'assets',out/'assets',dirs_exist_ok=True)
        xml=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
        for url in urls:
            ET.SubElement(ET.SubElement(xml,'url'),'loc').text=url
        ET.ElementTree(xml).write(out/'sitemap.xml',encoding='utf-8',xml_declaration=True)
        write(out/'robots.txt','User-agent: *\nAllow: /\nSitemap: '+base(key)+'/sitemap.xml\n')
if not domain:
    for p in sources:
        s=re.sub(r'<details class="region-picker">.*?</details>', '',read(p),flags=re.S)
        write(p,place_selector(s,'Белгород'))
print('Региональные версии готовы:', ', '.join(active))
