# Risk Register

**Purpose**: Document all identified risks, mitigation strategies, and decision rationale. Consult with professors/practitioners before major pivots.

**Last Updated**: 2026-05-20
**Review Cadence**: Every milestone completion
**Status**: Work in Progress (v0.5)

---

## R1: Decimal Precision Policy

**Risk**: Mismatch between Python `float64` and Lean numeric types causes NAV discrepancies.

**Severity**: 🔴 Critical (breaks verification)

**Mitigation Strategy** ✅ DECIDED:
- **Lean**: Use scaled `Int` (basis points: `Int` × 10,000 for 4 decimals)
  - Type: `structure Price where basisPoints : Int`
  - Rationale: Exact decimal arithmetic, standard in financial systems, fast, provably correct
- **Python**: Use `decimal.Decimal` (arbitrary precision)
  - Convert to int (basis points) at FFI boundary
  - Never use `float` for accounting/cash/prices
- **Float exception**: Black-Scholes/Greeks use `float` for performance, then convert to `Decimal`
- **Tolerance**: Allow ε = 0.0001 (1 basis point) in verification for numerical stability

**Implementation**: v0.2-numeric

**References**:
- Industry practice: Java `BigDecimal`, Python `decimal`, Rust `rust_decimal`
- Lean community: Scaled integers recommended for financial computing
- Research: See DECISIONS.md ADR-001

**Open Questions** 🤔:
- Should options Greeks use higher precision (8 decimals)? → Consult quant researchers
- How to handle very small probabilities in CVaR? → May need `Rat` for tail calculations

**Alternatives Considered**:
1. `Rat` everywhere: Exact fractions, but denominators grow unpredictably (GCD overhead)
2. `Float` everywhere: Fast but non-deterministic, rounding errors accumulate
3. Mixed (current choice): Exact for accounting, approximate for analytics

---

## R2: Lean Proof Difficulty Underestimation

**Risk**: Invariants assumed "easy" require deep Mathlib expertise, blocking progress.

**Severity**: 🟠 High (schedule risk)

**Status**: ✅ Resolved (v0.5). 26 theorems proved: 12 in `Invariants.lean`, 6 in
`SettlementInvariants.lean`, and 8 payoff theorems in `quant-core/QuantCore/OptionInvariants.lean`.
Zero `sorry`, zero `axiom`. The hardest theorem was `settlement_value_formula`
(unifies ITM/OTM expiry into a single statement); proved using `omega` + `simp`.

**Mitigation Strategy** ✅ DECIDED:
- **Prioritization**: Prove simple invariants first (NAV identity, conservation)
- **Defer complex proofs**: Self-financing requires field theory; defer to later milestones
- **Escape hatches**: Use `axiom` temporarily with `-- TODO: prove` comment
  - CI warning (not failure) if `axiom` count increases
- **Expert consultation**: Budget time to ask on Lean Zulip or engage theorem-proving consultant
- **Incremental approach**: Prove special cases first (e.g., single-asset portfolio), generalize later

**Implementation**: v0.3-trades (simple), v0.4 (all accounting + options theorems)

**Monitoring**:
- Track `axiom` count in CI
- Allocate 20% time buffer in proof-heavy milestones

**Open Questions** 🤔:
- Which invariant is hardest? → NAV identity likely easiest, self-financing hardest
- Should we hire a Lean expert consultant? → Decide after v0.3 if blocked >1 week

**Fallback**: Accept `axiom` for v1.0, target full proofs in v2.0

---

## R3: DerivaGem Reference Mismatch

**Risk**: Spreadsheet pricing differs from Python Black-Scholes due to undocumented quirks.

**Severity**: 🟢 Low (reference issue, not system risk)

**Status**: ✅ Mitigated (v0.4). Pricer matches Hull Ex 15.6 reference vectors within `abs=0.01`
on price and `abs=0.001` on delta. See `tests/test_pricer.py` for the reference test suite.

**Mitigation Strategy** ✅ DECIDED:
- **Use as sanity check only**: DG400a is not ground truth, just a reference
- **Document divergences**: Track known differences in `docs/architecture/pricer_validation.md`
- **Analytical benchmarks**: Test against known solutions (European call put-call parity, ATM straddle)
- **Multiple references**: Compare to QuantLib, OptionMetrics formulas
- **Tolerance**: Allow 1% difference from DG spreadsheets (document when exceeded)

**Implementation**: v0.4 (pricer validated against Hull/DerivaGem)

**Testing Strategy**:
- Unit tests: Black-Scholes matches analytical solutions (ATM, ITM, OTM)
- Integration tests: Compare Python pricer to DG spreadsheet on sample grid
- Log warnings (not errors) for >1% divergence

**Open Questions** 🤔:
- Should we reverse-engineer DG spreadsheet formulas? → No, too time-consuming
- Which pricer to trust when they disagree? → Analytical solution > QuantLib > DG

**Fallback**: If systematic divergence found, add adjustment factor (document in cert metadata)

---

## R4: JupyterBook Execution Timeout

**Risk**: Notebooks with large backtests time out during `jupyter-book build`.

**Severity**: 🟢 Low (documentation issue)

**Mitigation Strategy** ✅ DECIDED:
- **Execution timeout**: Set `execution_timeout: 300` (5 min) in `book/_config.yml`
- **Cache mode**: Use `execution_mode: cache` for slow notebooks
  - Execute manually, commit outputs (`.ipynb` with cells executed)
  - JupyterBook skips re-execution if cached
- **Smaller datasets**: Use 20-step backtests in docs, not 1000-step
- **Pre-execution**: For expensive notebooks, run `make docs-execute` locally before commit

**Implementation**: v0.4 (config set); pre-execute credibility exhibit notebooks before commit

**Workflow**:
1. Develop notebook interactively
2. Execute with full data
3. Clear outputs, save
4. Run `make docs-execute` (executes & caches)
5. Commit with outputs
6. CI builds book in cache mode (fast)

**Open Questions** 🤔:
- Should we use Binder for live execution? → Requires Docker image, defer to future
- Separate "live" vs "static" notebooks? → Tag expensive ones with warning banner

**Fallback**: Pre-execute all notebooks, commit outputs, disable execution in CI

---

## R5: uv Lock File Drift (Cross-Platform)

**Risk**: Team members on Linux/macOS/Windows get different dependency versions.

**Severity**: 🟡 Medium (reproducibility)

**Mitigation Strategy** ✅ DECIDED:
- **Pin Python version**: `.python-version` (3.12)
- **Universal lock**: Use `uv lock --universal` (cross-platform resolution)
- **CI matrix**: Test on Linux, macOS, Windows (GitHub Actions)
  - Workflow: `.github/workflows/python.yml` with `matrix: [ubuntu, macos, windows]`
- **Lockfile in git**: Commit `uv.lock`
- **Regular updates**: `uv lock --upgrade` monthly (scheduled PR)

**Implementation**: v0.1-scaffold (lockfile and CI matrix)

**Testing**:
- CI runs on all platforms
- Developer setup: `make setup` verifies lockfile hash

**Open Questions** 🤔:
- Support Python 3.11 as well? → Stick to 3.12 for simplicity (reassess in v1.0)
- Pin transitive dependencies? → uv handles this automatically

**Fallback**: If platform issues persist, use Docker for dev environment (heavier but reproducible)

---

## R6: Makefile Portability (Windows)

**Risk**: The Makefile does not function on Windows without WSL/Cygwin.

**Severity**: 🟡 Medium (accessibility)

**Mitigation Strategy** ✅ DECIDED:
- **Require WSL on Windows**: Document in CONTRIBUTING.md
  - WSL 2 is standard on Windows 10/11, widely adopted
- **Alternative**: Provide PowerShell script `scripts/setup.ps1` for Windows users (future)
  - Mirrors Makefile targets (`.\scripts\setup.ps1 build`)
- **Future**: Consider `justfile` (cross-platform Make alternative)
  - Defer to v0.15 based on user feedback
- **CI**: Windows job runs via WSL or PowerShell

**Implementation**: v0.1-scaffold (Makefile), future (PowerShell)

**Documentation**:
- CONTRIBUTING.md: "Windows users: use WSL or PowerShell scripts"
- README.md: Note WSL requirement

**Open Questions** 🤔:
- Invest in full Windows native support (batch/PowerShell)? → Wait for user requests
- Switch to `just` or `task` now? → Stick with Make (familiar), reassess in v0.15

**Fallback**: Docker-based dev environment (works everywhere, no Make needed)

---

## R7: Data Decryption Key Management

**Risk**: Decryption key for `data/` leaks via commit history or CI logs.

**Severity**: 🔴 Critical (security/compliance)

**Status**: ✅ Mitigated (v0.4). git-crypt unlock procedure is operational. Encrypted data files
(`fred_treasury.enc`, `wrds_sp500.enc`, `wrds_spx_options.enc`, `wrds_vix.enc`) and unencrypted
CSV/Parquet files are versioned in the repo. Key handoff uses secure channel only.

**Mitigation Strategy** ✅ DECIDED:
- **Never commit key**: Add to `.gitignore` and `data/.gitignore`
  - Pattern: `*.key`, `*.pem`, `secrets.*`
- **git-crypt**: Encrypt data files at rest in repo
  - Setup: `git-crypt init`, add `data/.gitattributes`
  - Pattern: `*.csv filter=git-crypt diff=git-crypt`
- **Key handoff**: Secure channel only (Signal, 1Password share, GPG-encrypted email)
  - Document in `data/README.md`: "Request key via secure channel"
- **CI**: Use GitHub Secrets for decryption key
  - Workflow: `env: DECRYPT_KEY: ${{ secrets.DATA_DECRYPT_KEY }}`
  - Never log key or decrypted data
- **Access control**: Limit who can access GitHub Secrets (admin only)
- **Rotation**: Rotate key if leaked (re-encrypt all data)

**Implementation**: v0.1-scaffold (git-crypt config), v0.4-data (unlock)

**Operational Procedure**:
1. New contributor requests access → secure key handoff
2. Run `git-crypt unlock /path/to/key` (one-time setup)
3. Data transparently encrypted/decrypted by git

**Monitoring**:
- Audit git history for accidental key commits (`git log -p | grep -i "key"`)
- GitHub Secret access logs

**Open Questions** 🤔:
- Use hardware key (YubiKey) for extra security? → Overkill for academic project, reassess if productionizing
- Separate keys for dev vs. CI? → Yes, different keys (principle of least privilege)

**Fallback**: If git-crypt too complex, use external encrypted storage (S3 with KMS, decrypt locally)

---

## R8: Empirical Credibility Work Scope Creep

**Risk**: The four credibility levers (P&L attribution, Leland sweep, QuantLib A-B, stress run)
each require external tools or data that may be harder to acquire or validate than expected.

**Severity**: 🟡 Medium (schedule risk for credibility work)

**Status**: Open. Accounting module is complete (v0.5); credibility levers are the remaining
open work.

**Mitigation Strategy**:

- **Lever 1 (P&L attribution)**: No external data needed; runs on GBM. Low risk.
- **Lever 2 (Leland 1985)**: Requires only the GBM simulator, already present. Low risk.
- **Lever 3 (QuantLib A-B)**: Requires installing QuantLib Python. Medium risk (build friction on macOS).
- **Lever 4 (WRDS stress run)**: Requires WRDS OptionMetrics access and git-crypt unlock. High risk (data dependency).

**Fallback**: Ship Levers 1–3 as the JupyterBook exhibits if WRDS data is unavailable.
Lever 4 can be a deferred proof-of-concept once data access is confirmed.

---

## Summary Risk Matrix

| ID | Risk | Severity | Status | Milestone |
|----|------|----------|--------|-----------|
| R1 | Decimal precision | 🔴 Critical | ✅ Mitigated | v0.2-nav |
| R2 | Proof difficulty | 🟠 High | ✅ Resolved | v0.5 |
| R3 | DG mismatch | 🟢 Low | ✅ Mitigated | v0.4 |
| R4 | Docs timeout | 🟢 Low | ✅ Mitigated | v0.4 |
| R5 | uv lock drift | 🟡 Medium | ✅ Mitigated | v0.1-scaffold |
| R6 | Windows Make | 🟡 Medium | ✅ Mitigated | v0.1-scaffold |
| R7 | Key leak | 🔴 Critical | ✅ Mitigated | v0.1, v0.4 |
| R8 | Credibility lever scope creep | 🟡 Medium | 🔄 Open | credibility plan |

**Review Schedule**: Update after each credibility lever ships; full review before publishing exhibits.

---

## Notes

This is a living document. Risks are documented candidly to facilitate informed decision-making. Consultation with domain experts (professors, practitioners) is encouraged before making major architectural changes.
