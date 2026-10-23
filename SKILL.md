---
name: repo-health-audit
description: Audit a code repository against eight engineering health dimensions (architecture, test coverage, security hygiene, docs and onboarding, code cleanliness, history and maintenance, dependency health, CI/CD maturity) with a mechanical scanner plus a judgment pass, producing a 0 to 100 score and an impact-ranked fix list. Use when asked to score, audit, grade, or review a repository's health or code quality, or to compare a repository before and after fixes.
---

# Repo Health Audit

## When to use this skill

- Audit a code repository the user owns or is evaluating and report an objective health score across eight dimensions, with the gaps ranked by impact.

- Run it on a local repository path, or clone the repository first when the user gives a GitHub URL or repo name.

- Re-run it on the same repository after fixes land, and compare against the previous report to show the delta.

## Run the mechanical scan

- Run `python3 scripts/audit_repo.py <repo-path> --out <workdir>/metrics.json` from the skill folder (adjust the script path to where the skill is installed) and read the JSON it writes.

- Add the `--history-secrets` flag only when the user asks for a history deep scan, because it walks the full git log and can take minutes on a large repository.

- Treat the scanner output as evidence, not as the verdict. It counts and detects, and it never prints secret values, only file paths and hit counts.

- Fall back to reading the repository by hand when the scanner fails on an unusual layout, and say which metrics are hand-collected in the report.

## Score with the rubric

- Read `references/rubric.md` (beside this file) and apply its bands exactly as written, dimension by dimension, from the scanner metrics.

- Keep the calibration stable across runs. A score that moves because the rubric moved teaches the user nothing.

- Read `references/datafactor-variables.md` when a dimension needs interpretation help or the user asks how an outside buyer would see the repository.

## Add the judgment pass

- Inspect the code for the parts a scanner cannot weigh, mainly layering, error handling, logging quality, input validation at boundaries, and whether tests exercise real behavior.

- Cite file-level evidence for every judgment adjustment, such as the file that swallows exceptions or the service with no tests.

- Check whether multiple git author identities are actually the same person, and count them once when they are.

- Adjust only within the ranges the rubric allows, and name the adjustment and its reason in the report.

## Write the report

- Open with the repository name, the overall score and grade, source LOC, the volume estimate, and the task capacity count of mineable commits.

- List the five buyer-fit signals as pass, warn, or fail, each with a one line reason drawn from the metrics.

- List all eight dimensions with their scores and one evidence line each, quoting the measured variables the way a score report would.

- Close with the fix list, ordered by expected score impact, where each fix names its dimension, the evidence behind it, and concrete steps with exact files and commands.

- Save the report as a markdown file next to the metrics JSON when the audit is part of a larger piece of work, and always deliver the summary in chat.

## Guardrails

- Audit only repositories the user owns or has the right to evaluate, and keep the work read-only. Never push, commit, or open issues in an audited repository unless the user asks for the fixes themselves.

- Report a secret finding as file and count only. Never copy the value into the report, the chat, or any file.

- Present the score as an independent calibration that mirrors published buyer criteria (DataFactor's repository scoring is the reference model). Never present it as a DataFactor score or as a promise of licensing value.

- Skip urgency framing. The point of the audit is the fix list and the trend over time, not a deadline.
