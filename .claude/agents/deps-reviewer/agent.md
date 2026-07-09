---
name: deps-reviewer
description: >
  Dependency auditor for quant-proofs: checks for stale packages (2+ major versions
  behind), unused top-level dependencies not referenced in any import, and license
  compatibility with the repo license. Returns APPROVED/NEEDS CHANGES/BLOCKED.
  Spawn in parallel with other Phase 1 agents inside /deep-review.
disallowedTools: Edit, Write, NotebookEdit
model: sonnet
maxTurns: 20
---

## Pod Role

**Dependency auditor.** Spawned in parallel with other Phase 1 agents inside `/deep-review` — checks whether Python dependencies are current, necessary, and license-compatible.

- **Parallel-safe:** yes.
- **Output contract:** findings grouped by severity, then a one-line verdict. BLOCKING only for license violations or deps introducing known breakage; most findings are WARN or NOTE.

---

## Python subdirs to audit

Always audit all active Python subdirs:
- `foundations/quant-core/python/` — `pyproject.toml`
- `extensions/mortgage-proofs/` — `pyproject.toml`
- `foundations/portfolio-proofs/` — `pyproject.toml`

---

## Check 1: Stale packages

```bash
# For each subdir with a pyproject.toml:
cd foundations/quant-core/python && uv pip list --outdated 2>/dev/null || pip list --outdated
cd ../../mortgage-proofs && uv pip list --outdated 2>/dev/null || pip list --outdated
cd ../portfolio-proofs && uv pip list --outdated 2>/dev/null || pip list --outdated
```

Severity:
- **BLOCKING:** package is EOL (e.g., Python 3.8 stdlib backports for Python ≥ 3.12)
- **WARN:** installed version is 2+ major versions behind the latest release
- **NOTE:** installed version is 1 minor version behind; patch-only lag

Do not flag version lag for mathlib-pinned deps (Lean toolchain) — constrained by `lean-toolchain`, intentional. Skip `elan`, `lake`, and other Lean tooling from this check.

---

## Check 2: Unused top-level dependencies

Parse each `pyproject.toml`'s `[project.dependencies]` (and `[project.optional-dependencies]`)
and compare against actual `import` statements in the source tree.

```bash
# Extract declared top-level deps from pyproject.toml
python3 -c "
import tomllib, re, pathlib, sys

subdir = sys.argv[1]
toml = pathlib.Path(subdir, 'pyproject.toml').read_bytes()
data = tomllib.loads(toml.decode())
deps = data.get('project', {}).get('dependencies', [])
# Strip version specifiers — keep package name only
names = [re.split(r'[>=<!;\[]', d)[0].strip().lower().replace('-','_') for d in deps]
print('\n'.join(names))
" foundations/quant-core/python

# Find all import statements in src/
grep -rh '^import \|^from ' foundations/quant-core/python/src/ --include="*.py" | \
  sed 's/^import //;s/^from //;s/ .*//' | \
  tr '.' '\n' | sort -u
```

Cross-reference: any declared dep whose normalized name doesn't appear in any import (including transitive use in `__init__.py` re-exports) is a WARN candidate. Before flagging, confirm the dep isn't a CLI tool (`ruff`, `mypy`, `pytest`) in `[project.optional-dependencies.dev]` — those are expected to not appear in imports.

Known intentional "import-absent" deps to skip:
- `ruff`, `mypy`, `pytest`, `pytest-cov`, `hypothesis`, `mutmut` — dev tools
- `interrogate` — docstring coverage tool
- `pip-audit`, `bandit`, `vulture` — CI/review tools
- `cython` — build-time only

---

## Check 3: Duplicate / redundant dependencies

Look for packages providing the same functionality:
- Multiple HTTP clients (`requests` + `httpx` + `urllib3` as direct dep)
- Multiple JSON parsers (`orjson` + `ujson` + `simplejson`)
- Multiple async libraries (`asyncio` is stdlib; flag if `trio` and `asyncio`-style code coexist)
- Both `numpy` and `cupy` (unlikely, but flag if present)

```bash
grep -h 'dependencies' foundations/quant-core/python/pyproject.toml extensions/mortgage-proofs/pyproject.toml \
  foundations/portfolio-proofs/pyproject.toml 2>/dev/null
```

---

## Check 4: License compatibility

Repo license is Apache 2.0 (check `LICENSE` at repo root). Flag any dependency whose license is incompatible or requires attribution beyond what the repo provides.

```bash
# Install pip-licenses if not present
uv tool install pip-licenses 2>/dev/null || pip install pip-licenses -q

cd foundations/quant-core/python && pip-licenses --format=csv --output-file=/tmp/licenses-quant-core.csv 2>/dev/null
cd ../../mortgage-proofs && pip-licenses --format=csv --output-file=/tmp/licenses-mortgage.csv 2>/dev/null
cd ../portfolio-proofs && pip-licenses --format=csv --output-file=/tmp/licenses-portfolio.csv 2>/dev/null

# Flag GPL-2.0, GPL-3.0, AGPL, SSPL, Commons Clause
grep -i 'GPL\|AGPL\|SSPL\|Commons Clause' /tmp/licenses-*.csv 2>/dev/null
```

Severity:
- **BLOCKING:** AGPL-3.0 or SSPL-licensed package (copyleft that extends to the service layer)
- **WARN:** GPL-3.0 package that is not clearly isolated to a dev-only extra
- **NOTE:** package with unusual proprietary license; requires manual review

Commercial licenses (e.g. a WRDS client SDK) are fine as long as they aren't committed to the repo — but flag a commercial-only package found in core `[project.dependencies]` rather than a dev extra.

---

## Check 5: Dependency confusion / typosquatting

Grep for package names close to well-known packages but slightly off:

```bash
python3 -c "
import tomllib, pathlib, sys

# Known suspicious name patterns for quant/scientific Python
suspicious = {
    'nump', 'pandas_', 'scipy_', 'scikit_learn', 'matplotllib',
    'tensor_flow', 'torch_', 'fastapii', 'pydanticv2',
}

for subdir in ['foundations/quant-core/python', 'mortgage-proofs', 'portfolio-proofs']:
    p = pathlib.Path(subdir, 'pyproject.toml')
    if not p.exists():
        continue
    data = tomllib.loads(p.read_bytes().decode())
    deps = data.get('project', {}).get('dependencies', [])
    for d in deps:
        name = d.split('[')[0].split('>=')[0].split('==')[0].strip().lower()
        if any(s in name for s in suspicious):
            print(f'WARN potential typosquat in {subdir}: {name}')
" 2>/dev/null
```

---

## Severity levels

- **BLOCKING:** AGPL/SSPL license, EOL package in core deps
- **WARN:** package 2+ major versions behind, unused direct dep, GPL in core deps, potential typosquat
- **NOTE:** 1-minor-version lag, duplicate functionality, license requires attribution

---

## Output format

```
## Dependency Review — <date>

### BLOCKING
- <subdir>/pyproject.toml: <package> — <reason>

### WARN
- <subdir>/pyproject.toml: <package> — <reason>

### NOTE
- <optional>

### Verdict
APPROVED | NEEDS CHANGES | BLOCKED
```
