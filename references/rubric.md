# Scoring rubric for repo-health-audit

Calibrated against two real DataFactor reports (borga 39.6, Brewing-Dungeon 33).
Scores are our own calibration: expect a ballpark match with any external
scorer, not an exact one. The trend of a repo's score over time is the signal
that matters, so apply the bands exactly as written on every run.

Each dimension scores 0 to 100 from the sub-checks below. Metrics come from
`scripts/audit_repo.py`. Where a sub-check says judgment, the agent inspects
the code and cites file-level evidence, the same way DataFactor pairs
structural signals with a judgment pass.

## Overall score

Weighted mean of the eight dimensions:

- D Architecture and Robustness × 0.18
- B Test Coverage × 0.18
- K History and Maintenance × 0.14
- F Docs and Onboarding × 0.12
- C Code Cleanliness × 0.12
- I Security Hygiene × 0.10
- E Dependency Health × 0.08
- H CI/CD Maturity × 0.08

Grade bands: A 85+, B 70 to 84, C 55 to 69, D 40 to 54, F below 40.
(DataFactor's paid-offer threshold of 70 is a useful reference line.)

## B · Test Coverage

- Test to source file ratio, from `test_source_ratio` (source files per test file):
  no tests 0, worse than 12 → 15, 8 to 12 → 25, 4 to 8 → 35, better than 4 → 45
- Test framework configured (`test_frameworks` non-empty): +10
- Coverage tooling present (`coverage_tooling` non-empty): +15
- Coverage gate enforced (`coverage_gate` true): +10
- CI runs the tests (`ci_runs.tests`): +20
- Judgment: up to +10 when tests exercise real behavior (services, endpoints,
  calculations) rather than trivial asserts, or down to −10 for hollow tests

## H · CI/CD Maturity

- No CI (`ci_present` false): 0 for the whole dimension
- CI present: 30
- CI runs tests: +25
- CI runs lint: +15
- CI runs typecheck: +10
- CI runs coverage: +10
- CI runs a security audit: +10

## E · Dependency Health

- Manifest present and parseable (`manifests` non-empty): 10
- Lockfile committed (`lockfiles_found` non-empty): +35
- Version discipline, from `version_spec_styles`: pinned plus caret at least
  80 percent of specs → +25, 50 to 80 percent → +15, under 50 percent → +5
- Update tooling (`dep_update_tooling` dependabot or renovate): +20
- Audit tooling wired in CI or scripts: +10

## F · Docs and Onboarding

- README exists: 10, and README of 90 lines or more: +10 (40 to 89 lines: +5)
- README sections, from `readme_sections`: install +5, run +5, env +5,
  features +5, architecture +5 (section subtotal capped at 25)
- `.env.example` present: 15, and complete (no `env_vars_missing_from_example`): +10
  (present but incomplete: +3 instead of +10)
- CONTRIBUTING present: +5
- CHANGELOG present: +5
- Dockerfile or devcontainer present: +5

## C · Code Cleanliness

- Lint config present (`has_lint_config`): 30
- Formatter configured (prettier, black, or a formatter entry in
  `linters_and_formatters`): +15
- God files (`god_files_over_500_loc`): none +25, one +12, two +5, three or more 0
- Median file size (`median_file_loc`) at most 150 lines: +15, 151 to 300: +8
- Judgment: up to +15 for consistent structure and naming, down for mixed
  conventions and dead code

## I · Security Hygiene

- No hardcoded secret hits (`hardcoded_secret_hits` 0): 35
  (1 to 2 hits: 15, more than 2 or any private key file: 0)
- No env files committed (`env_files_committed` empty): +20
- Secrets flow through env vars with a complete `.env.example`: +15
- Boundary input validation, from `architecture_hints.validation_libraries`
  plus judgment on actual usage at API and form boundaries: up to +20
- Dependency audit tooling present: +10
- Any real secret found is reported as file and line count only, never the value

## D · Architecture and Robustness

- Clear layering, from `architecture_hints.layer_dirs` plus judgment on the
  module layout: up to 30
- Structured logging, from `logging_library_files` versus
  `print_or_console_files`: up to 20 (logging in most files 20, print or
  console dominant 0 to 5)
- Error handling quality (judgment: exceptions swallowed into generic errors
  score down, typed and logged errors score up): up to 20
- Input validation at boundaries (schema library present and used): up to 20
- Health or metrics endpoint (`health_endpoint_files` non-empty): 10

## K · History and Maintenance

- Total commits: 100 or more → 25, 30 to 99 → 18, 10 to 29 → 12, 4 to 9 → 6, under 4 → 2
- Span of history (`span_days`): 180 or more → 20, 90 to 179 → 14, 30 to 89 → 9, under 30 → 4
- Human authors: 3 or more → 15, 2 → 10, 1 → 4
  (two identities of the same person count as one author)
- Active day ratio (`active_days` over `span_days`): 0.3 or more → 10,
  0.15 to 0.3 → 6, under 0.15 → 3
- Tags (`tag_count`): 5 or more → 10, 1 to 4 → 5, none → 0
- Conventional commit rate (`conventional_rate_last_200` × 10): up to 10
- Mineable share (`commits_touching_tests_and_source` over `commits_sampled`):
  0.3 or more → 10, 0.15 to 0.3 → 6, above 0 → 3, none → 0

## Buyer-fit signals (report alongside the score)

- Builds and tests at HEAD: `buyer_fit_raw.builds_and_tests_at_head`
- Task capacity: `buyer_fit_raw.task_capacity_proxy_mineable_commits`,
  the count of non-root commits that change source and tests together
- Genuine history: multi-author and spread over time, from the history metrics
- Self-contained: `buyer_fit_raw.self_contained_container`
- Not a demo: judgment, from the README and the shape of the history
