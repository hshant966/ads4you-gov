"""Performance agent. File size, external requests, render-blocking scripts, inline budget."""
import re, sys, pathlib, json

def run(html_path):
    src = pathlib.Path(html_path).read_text(encoding='utf-8')
    size_bytes = pathlib.Path(html_path).stat().st_size
    findings = []
    score = 100

    # file size
    size_kb = size_bytes / 1024
    if size_kb > 200:
        findings.append(f"WARN: HTML {size_kb:.1f}KB — consider splitting if >200KB")
        score -= 10
    elif size_kb > 100:
        findings.append(f"INFO: HTML {size_kb:.1f}KB — acceptable")

    # external requests
    external_srcs = re.findall(r'(?:src|href)="(https?://[^"]+)"', src, re.I)
    cdn_scripts = [u for u in external_srcs if re.search(r'\.(js|css)(\?|$)', u)]
    font_links = [u for u in external_srcs if 'fonts.google' in u or 'fonts.gstatic' in u]
    other_ext = [u for u in external_srcs if u not in cdn_scripts and u not in font_links]

    if cdn_scripts:
        findings.append(f"INFO: {len(cdn_scripts)} external JS/CSS: {cdn_scripts}")

    if len(font_links) > 3:
        findings.append(f"WARN: {len(font_links)} font requests — may slow on gov networks")
        score -= 8

    # render-blocking: scripts without defer/async in <head>
    head_match = re.search(r'<head\b[^>]*>(.*?)</head>', src, re.S | re.I)
    if head_match:
        head = head_match.group(1)
        blocking = re.findall(r'<script\b(?![^>]*\b(?:defer|async|type="module")\b)[^>]*src=[^>]*>', head, re.I)
        if blocking:
            findings.append(f"FAIL: {len(blocking)} render-blocking script(s) in <head>: {blocking}")
            score -= 15 * len(blocking)

    # inline script size
    inline_scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', src, re.S | re.I)
    total_inline = sum(len(s) for s in inline_scripts)
    if total_inline > 50000:
        findings.append(f"WARN: {total_inline//1024}KB inline JS — consider extracting to .js file")
        score -= 10

    # preconnect for fonts
    has_preconnect = 'preconnect' in src
    if font_links and not has_preconnect:
        findings.append("WARN: Google Fonts used but no <link rel=preconnect>")
        score -= 5

    # image optimization hints
    imgs = re.findall(r'<img\b[^>]*>', src, re.I)
    for img in imgs:
        if 'loading=' not in img.lower():
            findings.append(f"INFO: <img> missing loading=lazy: {img[:60]}")
            score -= 2

    return {
        'agent': 'perf',
        'size_kb': round(size_kb, 1),
        'external_requests': len(external_srcs),
        'cdn_scripts': len(cdn_scripts),
        'font_requests': len(font_links),
        'render_blocking': len(blocking) if head_match else 0,
        'inline_js_bytes': total_inline,
        'score': max(0, score),
        'findings': findings,
    }

if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), ensure_ascii=False, indent=2))
