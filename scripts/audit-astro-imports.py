"""
Focused high-risk helper check.
Every helper in HIGH_RISK has previously caused a "ReferenceError" by being
edited away from an import line while still being used in frontmatter.
For each .astro file, check whether HIGH_RISK identifiers are *used* in the
frontmatter server-side block; if used, they MUST appear in some `import {...}`
from '../lib/i18n.ts' / '../lib/destinations.ts' / '../lib/origins.ts' / etc.

Exits 0 if clean, 1 if anything is used-but-not-imported.
"""

import os, re, sys

HIGH_RISK = {
    # from src/lib/i18n.ts
    "t","layerName","originLabel","productName","destLabel","descLabel",
    "LANGS","PRODUCTS","ORIGINS","type Lang",
    # from src/lib/destinations.ts
    "destLabel",
    # from src/lib/origins.ts
    "destOptionsFor","US_EMBARGOED","ORIGINS",
    # from src/lib/calc.ts
    "computeStack","type Rate","sec232Matches",
    # from JSON default-imports (named-vs-default trap)
    # – these come in via `import <name> from '...json'` – we flag them separately.
    "BRIEF","brief",
    # ad-hoc helper once defined inside frontmatter
    "LAYER_COLOR","DEMO_HTS","DEFAULT_DEST","demoRates","fullRates",
    "_popularSet","_restOrigins","PINNED_ORIGINS","POPULAR_ORIGINS","LAYER_COLOR",
}

SKIP_DIRS = {"node_modules",".git","dist",".astro",".next"}


def frontmatter(src: str):
    if not src.startswith("---\n"): return ""
    end = src.find("\n---", 4)
    return src[4:end] if end > 0 else ""


def server_block(fm: str) -> str:
    """Drop <script> blocks and HTML/CSS so we audit only SSR-targeted JS."""
    return re.sub(r"<script[^>]*>.*?</script>", "", fm, flags=re.DOTALL)


def strip_strings(s: str) -> str:
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    s = re.sub(r"//[^\n]*", "", s)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.DOTALL)
    s = re.sub(r"'(?:\\.|[^'\\])*'", "''", s)
    s = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    # IMPORTANT: Astro frontmatter contains no backticks (those only live in
    # <script>); drop them defensively anyway.
    s = re.sub(r"`(?:\\.|[^`\\])*`", "``", s, flags=re.DOTALL)
    # Drop JSX expressions { ... } that interpolate into HTML — they're not
    # top-level identifiers, just inline JS expressions. Conservative: we only
    # drop nested { ... } inside attributes; top-level ${} inside backticks
    # was already removed.
    return s


def imports_in(fm: str):
    """Return dict of {module: [names]} for every import in the frontmatter."""
    out = {}
    for line in fm.splitlines():
        line = line.strip()
        m = re.match(r"^import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]+)['\"]", line)
        if m:
            out.setdefault(m.group(2), []).extend(
                t.strip().split(" as ")[-1].strip() for t in m.group(1).split(",")
            )
            continue
        m = re.match(r"^import\s+([A-Za-z_]\w*)\s*(?:,\s*\{([^}]+)\})?\s+from\s+['\"]([^'\"]+)['\"]", line)
        if m:
            mod = m.group(3)
            if m.group(1): out.setdefault(mod, []).append(m.group(1))
            if m.group(2):
                out.setdefault(mod, []).extend(
                    t.strip().split(" as ")[-1].strip() for t in m.group(2).split(",")
                )
    return out


def local_defs(fm: str):
    """Names declared inside this frontmatter via const/let/var/function."""
    out = set()
    decl_re = re.compile(r"^\s*(?:const|let|var|function)\s+(?:\{([^}]+)\}|([A-Za-z_]\w*))", re.MULTILINE)
    for m in decl_re.finditer(fm):
        if m.group(1):
            for tok in m.group(1).split(","):
                tok = tok.strip().split(" as ")[-1].strip()
                if tok.isidentifier(): out.add(tok)
        elif m.group(2):
            out.add(m.group(2))
    return out


def walk(root):
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".astro"): yield os.path.join(dp, f)


def audit(path):
    src = open(path, encoding="utf-8").read()
    fm = frontmatter(src)
    if not fm: return []
    server = strip_strings(server_block(fm))
    imports = imports_in(fm)
    imported = set().union(*[set(v) for v in imports.values()]) if imports else set()
    local = local_defs(fm)
    used = [tok for tok in HIGH_RISK if re.search(r"\b" + re.escape(tok) + r"\b", server)]
    missing = [tok for tok in used if tok not in imported and tok not in local]
    return missing


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "src"
    rc = 0
    for p in walk(root):
        bad = audit(p)
        if bad:
            rc = 1
            print(f"!! {p}: USED-BUT-NOT-IMPORTED: {sorted(set(bad))}")
    if rc == 0:
        print("OK: high-risk helpers used in server-scope are all imported.")
    sys.exit(rc)


if __name__ == "__main__":
    main()
