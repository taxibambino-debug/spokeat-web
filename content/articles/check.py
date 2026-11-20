import json, re, os, glob, sys
base = '/home/claude/spk/articles'
slugs = json.load(open(f'{base}/slugs.json'))
valid = {'en': {v['en'] for v in slugs.values()}, 'sv': {v['sv'] for v in slugs.values()}}
NEED = ['title', 'meta_title', 'meta_description', 'slug', 'lang', 'alternate', 'article_number', 'main_keyword', 'author', 'reviewer', 'last_reviewed']
rows = []
for lang in ('en', 'sv'):
    for n, v in sorted(slugs.items(), key=lambda x: int(x[0])):
        p = f'{base}/{lang}/{v[lang]}.md'
        r = {'n': int(n), 'lang': lang, 'file': os.path.basename(p), 'problems': []}
        if not os.path.exists(p):
            r['problems'].append('MISSING'); rows.append(r); continue
        t = open(p, encoding='utf-8').read()
        fm = re.match(r'^---\n(.*?)\n---\n', t, re.S)
        if not fm: r['problems'].append('no front matter')
        else:
            keys = set(re.findall(r'^([a-z_]+):', fm.group(1), re.M))
            miss = [k for k in NEED if k not in keys]
            if miss: r['problems'].append('front matter missing ' + ','.join(miss))
            mt = re.search(r'^meta_title:\s*"?(.*?)"?\s*$', fm.group(1), re.M)
            md = re.search(r'^meta_description:\s*"?(.*?)"?\s*$', fm.group(1), re.M)
            if mt and len(mt.group(1)) > 65: r['problems'].append(f'meta_title {len(mt.group(1))} chars')
            if md and len(md.group(1)) > 160: r['problems'].append(f'meta_description {len(md.group(1))} chars')
        body = t[fm.end():] if fm else t
        src_split = re.split(r'\n## (Sources|Källor)\s*\n', body)
        main = src_split[0]
        sources = src_split[2] if len(src_split) > 2 else ''
        if not sources: r['problems'].append('no Sources section')
        src_urls = re.findall(r'https?://[^\s>)\]]+', sources.split('<!-- schema -->')[0])
        r['sources'] = len(set(src_urls))
        words = len(re.findall(r'\w+', re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', main)))
        r['words'] = words
        cites = set(re.findall(r'\(#ref-(\d+)\)', main))
        anchors = set(re.findall(r'id="ref-(\d+)"', sources))
        if cites - anchors: r['problems'].append('citations without source: ' + ','.join(sorted(cites - anchors)))
        if len(cites) == 0: r['problems'].append('no inline citations')
        for l, s in re.findall(r'\]\(/(en|sv)/([a-z0-9-]+)\)', body):
            if s not in valid[l] and s != 'start': r['problems'].append(f'bad internal link /{l}/{s}')
        sch = re.search(r'```json\s*(\{.*?\})\s*```', body, re.S)
        if not sch: r['problems'].append('no schema')
        else:
            try: json.loads(sch.group(1))
            except Exception as e: r['problems'].append('schema JSON invalid')
        if '[AUTHOR NAME]' not in t and 'Ted Scheiman' not in t: r['problems'].append('no author')
        if r['n'] in (39, 40, 41, 47) and not re.search(r'1177|GP|doctor|läkare|psycholog', main, re.I): r['problems'].append('YMYL help missing')
        rows.append(r)
json.dump(rows, open(f'{base}/check.json', 'w'), ensure_ascii=False, indent=1)
done = [r for r in rows if 'MISSING' not in r['problems']]
print(f'{len(done)}/{2*len(slugs)} files present')
for r in rows:
    if r['problems'] and 'MISSING' not in r['problems']:
        print(r['n'], r['lang'], r.get('words'), r.get('sources'), '|', '; '.join(r['problems']))
if done:
    w = [r['words'] for r in done]; s = [r['sources'] for r in done]
    print('words min/median/max', min(w), sorted(w)[len(w)//2], max(w), '| sources min/median', min(s), sorted(s)[len(s)//2])
