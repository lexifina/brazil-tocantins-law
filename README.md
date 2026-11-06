# Tocantins: law in git

Part of [lexifina/global-law](https://github.com/lexifina/global-law), one git history for every country's law: this is the law of Tocantins, Brazil, which global-law reads at `brazil/tocantins/acts/`.

Selected laws of the State of Tocantins, in Portuguese, from the Assembleia Legislativa do Estado do Tocantins.

## What this repository holds

| Folder | Act | Versions |
| --- | --- | ---: |
| `lc-<year>-<number>/` | Existing complementary laws, as enacted (50 acts) | 1 each |
| `lei-<year>-<number>/` | Selected ordinary laws as current-text baselines, complete text in `texto.md` | 1 each |
| Additional `lc-<year>-<number>/` | Selected complementary laws as current-text baselines, complete text in `texto.md` | 1 each |

The released acts and versions are listed in [data/versions.json](data/versions.json). The original set comprises 50 complementary laws as enacted. Additional current-text baselines are recorded as they are released, each labelled the oldest version available in this record and credited to the publisher. The existing complementary laws retain their as-enacted label. This is a selected-acts corpus, with no complete historical record.

## Source

[Assembleia Legislativa do Estado do Tocantins, Legislação Estadual](https://www.al.to.leg.br/legislacaoEstadual). Each version identifies its official PDF and SHA-256 in `data/versions.json`. Only the Diário Oficial do Estado is authoritative.

## Dates

The additional current-text acts are dated by their own commencement clauses: the printed gazette publication day, a fixed stated date, or a stated number of days after the printed publication. Each version note quotes both source statements and explains any calculation. In the selected current-text set, nine acts commence after publication. For example, Lei 5.016/2026 was published on 4 May 2026 and takes effect 120 days later, on 1 September 2026. Existing complementary laws retain their recorded dates and labels. In-force dates describe legal commencement, independently of the git commit timestamp.

## Reading the record

| Question | Command |
| --- | --- |
| Who supplied a line? | `git blame <act>/texto.md` |
| What versions are recorded? | `git log -- <act>/` |
| What changed between revisions? | `git diff <old> <new> -- <act>/` |

## What author means

The publisher supplies current-text baselines. Existing as-enacted versions name the original law. Lexifina is the committer; the author labels identify provenance rather than a person drafting the text.

## How it is checked

The additional law text is compared word for word, including punctuation, with the official PDF using two independent PDF readers. The files are also checked on their version dates. Repeated builds establish reproducibility. Source decisions are recorded in `REPRODUCE.md`.

## Limits

Compiled PDFs with competing wordings, possible later amendments, uncertain commencement dates, images requiring assessment and scans requiring OCR are excluded from the additional baselines. Each included act is a single-file act: all its source text, textual annexes and signatures appear in `texto.md`. The 50 existing complementary laws retain their article files. Missing acts and versions are outside this record and cannot be inferred from it.

## Licence

Brazilian official law texts are not protected by copyright under Lei 9.610/1998, art. 8, IV. See [LICENSE](LICENSE).

Fonte: Assembleia Legislativa do Estado do Tocantins, Legislação Estadual. Este acervo reúne leis selecionadas e não substitui o Diário Oficial do Estado.
