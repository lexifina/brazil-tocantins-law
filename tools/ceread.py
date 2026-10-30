"""Private. Constituição do Estado do Tocantins (ALETO PDF, WPS Writer text layer) -> paragraphs with their notes.

pymupdf spans. Pages 9..85 of the PDF (index 8..84) hold the text; the pages before are the cover and contents, the
pages after reprint each Emenda Constitucional. Page numbers (small, at the foot) are dropped. A line whose spans are
all small (< 11 pt) is a publisher's note ("*(... pela Emenda Constitucional nº ...)"); a line starting at the
paragraph indent (x0 >= 100) starts a paragraph, a line at the margin continues it. Fragments on one baseline are
joined left to right.
"""
import re
import unicodedata

import pymupdf

FIRST, LAST = 8, 84


def clean(s):
    s = unicodedata.normalize('NFC', s.replace('\xa0', ' ').replace('­', '').replace('\t', ' '))
    return re.sub(r' {2,}', ' ', s).strip()


def page_lines(page):
    rows = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            sp = [s for s in l['spans'] if s['text'].strip()]
            if not sp:
                continue
            rows.append({'y': round(l['bbox'][3], 0), 'x0': l['bbox'][0], 'x1': l['bbox'][2], 'spans': l['spans']})
    rows.sort(key=lambda r: (r['y'], r['x0']))
    out = []
    for r in rows:
        if out and abs(out[-1]['y'] - r['y']) <= 2:
            out[-1]['spans'] += [{'text': ' '}] + r['spans']
            out[-1]['x1'] = r['x1']
        else:
            out.append(r)
    res = []
    for r in out:
        sp = [s for s in r['spans'] if s['text'].strip()]
        text = clean(''.join(s['text'] for s in r['spans']))
        small = all(s['size'] < 11 for s in sp)
        if small and re.fullmatch(r'\d{1,3}', text) and r['y'] > 720:
            continue  # page number
        res.append({'text': text, 'x0': r['x0'], 'y': r['y'], 'note': small,
                    'bold': all('Bold' in s['font'] for s in sp),
                    'red': [clean(s['text']) for s in sp if s.get('color') == 16711680 and s['size'] >= 11]})
    return res


def lines(path):
    d = pymupdf.open(path)
    out = []
    for pno in range(FIRST, LAST + 1):
        for l in page_lines(d[pno]):
            l['page'] = pno
            out.append(l)
    return out


def paragraphs(ls):
    """-> [{'text', 'notes': [...], 'heading': bool, 'page'}]"""
    out = []
    for l in ls:
        if l['note']:
            if out and out[-1].get('open_note'):
                out[-1]['notes'][-1] += ' ' + l['text']
            elif out:
                out[-1]['notes'].append(l['text'])
            else:
                out.append({'text': '', 'notes': [l['text']], 'heading': False, 'page': l['page']})
            out[-1]['open_note'] = not l['text'].rstrip().endswith((')', ').', ');'))
            continue
        heading = l['bold'] and l['x0'] > 180
        if out and out[-1]['notes'] == [] and not heading and not out[-1]['heading'] and l['x0'] < 100 and out[-1]['text']:
            p = out[-1]['text']
            out[-1]['text'] = p + l['text'] if re.search(r'\w-$', p) and not p.endswith(' -') else p + ' ' + l['text']
            out[-1]['red'] += l['red']
            continue
        if out and out[-1]['heading'] and heading and not re.match(r'(T[ÍI]TULO|CAP[ÍI]TULO|SE[ÇC][ÃA]O|SUBSE[ÇC]|\*)', l['text']):
            out[-1]['text'] += ' ' + l['text']  # a heading's name on two lines
            continue
        out.append({'text': l['text'], 'notes': [], 'heading': heading, 'page': l['page'], 'red': list(l['red'])})
    for p in out:
        p.pop('open_note', None)
    return out
