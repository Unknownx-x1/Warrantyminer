import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
PROD_API_DIR = BASE_DIR / "apps" / "api"
PROD_WEB_DIR = BASE_DIR / "apps" / "web" / "src"

# Patterns that indicate suspicious hardcoded demo logic in production code
SUSPICIOUS_PATTERNS = [
    (r"\bcanonical_warranty_claims\b", "Hardcoded reference to canonical CSV in production"),
    (r"\bC-900[1-9]\b", "Hardcoded canonical claim ID in production"),
    (r"\bcluster_size\s*==\s*35\b", "Hardcoded check for canonical cluster size 35"),
    (r"\balert_score\s*==\s*95\.8\b", "Hardcoded alert score 95.8 in production"),
    (r"\bif\s+.*canonical.*\b", "Demo-specific conditional branch"),
    (r"import.*ground_truth", "Ground truth imported into production code"),
    (r"from.*ground_truth.*import", "Ground truth imported into production code"),
    (r"import.*tests\b", "Test suite imported into production code"),
    (r"from\s+tests\b", "Test suite imported into production code"),
]

def audit_directory(directory: Path) -> List[Dict[str, Any]]:
    violations = []
    for root, _, files in os.walk(directory):
        for f in files:
            if not f.endswith((".py", ".ts", ".tsx")):
                continue
            fpath = Path(root) / f
            rel_path = fpath.relative_to(BASE_DIR)

            with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                for line_no, line in enumerate(fp, start=1):
                    # Skip comment-only lines
                    stripped = line.strip()
                    if stripped.startswith(("#", "//", "/*", "*")):
                        continue

                    for pat, reason in SUSPICIOUS_PATTERNS:
                        if re.search(pat, line):
                            violations.append({
                                "file": str(rel_path),
                                "line": line_no,
                                "content": stripped,
                                "reason": reason
                            })
    return violations

def main():
    print("=" * 75)
    print("      RELIANT.AI -- PRODUCTION HARDCODING & ISOLATION AUDIT")
    print("=" * 75)

    print(f"\n[1] Auditing Backend Production Code: {PROD_API_DIR.relative_to(BASE_DIR)}...")
    api_violations = audit_directory(PROD_API_DIR)

    print(f"[2] Auditing Frontend Production Code: {PROD_WEB_DIR.relative_to(BASE_DIR)}...")
    web_violations = audit_directory(PROD_WEB_DIR)

    all_violations = api_violations + web_violations

    print(f"\n[Audit Summary]")
    print(f"Total Production Files Inspected: {len(list(PROD_API_DIR.rglob('*.py'))) + len(list(PROD_WEB_DIR.rglob('*.ts*')))}")
    print(f"Total Suspicious Flags Detected:   {len(all_violations)}")

    if all_violations:
        print("\n" + "!" * 75)
        print("VIOLATIONS DETECTED IN PRODUCTION INFERENCE CODE:")
        print("!" * 75)
        for v in all_violations:
            print(f"File: {v['file']}:{v['line']}")
            print(f"Reason: {v['reason']}")
            print(f"Code:   {v['content']}")
            print("-" * 50)
        sys.exit(1)
    else:
        print("\n" + "=" * 75)
        print("[PASS] AUDIT PASSED: ZERO HARDCODED DEMO KNOWLEDGE IN PRODUCTION CODE")
        print("[PASS] AUDIT PASSED: GROUND-TRUTH IS STRICTLY ISOLATED TO TESTS/EVAL")
        print("=" * 75)
        sys.exit(0)

if __name__ == "__main__":
    main()
