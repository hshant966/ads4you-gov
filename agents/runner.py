#!/usr/bin/env python3
"""
Parallel audit runner. Runs all agents on index.html simultaneously.
Usage: python3 runner.py [path/to/index.html]
"""
import sys, json, time, pathlib
from multiprocessing import Pool
from datetime import datetime

# import agents as modules
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import agent_lang, agent_blueprint, agent_a11y, agent_links, agent_perf, agent_html

AGENTS = [
    agent_lang,
    agent_blueprint,
    agent_a11y,
    agent_links,
    agent_perf,
    agent_html,
]

AGENT_NAMES = ['agent_lang', 'agent_blueprint', 'agent_a11y', 'agent_links', 'agent_perf', 'agent_html']

def run_agent(args):
    name, path = args
    try:
        import importlib, sys, pathlib as _p
        sys.path.insert(0, str(_p.Path(__file__).parent))
        module = importlib.import_module(name)
        t0 = time.time()
        result = module.run(path)
        result['_time_ms'] = round((time.time() - t0) * 1000)
        return result
    except Exception as e:
        return {'agent': name, 'error': str(e), 'score': 0, 'findings': [str(e)]}

def main():
    html_path = sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).parent.parent / 'index.html')
    if not pathlib.Path(html_path).exists():
        print(f"ERROR: file not found: {html_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  ADS4YOU GOV — AUDIT RUNNER")
    print(f"  File: {html_path}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    t0 = time.time()
    args = [(n, html_path) for n in AGENT_NAMES]

    with Pool(len(AGENT_NAMES)) as pool:
        results = pool.map(run_agent, args)

    elapsed = round((time.time() - t0) * 1000)

    # aggregate
    total_score = sum(r.get('score', 0) for r in results)
    avg_score = total_score / len(results)
    all_findings = []
    for r in results:
        for f in r.get('findings', []):
            all_findings.append(f"[{r['agent'].upper()}] {f}")

    fails = [f for f in all_findings if f.startswith('[') and 'FAIL' in f]
    warns = [f for f in all_findings if 'WARN' in f]
    infos = [f for f in all_findings if 'INFO' in f]

    # print per-agent summary
    print("AGENT SCORES:")
    for r in results:
        s = r.get('score', 0)
        bar = '█' * (s // 10) + '░' * (10 - s // 10)
        status = '✓' if s >= 80 else ('△' if s >= 60 else '✗')
        print(f"  {status} {r['agent']:<12} {bar} {s:>3}/100  ({r.get('_time_ms','?')}ms)")

    print(f"\n{'─'*60}")
    print(f"  OVERALL SCORE: {avg_score:.0f}/100")
    print(f"  Total time: {elapsed}ms")
    print(f"  Fails: {len(fails)}  Warns: {len(warns)}  Info: {len(infos)}")
    print(f"{'─'*60}\n")

    if fails:
        print("FAILURES (fix before deploy):")
        for f in fails: print(f"  {f}")
        print()

    if warns:
        print("WARNINGS:")
        for w in warns: print(f"  {w}")
        print()

    # write JSON report
    report = {
        'timestamp': datetime.now().isoformat(),
        'file': html_path,
        'overall_score': round(avg_score, 1),
        'agents': results,
        'fails': fails,
        'warns': warns,
        'infos': infos,
    }
    report_path = pathlib.Path(html_path).parent / 'AUDIT-REPORT.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Report saved: {report_path}")

    sys.exit(0 if avg_score >= 75 else 1)

if __name__ == '__main__':
    main()
