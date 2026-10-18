"""Desktop Chromium comparison; run with uv --with playwright python benchmark.py."""
import codecs
import json
import statistics
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent
REPO = Path.cwd()
sys.path.insert(0, str(REPO / 'tests/viewer'))
from server import ViewerServer

BASE = '8f60e20ea0b3defffc2ae89dd49bb36c9f09a5ff'
RUNS = 3
PAGE = 5 * 1024 * 1024

def repeated(line, size):
    data = line.encode('utf-8')
    return (data * (size // len(data) + 1))[:size]

cases = {
    'small_arabic': ('هذه فقرة عربية للقراءة واختبار اتجاه النص.\n' * 60).encode(),
    'arabic_1mib': repeated('هذه فقرة عربية للقراءة واختبار اتجاه النص مع بعض الكلمات والأرقام 123.\n', 1024 * 1024),
    'english_5mib': repeated('English words on a normal text line, with spaces and punctuation.\n', PAGE),
    'arabic_6mib_paged': repeated('هذه فقرة عربية للقراءة واختبار اتجاه النص مع بعض الكلمات والأرقام 123.\n', 6 * 1024 * 1024),
    'unbroken_6mib_paged': b'a' * (6 * 1024 * 1024),
    'short_lines_1mib': b'a\n' * (1024 * 1024 // 2),
}
sources = {}
for version in ('before', 'after'):
    sources[version] = {}
    for name in ('text.html', 'text.js'):
        path = 'app/src/main/assets/viewer/' + name
        sources[version][name] = (subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=REPO, text=True)
                                  if version == 'before' else (REPO / path).read_text())
    js = sources[version]['text.js']
    for old in ('function showPage() {', '    firstPage = false;', '    shown += page.bytes;'):
        assert js.count(old) == 1, old
    js = js.replace('function showPage() {', 'function showPage() {\n  var benchCall = performance.now();')
    js = js.replace('    firstPage = false;', '    firstPage = false;\n    var benchStart = performance.now();')
    js = js.replace('    shown += page.bytes;', '''    var benchBuilt = performance.now();
    var benchHeight = content.getBoundingClientRect().height;
    var benchLaid = performance.now();
    var result = {insert_ms: benchBuilt - benchStart,
      layout_ms: benchLaid - benchBuilt, dom_layout_ms: benchLaid - benchStart,
      paragraphs: content.childElementCount, height: benchHeight};
    requestAnimationFrame(function () { requestAnimationFrame(function () {
      result.operation_ms = performance.now() - benchCall;
      result.navigation_ms = performance.now();
      window.__benchResults = window.__benchResults || [];
      window.__benchResults.push(result);
    }); });
    shown += page.bytes;''')
    sources[version]['text.js'] = js

server = ViewerServer()
records = {name: {'bytes': len(data), 'before': [], 'after': []} for name, data in cases.items()}
try:
    with sync_playwright() as p:
        exe = next((Path.home() / 'Library/Caches/ms-playwright/chromium_headless_shell-1243').rglob('chrome-headless-shell'), None)
        browser = p.chromium.launch(**({'executable_path': str(exe)} if exe else {}))
        browser_version = browser.version
        for name, data in cases.items():
            fixture = OUT / (name + '.txt')
            fixture.write_bytes(data)
            server.show(fixture)
            for run in range(RUNS + 1):
                for version in (('before', 'after') if run % 2 == 0 else ('after', 'before')):
                    context = browser.new_context(viewport={'width': 412, 'height': 660}, locale='en-US', reduced_motion='reduce')
                    page = context.new_page()
                    for asset, mime in (('text.html', 'text/html'), ('text.js', 'text/javascript')):
                        page.route('**/assets/viewer/' + asset + ('*' if asset.endswith('.html') else ''),
                                   lambda route, request, body=sources[version][asset], mime=mime: route.fulfill(status=200, content_type=mime, body=body))
                    page.goto(server.url('text.html'))
                    page.wait_for_function('() => window.__benchResults && window.__benchResults.length === 1', timeout=60000)
                    opening = page.evaluate('window.__benchResults[0]')
                    decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
                    expected = decoder.decode(data[:PAGE], final=len(data) <= PAGE)
                    assert page.locator('#content').text_content() == expected
                    result = {'open': opening}
                    if len(data) > PAGE:
                        page.evaluate("() => document.querySelector('#moreBtn').click()")
                        page.wait_for_function('() => window.__benchResults.length === 2', timeout=60000)
                        assert page.locator('#content').text_content() == data.decode(errors='replace')
                        result['append'] = page.evaluate('window.__benchResults[1]')
                    if run:
                        records[name][version].append(result)
                    context.close()
            print(name, flush=True)
            for phase in ('open', 'append'):
                if phase not in records[name]['before'][0]:
                    continue
                medians = {version: {key: round(statistics.median(row[phase][key] for row in records[name][version]), 2)
                                     for key in ('dom_layout_ms', 'operation_ms', 'navigation_ms', 'paragraphs')}
                           for version in ('before', 'after')}
                records[name][phase + '_medians'] = medians
                print(' ', phase, json.dumps(medians), flush=True)
            (OUT / 'performance.json').write_text(json.dumps({'baseline': BASE, 'implementation': 'File-level native dir=auto for txt/log/nfo/extensionless files; unicode-bidi:isolate. Original text nodes and paging preserved. No paragraph spans.', 'browser': browser_version,
                'runs_per_version': RUNS, 'warmup_pairs_per_case': 1, 'viewport': {'width': 412, 'height': 660},
                'method': 'Alternating order, new browser context each sample. Identical instrumentation around DOM insertion and forced layout. Operation includes read/decode and two RAFs for a paint opportunity; navigation also includes assets/startup. No CPU throttling. Text equality asserted each page. Desktop only; not Android.',
                'cases': records}, ensure_ascii=False, indent=2) + '\n')
        browser.close()
finally:
    server.stop()
