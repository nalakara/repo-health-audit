# DataFactor scoring variables — extracted from two real reports

Source material for the repo-health-audit skill rubric. Extracted 2026-10-24 from:
- nalakara/borga report (text, pasted by Yudhan): score 39.6
- nalakara/Brewing-Dungeon report (full-page PDF): score 33

DataFactor's own description of its method: "Live score: structural signals plus a
Claude judgment pass over a read-only copy of the repository." (judged by claude-sonnet-5)
=> Mirror design for our skill: mechanical scanner + agent judgment pass.

## Global / header metrics
- repo_type tag: backend | full-stack | ... (per-repo classification)
- source_loc: source lines of code (borga 5,159 total LOC reported; Brewing-Dungeon source_loc 2,507)
- volume: composite size metric (borga 18.2; Brewing-Dungeon 9)
- mining_rank: 0 = very low (how mineable the history is)
- task_capacity: ~N — estimated count of self-contained engineering tasks minable from
  history; a task = a change that arrives WITH the tests that prove it.
  "Value scales with task capacity, and quality times zero tasks is zero."
- overall_score 0-100 + letter grade; offer threshold = 70
- estimated_payout: $0 below the quality bar regardless of volume; above the bar
  "up to $4,800 total per contributor" (approximate, non-binding)

## Buyer-fit signals (5, shown as pass / warn / fail)
1. builds_and_tests_at_head — a runnable test suite exists at HEAD (heaviest signal)
2. task_capacity — mineable commits exist (see above)
3. genuine_history — multi-author back-and-forth > single-author burst
4. self_contained — container setup detected (Dockerfile/devcontainer); buyers sandbox repos
5. not_a_demo — nothing suggests a demo or template

## Dimensions (letter-coded; a larger A..K taxonomy, subset shown per repo)
Observed letters: B Test Coverage, C Code Cleanliness, D Architecture & Robustness,
E Dependency Health, F Docs & Onboarding, H CI/CD Maturity, I Security Hygiene,
K History & Maintenance.

### B · Test Coverage
- test_spec_files (count), test_framework[] (pytest, vitest, ...)
- test_source_ratio (borga 1:8; Brewing-Dungeon 0)
- coverage_tooling (pytest-cov etc.), coverage gate (--cov-fail-under)
- ci_enforcement: tests actually run in CI

### C · Code Cleanliness
- has_lint_config, linters_and_formatters{} (ruff, flake8, eslint, prettier)
- god_files_over_500_loc / top_largest_files (name + LOC of largest files)
- median_file_loc (borga 88)
- note: tsc --noEmit used as 'lint' script does NOT count as lint config

### D · Architecture & Robustness
- layering (service/repositories/models/cli/web separation)
- logging_framework (null = print/console.error only) — structured logging wanted
- error handling quality (exceptions swallowed into generic 500 = negative)
- input_validation: schema validation at boundaries (pydantic models, zod);
  input_validation_patterns[]; unvalidated req.body destructuring = negative
- health/metrics endpoint presence (/api/health counts positively)
- secrets kept server-side / env-based proxy pattern counts positively

### E · Dependency Health
- lockfiles_found[] (poetry.lock, uv.lock, package-lock.json, ...)
- package_managers[] detected (pip/poetry; npm/yarn/pnpm)
- direct_runtime_deps count, dev deps count, pinned vs lower-bound version specs
- dep_update_tooling: dependabot.yml / renovate.json ('none' = negative)
- audit tooling (pip-audit, npm audit, safety)

### F · Docs & Onboarding
- README presence + line count + sections (install/run/env/features/architecture/test command)
- env_example_file (.env.example) presence
- env_vars_in_example vs env_vars_referenced_in_source -> env_vars_missing_from_example[]
- CONTRIBUTING, CHANGELOG presence
- Dockerfile / devcontainer presence

### H · CI/CD Maturity
- ci_present (bool), ci_config_files[]
- what CI runs: install, lint, typecheck, tests, coverage gate, security audit
- action version pinning (e.g. checkout@v4), dependency caching

### I · Security Hygiene
- hardcoded_secret_hits (count from secret scan)
- env_files_committed[] (.env committed = negative)
- secrets handled via env vars / BYOK pattern (positive)
- boundary validation beyond framework defaults

### K · History & Maintenance
- git_stats: total_commits, human_authors (count), span_days, tag_count, releases
- conventional_rate_last_200 (share of conventional-commit prefixes)
- cadence: small focused commits, feature+tests in same commit, PR-based flow
- bulk/mixed commits (formatting+refactor+feature in one) count negatively

## Fix-list format (their output template — worth mirroring)
Each fix: title, impact tag (high/medium/low), optional "payout impact" flag,
dimension letter tag, one evidence line citing the measured variables,
then numbered concrete sub-steps (exact files/commands to run).

## Recurring highest-impact fixes (both reports)
1. Ship features with their tests, small focused commits (payout, high)
2. Fresh-clone path works: install + build + test green from README alone (payout, high)
3. Sustained real increments over time; multi-author if a team exists (payout, medium)
4. Add CI pipeline: lint + typecheck + tests on every PR (high)
5. Commit lockfile + dependency update tooling (medium)
6. Test suite for core logic + coverage tooling/gate (high)
7. Structured logging + health endpoint (medium)
8. .env.example complete vs referenced env vars (low-medium)
9. Split god files >500 LOC (low)

## Notes
- Brewing-Dungeon per-dimension: Architecture 45, Test Coverage 3, Cleanliness 30,
  Docs 60, Security 55, Dependency 25, CI/CD 0, History 20.
- borga per-dimension: Architecture 45, Tests 45, Security 45, Docs 55,
  Cleanliness 55, History 25, Dependency 20, CI/CD 0.
- Privacy note from their own page ("Your code stays yours" §3): the submitted
  token IS saved with the browser session and used for "read-only repository
  access and sales follow-up" — despite the token page saying "never stored".
  => Always delete the token right after scoring.
