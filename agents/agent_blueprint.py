"""Blueprint compliance agent. Checks forbidden phrases, required terms, contact rules."""
import re, sys, pathlib, json

FORBIDDEN = [
    # contact violations
    r'\bwhatsapp\b', r'\bphone\b', r'\bmobile\b', r'\+91', r'9[0-9]{9}',
    # pricing
    r'₹\s*\d', r'\bpricing\b', r'\bpackage\b', r'\bcost\b', r'\bfee\b', r'\brate\b',
    # fake claims
    r'\bguarantee\b', r'\bguaranteed\b', r'\bcertified by\b', r'\bapproved by government\b',
    r'\bISO\b', r'\bCERT-In empanelled\b', r'\bGeM registered\b',
    # startup hype
    r'\bdisrupt\b', r'\brevolution\b', r'\bgame.chang\b', r'\bbest in\b', r'\bno\.?\s*1\b',
    r'\btransform.*government\b',
    # marketing Marathi bad patterns from blueprint
    r'Pending तक्रारी', r'मोठ्या Vendor', r'हैदराबादला', r'शून्य जोखीम',
    # testimonials / fake social proof
    r'\btestimonial\b', r'\breview[s]?\b', r'\bstar rating\b', r'\bclient said\b',
]

REQUIRED = [
    ('UDYAM', 'UDYAM registration number visible'),
    ('ads4you@zohomail', 'correct email present'),
    ('data-lang-mr', 'bilingual tagging present'),
    ('data-lang-en', 'bilingual EN tagging present'),
    ('प्रायोगिक', 'pilot-first language present'),
    ('उत्तरदायित', 'accountability language present'),
    ('वाकड', 'local presence (Wakad) stated'),
    ('MSME', 'MSME category mentioned'),
    ('#contact', 'contact CTA link present'),
    ('mailto:', 'email link present'),
]

REQUIRED_ABSENT = [
    ('tel:', 'phone link must not exist'),
    ('wa.me', 'WhatsApp link must not exist'),
    ('api.whatsapp', 'WhatsApp API must not exist'),
]

def run(html_path):
    src = pathlib.Path(html_path).read_text(encoding='utf-8').lower()
    src_raw = pathlib.Path(html_path).read_text(encoding='utf-8')
    findings = []
    score = 100

    # forbidden
    forbidden_hits = []
    for pat in FORBIDDEN:
        m = re.search(pat, src, re.I)
        if m:
            line = src[:m.start()].count('\n') + 1
            forbidden_hits.append(f"line {line}: forbidden pattern '{pat}' → '{src_raw[max(0,m.start()-20):m.end()+20].strip()}'")
            score -= 8
    findings += forbidden_hits

    # required present
    missing_req = []
    for term, desc in REQUIRED:
        if term.lower() not in src:
            missing_req.append(f"MISSING: {desc} ('{term}')")
            score -= 6
    findings += missing_req

    # required absent
    for term, desc in REQUIRED_ABSENT:
        if term.lower() in src:
            findings.append(f"VIOLATION: {desc}")
            score -= 15

    # email check — must be exact
    if 'ads4you@zohomail.in' not in src_raw:
        findings.append("WRONG EMAIL: must be ads4you@zohomail.in (not .com or other)")
        score -= 20

    return {
        'agent': 'blueprint',
        'forbidden_hits': len(forbidden_hits),
        'missing_required': len(missing_req),
        'score': max(0, score),
        'findings': findings[:30],
    }

if __name__ == '__main__':
    print(json.dumps(run(sys.argv[1]), ensure_ascii=False, indent=2))
