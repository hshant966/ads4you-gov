"""Bilingual coverage agent. Verifies every data-lang-mr has matching data-lang-en."""
import re, sys, pathlib

def run(html_path):
    src = pathlib.Path(html_path).read_text(encoding="utf-8")
    findings = []
    # find all elements with data-lang-mr
    pat_mr = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)([^>]*\bdata-lang-mr="([^"]*)"[^>]*)>', re.S)
    matches = list(pat_mr.finditer(src))
    total = len(matches)
    missing_en = 0
    empty = 0
    for m in matches:
        attrs = m.group(2)
        if 'data-lang-en="' not in attrs:
            missing_en += 1
            findings.append(f"line ~{src[:m.start()].count(chr(10))+1}: <{m.group(1)}> has data-lang-mr but no data-lang-en")
        else:
            mr = m.group(3).strip()
            en_m = re.search(r'data-lang-en="([^"]*)"', attrs)
            en = en_m.group(1).strip() if en_m else ''
            if not mr or not en:
                empty += 1
                findings.append(f"line ~{src[:m.start()].count(chr(10))+1}: empty mr/en value")
    # also check button toggle exists
    has_btn = 'id="langBtn"' in src
    has_setlang = 'setLang' in src or 'data-lang-' in src
    score = 100
    if missing_en: score -= min(60, missing_en*5)
    if empty: score -= min(20, empty*3)
    if not has_btn: score -= 20
    return {
        "agent":"lang",
        "total_mr_tagged": total,
        "missing_en": missing_en,
        "empty": empty,
        "has_toggle_btn": has_btn,
        "has_toggle_logic": has_setlang,
        "score": max(0,score),
        "findings": findings[:20],
    }

if __name__=="__main__":
    import json
    print(json.dumps(run(sys.argv[1]), ensure_ascii=False, indent=2))
