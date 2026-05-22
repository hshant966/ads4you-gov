"""Accessibility agent. Checks heading hierarchy, skip link, lang, aria, focus, mobile viewport."""
import re, sys, pathlib, json

def run(html_path):
    src = pathlib.Path(html_path).read_text(encoding='utf-8')
    findings = []
    score = 100

    # lang attribute on html
    if not re.search(r'<html[^>]+lang=', src, re.I):
        findings.append("FAIL: <html> missing lang attribute")
        score -= 15

    # viewport meta
    if 'viewport' not in src.lower():
        findings.append("FAIL: missing viewport meta")
        score -= 10

    # skip link
    if 'skip' not in src.lower() or '#main' not in src:
        findings.append("WARN: no skip-to-main link found")
        score -= 8

    # heading hierarchy — extract all h tags in order
    hs = re.findall(r'<(h[1-6])\b[^>]*>', src, re.I)
    if hs:
        levels = [int(h[1]) for h in hs]
        if levels[0] != 1:
            findings.append(f"FAIL: first heading is h{levels[0]}, should be h1")
            score -= 10
        for i in range(1, len(levels)):
            if levels[i] > levels[i-1] + 1:
                findings.append(f"WARN: heading jump h{levels[i-1]}→h{levels[i]} at heading {i+1}")
                score -= 4
    else:
        findings.append("FAIL: no headings found")
        score -= 20

    # images without alt
    imgs = re.findall(r'<img\b[^>]*>', src, re.I)
    for img in imgs:
        if 'alt=' not in img.lower():
            findings.append(f"FAIL: <img> missing alt: {img[:80]}")
            score -= 5

    # interactive elements: buttons without aria-label or text
    btns = re.findall(r'<button\b([^>]*)>(.*?)</button>', src, re.I | re.S)
    for attrs, content in btns:
        text = re.sub(r'<[^>]+>', '', content).strip()
        has_label = 'aria-label' in attrs.lower()
        if not text and not has_label:
            findings.append(f"FAIL: button no text/aria-label: {attrs[:60]}")
            score -= 8

    # links with no text
    links = re.findall(r'<a\b([^>]*)>(.*?)</a>', src, re.I | re.S)
    for attrs, content in links:
        text = re.sub(r'<[^>]+>', '', content).strip()
        has_label = 'aria-label' in attrs.lower()
        if not text and not has_label:
            findings.append(f"WARN: link no text/aria-label: {attrs[:60]}")
            score -= 5

    # focus-visible / focus style
    if 'focus-visible' not in src and ':focus' not in src:
        findings.append("WARN: no focus styles found in CSS")
        score -= 8

    # touch targets — check mobile meta
    if 'width=device-width' not in src:
        findings.append("WARN: viewport not device-width")
        score -= 5

    # duplicate IDs
    ids = re.findall(r'\bid="([^"]+)"', src)
    seen = set(); dupes = set()
    for i in ids:
        if i in seen: dupes.add(i)
        seen.add(i)
    if dupes:
        findings.append(f"FAIL: duplicate IDs: {', '.join(dupes)}")
        score -= 10

    return {
        'agent': 'a11y',
        'headings': hs,
        'duplicate_ids': list(dupes),
        'images_checked': len(imgs),
        'score': max(0, score),
        'findings': findings,
    }

if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), ensure_ascii=False, indent=2))
