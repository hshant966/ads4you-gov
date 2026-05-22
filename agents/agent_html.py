"""HTML structure agent. Checks semantic tags, meta, title, charset, doctype, nav/main/footer."""
import re, sys, pathlib, json

REQUIRED_META = [
    ('charset', 'charset declaration'),
    ('viewport', 'viewport meta'),
    ('description', 'meta description'),
    ('theme-color', 'theme-color meta (mobile browser chrome)'),
]

SEMANTIC_TAGS = ['nav', 'main', 'section', 'footer', 'aside', 'article', 'header']

def run(html_path):
    src = pathlib.Path(html_path).read_text(encoding='utf-8')
    src_l = src.lower()
    findings = []
    score = 100

    # doctype
    if not src_l.startswith('<!doctype html') and '<!doctype html' not in src_l[:100]:
        findings.append("FAIL: missing <!DOCTYPE html>")
        score -= 10

    # required meta
    for term, desc in REQUIRED_META:
        if term not in src_l:
            findings.append(f"FAIL: missing {desc}")
            score -= 8

    # title
    title = re.search(r'<title[^>]*>(.*?)</title>', src, re.I | re.S)
    if not title:
        findings.append("FAIL: no <title>")
        score -= 10
    elif len(title.group(1).strip()) < 5:
        findings.append("WARN: <title> too short")
        score -= 5

    # semantic structure
    for tag in SEMANTIC_TAGS:
        if f'<{tag}' not in src_l:
            findings.append(f"INFO: no <{tag}> element found")
            score -= 2

    # main landmark
    if '<main' not in src_l:
        findings.append("FAIL: no <main> landmark")
        score -= 10

    # nav aria-label
    navs = re.findall(r'<nav\b([^>]*)>', src, re.I)
    for nav in navs:
        if 'aria-label' not in nav.lower() and 'aria-labelledby' not in nav.lower():
            findings.append("WARN: <nav> missing aria-label")
            score -= 5

    # no inline style overriding contrast (basic check)
    inline_styles = re.findall(r'style="[^"]*color\s*:\s*#?(?:fff|ffffff|white)[^"]*"', src_l)
    # just flag count, not scoring

    # check for console.log left in scripts
    if 'console.log' in src:
        findings.append("WARN: console.log found in source — remove before production")
        score -= 3

    # no alert/confirm
    for bad in ['alert(', 'confirm(', 'prompt(']:
        if bad in src:
            findings.append(f"WARN: {bad} found in JS")
            score -= 5

    # language toggle script present
    if 'setLang' not in src and 'data-lang' not in src:
        findings.append("FAIL: bilingual toggle logic missing")
        score -= 15

    return {
        'agent': 'html',
        'has_doctype': '<!doctype html' in src_l[:100],
        'has_title': bool(title),
        'semantic_tags_found': [t for t in SEMANTIC_TAGS if f'<{t}' in src_l],
        'score': max(0, score),
        'findings': findings,
    }

if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), ensure_ascii=False, indent=2))
