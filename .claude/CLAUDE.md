# aldo-git-bit.github.io

John Alderete's personal site, served by GitHub Pages from `main`. Pushing to `main` deploys within a minute or two. This repo is edited from two laptops, so the rules below live here (not in per-laptop memory) to keep both in sync.

## Audience and tone

The site shares research news with business managers, recruiters and academic audiences. Keep wording concise and accessible, not overly technical.

## News section (`index.html`)

- Each item starts with a date tag: `<strong>YYYY-Mon:</strong>`, using three-letter months (Jan, Feb, Mar, …, Sept is written `Sept`).
- Newest items go at the top.
- Link papers with `target="_blank"`. Prefer the publisher's or venue's official open-access link when one exists.

## Publications (`publications.html`)

`publications.html` is edited directly. It used to be generated from a Zotero BibTeX export; that pipeline was retired on 2026-10-24, so never regenerate the page from a `.bib` file, because that would wipe hand edits.

To add a publication, insert a block matching the existing entries:

```html
<div class="publication" data-theme="AI, speech-NLP">
  <p><strong>YEAR</strong>: <a href="URL" target="_blank">Title</a><br>
  Last, First, Last, First.<br><em>Venue, vol, pages</em></p>
</div>
```

- Keep descending year order; the newest item of a year goes at the top of that year.
- Themes in `data-theme` must each have a matching checkbox in the `.filters` block, which is static HTML. Existing themes: AI, computational-learning, constraint-optimization, data-annotation, psycholinguistics, speech-NLP. For a new theme, add `<label><input type="checkbox" name="theme" value="..."> ...</label>` in alphabetical order.
- Before committing, check that the HTML is well formed, the entry count went up by the expected number, and every theme has a checkbox.
