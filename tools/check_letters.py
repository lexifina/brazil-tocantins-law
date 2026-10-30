"""Independent letters-and-digits check of a part against the source PDFs, read by a second engine (xpdf/poppler
pdftotext -raw), not pymupdf.

    python -X utf8 check_letters.py corpus.d/21-lc-01.json [...]

Private. For each version: the PDF's sha256 equals the one recorded; the PDF's text, with its page numbers (a line of
1-3 digits alone) left out, reduced to letters and digits, must equal the version's unit files reduced the same way
(heading marks "#" dropped), each unit found at its place in document order and nothing left over.
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from br_lib import letters_check  # noqa: E402


def source(pdf):
    out = subprocess.run(['pdftotext', '-raw', '-enc', 'UTF-8', str(pdf), '-'], capture_output=True, check=True).stdout
    t = out.decode('utf-8', 'replace')
    return re.sub(r'(?m)^\s*\d{1,3}\s*$', '', t.replace('\x0c', '\n'))


def main(paths):
    vs = []
    for p in paths:
        for a in json.load(open(p, encoding='utf-8'))['acts']:
            for v in a['versions']:
                f = HERE / '.cache' / 'raw' / hashlib.sha256(v['source_url'].encode()).hexdigest()
                assert hashlib.sha256(f.read_bytes()).hexdigest() == v['sha256'], (a['slug'], 'sha256')
                vs.append((f"{a['slug']} {v['from']}", v['units'], source(f)))
    bad = letters_check(vs, None)
    for b in bad:
        print(b)
    print(f'{len(vs)} versions checked, {len(bad)} mismatches')
    return len(bad)


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1:] or sorted(str(p) for p in (HERE / 'corpus.d').glob('*.json'))) else 0)
