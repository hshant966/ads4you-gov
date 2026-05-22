"""Links agent. Checks no broken anchors, no placeholder hrefs, mailto valid, anchors exist."""
import re, sys, pathlib, json

def run(html_path):
    src = pathlib.Path(html_path).read_text(encoding='utf-8')
    findings = []
    score = 100

    # collect all anchor IDs in doc
    anchor_ids = set(re.findall(r'\bid="([^"]+)"', src))

    # collect all hrefs
    hrefs = re.findall(r'\bhref="([^"]*)"', src)

    placeholder = []
    broken_anchors = []
    no_mailto_subject = []
    valid_external = []

    for href in hrefs:
        href = href.strip()
        # placeholder check
        if href in ('#', '', 'javascript:void(0)', 'javascript:', '#!'):
            placeholder.append(href)
            score -= 5
            findings.append(f"WARN: placeholder href '{href}'")
            continue

        # internal anchor
        if href.startswith('#'):
            anchor = href[1:]
            if anchor and anchor not in anchor_ids:
                broken_anchors.append(href)
                score -= 10
                findings.append(f"FAIL: anchor '{href}' target id not in document")

        # mailto check
        if href.startswith('mailto:'):
            addr = href[7:].split('?')[0]
            if 'ads4you@zohomail.in' not in addr:
                findings.append(f"WARN: unexpected mailto address: {addr}")
                score -= 8

    # check required anchor targets exist
    required_anchors = ['main', 'contact', 'trust', 'capabilities', 'approach', 'context']
    for req in required_anchors:
        if req not in anchor_ids:
            findings.append(f"WARN: expected anchor id='{req}' not found")
            score -= 4

    # no tel: links
    tel = re.findall(r'href="tel:[^"]*"', src)
    if tel:
        for t in tel:
            findings.append(f"FAIL: tel link found (must remove): {t}")
            score -= 15

    # no wa.me
    if 'wa.me' in src or 'whatsapp.com' in src.lower():
        findings.append("FAIL: WhatsApp link found — must remove")
        score -= 20

    return {
        'agent': 'links',
        'total_hrefs': len(hrefs),
        'placeholder': len(placeholder),
        'broken_anchors': len(broken_anchors),
        'tel_links': len(tel),
        'anchor_ids_found': sorted(anchor_ids),
        'score': max(0, score),
        'findings': findings,
    }

if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), ensure_ascii=False, indent=2))
