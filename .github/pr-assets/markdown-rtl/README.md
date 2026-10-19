# Markdown direction PR evidence

Evidence only; this branch is not the implementation PR.

- Baseline: upstream `8f60e20ea0b3defffc2ae89dd49bb36c9f09a5ff`.
- Implementation: `4de1c28` on `fix/markdown-rtl`.
- Same rendered source before (left) and after (right), using shipped viewer assets.
- Desktop headless Chromium 153.0.8010.12, 412×560 CSS-pixel viewport, en-US locale. These are not native Android UI or WebView screenshots.
- `markdown-before-after.png`: Arabic heading, paragraphs, list, quote, inline/fenced code and table.
- `code-first-before-after.png`: English code before Arabic prose; code stays LTR and does not choose the document direction.
- `arabic-dark-before-after.png`: Arabic example in the dark theme.
- `english-before-after.png`: English-only example, pixel-identical before/after.
- `comparison.json`: observed direction, quote borders, code direction, element counts, rendered text and copied selections. Text/selection and element counts are unchanged. An authored-direction example is also pixel-identical.

The renderer intentionally chooses whole-document direction from the first strong character outside explicitly directed scopes. It does not choose an independent direction for every paragraph. Existing authored direction scopes are preserved; code defaults to LTR only outside those scopes.

No screenshots or evidence files are included in the implementation diff.
