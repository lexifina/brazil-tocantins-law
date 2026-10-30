# Tocantins: law history in git

The law of the State of Tocantins (Estado do Tocantins) (Brazil) as a git history: one file per Artigo, one paragraph per line, so `git blame`, `git log` and `git diff` work line by line. The text is Portuguese, the only official language.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law).

## What this repository holds

| Folder | Act | Versions |
| --- | --- | ---: |
| `lc-<year>-<number>/` | Leis Complementares that were never altered, each as enacted (97 acts) | 1 each |

Only Leis Complementares that were never altered are included. The Assembleia's compiled PDFs print an altered provision's earlier and later wordings one after the other, each with a note naming the act that gave it, and do not mark which one is in force, so altered acts, revoked acts and the Constituição do Estado (compiled the same way) are left out rather than guessed. Ordinary Leis are not included yet.

## Source

[Assembleia Legislativa do Estado do Tocantins, Legislação Estadual](https://www.al.to.leg.br/legislacaoEstadual), published by the Assembleia Legislativa do Estado do Tocantins. Each version names the page it was taken from and that page's sha256, in `data/versions.json`.

## Dates

Each act is dated by its publication in the Diário Oficial do Estado where the Assembleia's record gives that date, otherwise by the act's own date in its title (Tocantins Leis Complementares take effect on publication). Commits are at noon in Palmas.

## How it is built

Lexifina reads the sources listed here and records each act's dated versions, and the laws that made each change, in one corpus file. `tools/build.py` writes this repository from that file, and the same corpus always gives the same commit hashes; `REPRODUCE.md` gives the details and the checks. A model (Claude) wrote Lexifina's code; it wrote no legal text, and no model runs when the history is built.

Each act's PDF (text layer) becomes one file per Art.; headings stand above the first article under them; `000-titulo.md` holds the title, the publication line, the ementa and the enacting formula. Wrapped lines are joined; a line that does not reach the right margin ends its paragraph. An act is taken as never altered when its PDF carries no compilation mark (no red text, no small italic note, no line starting with "*", no "Revogada" or "Alterada" line under the title) and no other Lei Complementar on the list cites it next to a word of alteration or repeal. Acts whose tables a second PDF reader reads in a different order are left out.

## How it is checked

Every version is read back from git on the day it took effect (`tools/check_repo.py`) and must match the corpus; an independent letters-and-digits comparison of every version against the source page must show no difference. Results are in `REPRODUCE.md`.

## What "author" means

The author of each commit is the law that made the text, or, for a consolidated text, the publisher, with an e-mail address that cannot exist; the committer is always Lexifina.

## Limits

Not a complete history: only never-altered Leis Complementares, each as enacted. The list shows no record for Leis Complementares nos 50, 119, 122 and 130, so an alteration made by one of them cannot be seen. Ordinary laws are not checked for alterations. The text is not the official version: only the Diário Oficial do Estado is authoritative. Text after the last article (place, date, signatures, annexes) stays in the last article's file; tables are flattened into lines.

## Licence

See [LICENSE](LICENSE): Brazilian law texts are not protected by copyright (Lei 9.610/1998, art. 8, IV). Fonte: Assembleia Legislativa do Estado do Tocantins, Legislação Estadual, Assembleia Legislativa do Estado do Tocantins.
