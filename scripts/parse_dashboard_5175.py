import re
import html
from pathlib import Path

text = Path("_dashboard_5175.html").read_text(encoding="utf-8")

rows = re.findall(r'<tr class="align-top">(.*?)</tr>', text, re.S)
print("=== OVERVIEW TABLE ===")
for row in rows:
    cells = re.findall(r'<td class="[^"]*">(.*?)</td>', row, re.S)
    clean = []
    for c in cells:
        c = re.sub(r"<[^>]+>", " ", c)
        c = html.unescape(re.sub(r"\s+", " ", c).strip())
        clean.append(c)
    if clean:
        print("ACCOUNT:", clean[0])
        print("  Status:", clean[1] if len(clean) > 1 else "")
        print("  Top Priority:", clean[2] if len(clean) > 2 else "")
        print("  Signal:", clean[3] if len(clean) > 3 else "")
        print("  Owner:", clean[4] if len(clean) > 4 else "")
        print("  Blocker:", clean[5] if len(clean) > 5 else "")
        print("  Due:", clean[6] if len(clean) > 6 else "")
        print()

articles = re.findall(r'<article class="rounded-lg.*?</article>', text, re.S)
print(f"\n=== ACCOUNT ROOMS ({len(articles)}) ===")
for art in articles:
    h3 = re.search(r'<h3 class="text-base font-semibold">([^<]+)</h3>', art)
    status = re.search(r'border-(?:rose|amber|emerald)-300[^"]*">([^<]+)</span>', art)
    signals = re.findall(r'<li class="border-l-2[^"]*">([^<]+)</li>', art)
    rec = re.search(r'Recommended Next Step</h4><p class="mt-2[^"]*">([^<]+)</p>', art)
    sig_ta = re.search(r'>Signals Made</span>.*?<textarea[^>]*>([^<]*)</textarea>', art, re.S)
    asks_ta = re.search(r'>Asks</span><textarea[^>]*>([^<]*)</textarea>', art)
    name = h3.group(1) if h3 else "?"
    print(f"\n## {name} ({status.group(1) if status else '?'})")
    if sig_ta:
        print("Signals:", sig_ta.group(1).replace("\n", " / ")[:400])
    if asks_ta:
        print("Asks:", asks_ta.group(1).replace("\n", " / ")[:300])
    if rec:
        print("Next:", rec.group(1)[:300])
