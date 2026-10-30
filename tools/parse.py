"""Builds corpus.d parts for Tocantins from the retrieved Assembleia Legislativa PDFs (no network).

    python -X utf8 parse.py list                     # every Lei Complementar, with the reason it is in or out
    python -X utf8 parse.py part <n> <from> <to>     # part n: the selected LCs [from:to], oldest first

Source: www.al.to.leg.br "Legislação Estadual" (tipo complementar), one PDF per Lei Complementar (/arquivo/<id>), as
compiled by the Assembleia's documentation service. Where an act was altered, the compiled PDF prints the earlier and
the later wordings one after the other, each with a small italic note naming the act that gave it, and nothing marks
which one is in force (no strike-through). So only acts that were never altered are taken, as enacted:
- the PDF has a text layer and carries no compilation mark: no red text, no small italic note in the body, no line
  starting with "*", no "Revogada"/"Alterada" line under the title;
- no other Lei Complementar on the list (its ementa or its text) cites it next to a word of alteration or repeal.
Each is dated by its publication in the Diário Oficial do Estado when the record gives the date, otherwise by the
act's own date (Tocantins Leis Complementares take effect on publication, which is printed with the act's date).
"""
import json, re, sys, unicodedata
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from br_lib import units_of, write_part, sha, norm, MONTHS  # noqa: E402

CACHE = HERE / '.cache'
SITE = 'https://www.al.to.leg.br/legislacaoEstadual'
RETRIEVED = '2026-10-30'
# left out after check_letters.py: the independent reader (pdftotext) reads these acts' tables in another order
R = 'left out: a second PDF reader (pdftotext) reads its text (tables, annexes) in a different order'
LEFT_OUT = {32: R, 33: R, 42: R, 52: R, 59: R, 92: R, 100: R, 111: R, 113: R, 125: R, 135: R, 137: R, 148: R, 156: R, 157: R, 163: R, 173: R, 174: R, 176: R}

COUNTRY = {
    'code': 'BR-TO', 'name': 'Tocantins', 'slug': 'brazil-tocantins', 'lang': 'pt', 'tz': 'America/Araguaina',
    'future_branch': 'futuro',
    'publisher': {'name': 'Assembleia Legislativa do Estado do Tocantins (al.to.leg.br)',
                  'email': 'legislacao@al.to.leg.br.invalid'},
    'default_in_force_rule': {
        'text': 'Decreto-Lei 4.657/1942 (LINDB) art. 1: unless it says otherwise, a law takes effect 45 days after its '
                'official publication. Tocantins Leis Complementares almost always say they take effect on the date '
                'of their publication; this record dates each act as enacted by its publication in the Diário Oficial '
                'do Estado.',
        'source': 'https://www.planalto.gov.br/ccivil_03/decreto-lei/del4657compilado.htm'},
    'licence_note': 'Texts: Assembleia Legislativa do Estado do Tocantins, www.al.to.leg.br (Legislação Estadual). '
                    'Lei 9.610/1998 art. 8 IV: the texts of laws and other official acts are not protected by '
                    'copyright. Non-official text: only the Diário Oficial do Estado is authoritative.',
}
DECISIONS = [
    'Only Leis Complementares that were never altered are given, each as enacted, credited to the act itself. The '
    'Assembleia\'s compiled PDFs print an altered provision\'s earlier and later wordings one after the other, each with '
    'a note naming the act that gave it, and do not mark which one is in force; such acts (and the Constituição, compiled '
    'the same way) are left out rather than guessed. An act is taken as never altered when its PDF carries no '
    'compilation mark (no red text, no note in small italics in the body, no line starting with "*", no "Revogada" or '
    '"Alterada" line under the title) and no other Lei Complementar on the Assembleia\'s list cites it, in its ementa or '
    'its text, next to a word of alteration or repeal. Ordinary laws are not checked (a Lei Complementar is altered by '
    'another Lei Complementar). The list shows no record for Leis Complementares nos 50, 119, 122 and 130. Acts whose '
    'text a second PDF reader (pdftotext) reads in a different order (mostly tables in annexes) are left out.',
    'Each act is dated by its publication in the Diário Oficial do Estado where the Assembleia\'s record gives that date '
    '("Publicada no Diário Oficial nº ... de dd/mm/yyyy"), otherwise by the act\'s own date in its title.',
    'One file per Art.; headings stand above the first article under them; "000-titulo" holds the title, the '
    'publication line, the ementa and the enacting formula. Text after the last article (place, date, signatures) stays '
    'with the last article. Wrapped lines are joined; a line that does not reach the right margin ends its paragraph.',
]
AI = ["Claude Code (claude-opus-5-5) wrote Lexifina's code and chose the sources. No model output is used as legal "
      "text or dates: every word comes from the Assembleia Legislativa's PDFs."]

START = re.compile(r'^\s*\*?\s*(Art\.?\s*\d|§|Par[áa]grafo [úu]nico|[IVXLC]+\s*[-–.]\s|[IVXLC]+\s*[-–]$|[a-z]\)\s|\d+[.)]\s'
                   r'|T[ÍI]TULO\b|CAP[ÍI]TULO\b|SE[ÇC][ÃA]O\b|SUBSE[ÇC][ÃA]O\b|LIVRO\b|ANEXO\b)')


def clean(s):
    s = unicodedata.normalize('NFC', s.replace('\xa0', ' ').replace('­', '').replace('\t', ' '))
    return re.sub(r' {2,}', ' ', s).strip()


def pdf_of(rec):
    p = CACHE / 'raw' / sha(f"https://www.al.to.leg.br/arquivo/{rec['id']}".encode())
    return p if p.exists() else None


def read(path):
    """-> (lines, marks). lines: [{'text','x0','x1','page','bold','small'}] in reading order; marks: why it is compiled."""
    d = pymupdf.open(path)
    out, marks = [], []
    for page in d:
        rows = []
        for b in page.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                sp = [s for s in l['spans'] if s['text'].strip()]
                if not sp:
                    continue
                if any(s['color'] == 16711680 for s in sp):
                    marks.append('red text')
                rows.append({'y': l['bbox'][3], 'x0': l['bbox'][0], 'x1': l['bbox'][2], 'spans': l['spans']})
        rows.sort(key=lambda r: (round(r['y']), r['x0']))
        merged = []
        for r in rows:
            if merged and abs(merged[-1]['y'] - r['y']) <= 2:
                merged[-1]['spans'] = merged[-1]['spans'] + [{'text': ' ', 'size': 99, 'font': '', 'flags': 0}] + r['spans']
                merged[-1]['x1'] = max(merged[-1]['x1'], r['x1'])
            else:
                merged.append(dict(r))
        for r in merged:
            sp = [s for s in r['spans'] if s['text'].strip()]
            text = clean(''.join(s['text'] for s in r['spans']))
            small = all(s['size'] < 10.5 for s in sp)
            if small and re.fullmatch(r'\d{1,3}', text):
                continue  # page number
            if small and any('Italic' in s['font'] for s in sp):
                marks.append('note in small italics')
            if text.startswith('*'):
                marks.append('line starting with "*"')
            out.append({'text': text, 'x0': r['x0'], 'x1': r['x1'], 'page': page.number, 'small': small,
                        'bold': all('Bold' in s['font'] for s in sp)})
    return out, sorted(set(marks)), d.page_count


def paragraphs(lines):
    if not lines:
        return []
    xs = sorted(l['x1'] for l in lines if not l['small'])
    right = xs[int(len(xs) * 0.9)] if xs else 0
    out, prev = [], None
    for l in lines:
        t = l['text']
        cont = (prev is not None and prev['x1'] >= right - 25 and not START.match(t) and not prev['small']
                and not l['small'] and prev['page'] == l['page'] or
                (prev is not None and prev['x1'] >= right - 25 and not START.match(t) and l['page'] != prev['page']))
        if cont and out:
            p = out[-1]
            out[-1] = p + t if re.search(r'\w-$', p) and not p.endswith(' -') else p + ' ' + t
        else:
            out.append(t)
        prev = l
    return [norm(p) for p in out if norm(p)]


def num_re(n):
    return rf'(?:Lei\s+Complementar|LC)\s*(?:n[º°o.]*\s*)?0*{n}(?!\d)(?!\s*\.\d)'


ALTER = re.compile(r'(?i)alter|revog|acresc|reda[çc][ãa]o|vigorar|suprim|modific|inclu[ií]|derrog|substitu|renumer')


def main():
    idx = json.loads((CACHE / 'lc-index.json').read_text(encoding='utf-8'))
    have = {r['numero'] for r in idx}
    missing = sorted(set(range(1, max(have) + 1)) - have)
    texts, res = {}, []
    for r in idx:
        p = pdf_of(r)
        if p is None:
            texts[r['id']] = None
            continue
        b = p.read_bytes()
        if not b.startswith(b'%PDF'):
            texts[r['id']] = None
            continue
        lines, marks, pages = read(p)
        texts[r['id']] = (lines, marks, ' '.join(l['text'] for l in lines), b)
    for r in idx:
        t = texts[r['id']]
        if t is None:
            res.append((r, None, 'not fetched or not a PDF'))
            continue
        lines, marks, full, b = t
        if len(re.sub(r'\W', '', full)) < 200:
            res.append((r, None, 'no text layer (scanned)'))
            continue
        head = ' '.join(l['text'] for l in lines[:8])
        if re.search(r'(?i)\b(revogad|alterad|suspens|declarad)', head):
            res.append((r, None, 'compiled: ' + re.search(r'(?i)\b(revogad|alterad|suspens|declarad)\w*', head).group(0) + ' under the title'))
            continue
        if marks:
            res.append((r, None, 'compiled: ' + ', '.join(marks)))
            continue
        cre = re.compile(num_re(r['numero']), re.I)
        hit = None
        for o in idx:
            if o['id'] == r['id'] or (o['ano'], o['numero']) < (r['ano'], r['numero']):
                continue
            ot = texts.get(o['id'])
            src = o['ementa'] + ' ' + (ot[2] if ot else o['snippet'])
            for m in cre.finditer(src):
                win = src[max(0, m.start() - 250):m.end() + 250]
                # LC numbers are unique in Tocantins, so a citation counts whatever year follows it (strict)
                if ALTER.search(win):
                    hit = o
                    break
            if hit:
                break
        if hit:
            res.append((r, None, f'touched by LC {hit["numero"]}/{hit["ano"]}'))
            continue
        if r['numero'] in LEFT_OUT:
            res.append((r, None, LEFT_OUT[r['numero']]))
            continue
        res.append((r, (lines, b), 'in'))
    return idx, res, missing


def date_of(r, lines):
    m = re.search(r'Publicad[ao] no Di[áa]rio Oficial n[º°o]\s*[\d.]+,?\s*de\s*(\d{1,2})/(\d{1,2})/(\d{4})', r['snippet'])
    if m:
        return f'{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}', 'published'
    title = ' '.join(l['text'] for l in lines[:3])
    m = re.search(r'DE\s+(\d{1,2})[º°]?\s+DE\s+([A-ZÇ]+)\s+DE\s+(\d{4})', title.upper())
    if m and m.group(2).lower().replace('ç', 'ç') in MONTHS:
        return f'{int(m.group(3)):04d}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}', 'enacted'
    return r['data'], 'listed'


def act(r, lines, b):
    paras = paragraphs(lines)
    units = units_of([('p', p) for p in paras], adt=False)
    day, how = date_of(r, lines)
    n, y = r['numero'], r['ano']
    key = slug = f'lc-{y}-{n:03d}'
    label = f'Lei Complementar nº {n}, de {y}'
    url = f"https://www.al.to.leg.br/arquivo/{r['id']}"
    law = {'label': label, 'title': r['ementa'] or label, 'kind': 'law', 'enacted': r['data'],
           'published': day if how == 'published' else None, 'url': url, 'temporary_until': None,
           'restores': None, 'note': None}
    e = r['ementa']
    a = {'slug': slug, 'short': f'LC {n}/{y}', 'title': label + (f' ({e})' if e and len(e) < 160 else ''),
         'url': url, 'first_law': key, 'earlier_laws': [],
         'versions': [{'from': day, 'source_url': url, 'sha256': sha(b), 'units': units}]}
    return a, {key: law}


def cli():
    idx, res, missing = main()
    if sys.argv[1] == 'list':
        for r, ok, why in res:
            print(r['numero'], r['ano'], r['data'], '->', why, '|', r['ementa'][:60])
        print(sum(1 for x in res if x[1]), 'in of', len(res), '; numbers missing from the list:', missing)
        return
    n, a, b = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    sel = sorted([x for x in res if x[1]], key=lambda x: (x[0]['data'] or '', x[0]['numero']))[a:b]
    acts, laws = [], {}
    for r, (lines, raw), _ in sel:
        x, l = act(r, lines, raw)
        acts.append(x)
        laws.update(l)
    dec = [DECISIONS[0].replace('nos 50, 119, 122 and 130', 'nos ' + ', '.join(map(str, missing)))] + DECISIONS[1:]
    c = {'country': COUNTRY,
         'sources': [{'name': 'Assembleia Legislativa do Estado do Tocantins: Legislação Estadual (one PDF per act)',
                      'url': SITE, 'retrieved': RETRIEVED, 'licence': COUNTRY['licence_note'],
                      'notes': f'{len(acts)} acts in this part.'}],
         'laws': laws, 'acts': acts, 'applies': [], 'decisions': dec, 'ai_use': AI}
    print(write_part(HERE / 'corpus.d', f'{20 + n}-lc-{n:02d}', c), len(acts), 'acts')


if __name__ == '__main__':
    cli()
