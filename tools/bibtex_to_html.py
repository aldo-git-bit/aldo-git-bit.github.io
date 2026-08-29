#!/usr/bin/env python3
"""Generate publications.html from a Zotero BibTeX export.

Usage:
    python3 tools/bibtex_to_html.py <input.bib> [-o publications.html]

Replaces the old Google Colab notebook. Requires bibtexparser:
    python3 -m pip install bibtexparser

Theme handling
--------------
Themes live in each Zotero item's Extra field as `tex.theme: a, b`.
How they reach the .bib depends on which exporter was used:

  Better BibTeX  ->  promoted to a real field:  theme = {a, b}
  stock Zotero   ->  dumped verbatim into:      note = {tex.theme: a, b}

The old notebook only read the first form, so a stock export left every
entry "unspecified". read_theme() handles both. Note that `note` may hold
unrelated lines too (e.g. "Place: Burnaby, BC"), sometimes on their own
line, so only the tex.theme line is consumed.
"""

import argparse
import html
import re
import sys

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

LATEX_REPLACEMENTS = {
    r"\'a": "á", r"\'e": "é", r"\'i": "í", r"\'o": "ó", r"\'u": "ú", r"\'y": "ý", r"\'c": "ć",
    r'\"u': "ü", r'\"a': "ä", r'\"o': "ö", r'\=o': "ō",
    r"\'{e}": "é", r"\'{y}": "ý", r"\'{c}": "ć", r'{\\"u}': "ü", r'{\\=o}': "ō",
}

DEFAULT_THEME = "unspecified"


def decode_latex(text):
    for latex, uni in LATEX_REPLACEMENTS.items():
        text = text.replace(latex, uni)
    return text


def clean(text):
    return re.sub(r"\.\.", ".", decode_latex(re.sub(r"[{}]", "", text))).strip()


def read_theme(entry):
    """Return the entry's theme string, from either export format."""
    field = entry.get("theme", "").strip()
    if not field:
        # Stock Zotero: Extra is dumped into `note`, one directive per line.
        match = re.search(r"tex\.theme\s*:\s*([^\n}]*)", entry.get("note", ""))
        field = match.group(1) if match else ""

    themes = [clean(t) for t in field.split(",")]
    themes = [t for t in themes if t]
    return ", ".join(themes) if themes else DEFAULT_THEME


def format_authors(authors):
    formatted = []
    for a in authors.split(" and "):
        a = clean(a)
        parts = a.split(",")
        if len(parts) == 2:
            formatted.append(f"{parts[0].strip()}, {parts[1].strip()}")
        else:
            formatted.append(a.strip())
    return ", ".join(formatted)


def format_editors(editors):
    people = editors.split(" and ")
    output = []
    for i, ed in enumerate(people):
        ed = clean(ed)
        parts = ed.split(",")
        if len(parts) == 2:
            first = f"{parts[1].strip()} {parts[0].strip()}"
            last = f"{parts[0].strip()}, {parts[1].strip()}"
            output.append(first if i == 0 else last)
        else:
            output.append(ed.strip())
    return "edited by " + " and ".join(output)


def format_venue(entry):
    venue = []
    entry_type = entry.get("ENTRYTYPE", "").lower()

    if entry_type == "article":
        for key in ("journal", "volume"):
            if key in entry:
                venue.append(clean(entry[key]))
        if "number" in entry:
            venue.append(f"({clean(entry['number'])})")
        if "pages" in entry:
            venue.append(clean(entry["pages"]))

    elif entry_type == "incollection":
        if "booktitle" in entry:
            venue.append(clean(entry["booktitle"]))
        if "editor" in entry:
            venue.append(format_editors(entry["editor"]))
        for key in ("publisher", "address", "pages"):
            if key in entry:
                venue.append(clean(entry[key]))

    elif entry_type == "techreport":
        venue.append("Technical report")
        if "institution" in entry:
            venue.append(clean(entry["institution"]))

    else:
        for key in ("publisher", "address", "pages"):
            if key in entry:
                venue.append(clean(entry[key]))

    return ", ".join(venue)


def format_entry(entry):
    authors = format_authors(entry.get("author", "Unknown Author"))
    title = clean(entry.get("title", "No Title"))
    url = entry.get("url", "#")
    year = entry.get("year", "n.d.")
    try:
        year_sort = int(year)
    except ValueError:
        year_sort = 0

    theme = read_theme(entry)
    return {
        "year_sort": year_sort,
        "theme": theme,
        "html": f"""
        <div class="publication" data-theme="{html.escape(theme, quote=True)}">
          <p><strong>{year}</strong>: <a href="{html.escape(url, quote=True)}" target="_blank">{title}</a><br>
          {authors}.<br><em>{format_venue(entry)}</em></p>
        </div>
        """,
    }


def build_html(entries):
    formatted = [format_entry(e) for e in entries]
    formatted.sort(key=lambda x: x["year_sort"], reverse=True)
    entries_html = "\n".join(e["html"] for e in formatted)

    themes = sorted({t.strip() for e in formatted for t in e["theme"].split(",") if t.strip()})
    theme_html = "\n".join(
        f'<label><input type="checkbox" name="theme" value="{html.escape(t, quote=True)}"> {t}</label>'
        for t in themes
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Research Publications</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    .publication {{ margin-bottom: 20px; }}
    .filters {{ margin: 20px 0; }}
  </style>
</head>
<body>
  <header><h1>John Alderete - Publications</h1></header>
  <div class="filters"><strong>Filter by theme:</strong><br/>{theme_html}</div>
  <section id="publications">{entries_html}</section>
  <script>
    document.querySelectorAll('input[name="theme"]').forEach(cb => {{
      cb.addEventListener('change', () => {{
        const selected = Array.from(document.querySelectorAll('input[name="theme"]:checked')).map(cb => cb.value);
        document.querySelectorAll('.publication').forEach(pub => {{
          const themes = pub.dataset.theme.split(',').map(t => t.trim());
          pub.style.display = selected.length === 0 || selected.some(t => themes.includes(t)) ? 'block' : 'none';
        }});
      }});
    }});
  </script>
</body>
</html>
""", formatted


def main():
    ap = argparse.ArgumentParser(description="Build publications.html from a Zotero BibTeX export.")
    ap.add_argument("bib", help="path to the exported .bib file")
    ap.add_argument("-o", "--output", default="publications.html", help="output HTML path")
    args = ap.parse_args()

    with open(args.bib, encoding="utf-8") as f:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        entries = bibtexparser.load(f, parser=parser).entries

    if not entries:
        sys.exit(f"No entries parsed from {args.bib}")

    page, formatted = build_html(entries)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(page)

    untagged = [e for e in formatted if e["theme"] == DEFAULT_THEME]
    print(f"Parsed {len(entries)} entries -> {args.output}")
    print(f"Themed: {len(formatted) - len(untagged)}   untagged: {len(untagged)}")
    if untagged:
        print(f"\nEntries with no tex.theme (add one in Zotero's Extra field):")
        for e in untagged:
            title = re.search(r'target="_blank">(.*?)</a>', e["html"], re.S)
            print(f"  {e['year_sort']}  {title.group(1)[:80] if title else '?'}")


if __name__ == "__main__":
    main()
