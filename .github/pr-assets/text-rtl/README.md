# Plain-text direction PR evidence

Evidence only; this branch is not the implementation PR.

- Baseline: upstream `8f60e20ea0b3defffc2ae89dd49bb36c9f09a5ff`.
- Implementation: `9c228e0` (`fix/text-auto-direction`).
- `txt-before-after.png`: Arabic-first TXT, upstream on the left, file-level automatic direction on the right. The logical source and copied text are unchanged. English paragraphs also inherit the file's direction.
- `arabic.log-comparison.png`: demonstrates the deliberate file-wide limitation: date/time groups can change visual order under RTL.
- `arabic.nfo-comparison.png`: demonstrates the same limitation for ASCII artwork, which may be mirrored in an Arabic-first file.
- Screenshots use the shipped viewer assets in desktop Chromium, light theme, not native Android UI/WebView. The TXT viewport is 412×520; LOG/NFO viewports are 412×320.

## Measurements

`performance.json` contains the final implementation's raw samples and medians. Desktop headless Chromium 153.0.8010.12, 412×660 CSS-pixel viewport, no CPU throttling, three measured runs per version after one warm-up pair, alternating order. Each sample uses a fresh browser context and identical instrumentation around DOM insertion and forced layout. Two animation frames allow a paint opportunity. Navigation measurements include assets/startup; append operation measurements start at the Show more handler. Exact displayed text is asserted after every page.

These are desktop measurements, not Android performance guarantees. Native memory usage was not measured.

To repeat from a checkout of the implementation branch, save `benchmark.py` into a writable temporary directory, then run from the repository root:

```sh
uv run --no-project --with playwright playwright install chromium
uv run --no-project --with playwright python /path/to/benchmark.py
```

The script uses the cached headless Chromium 1243 executable on the original macOS machine when present; otherwise it uses Playwright's installed Chromium. It writes its generated input files and results beside the script. Different browsers/platforms will produce different timings.
