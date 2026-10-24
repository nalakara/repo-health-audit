**English** | [Bahasa Indonesia](README.id.md)

# Repo Health Audit

**Your repo looks finished. Would it survive a buyer's scorecard?**

Repo Health Audit is a free agent skill that grades any code repository from 0 to 100 across eight engineering health dimensions, shows you exactly where the points are leaking, and hands you a fix list ranked by impact. Run it before a buyer, a client, or a reviewer runs theirs.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)
![Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)
![Mode](https://img.shields.io/badge/mode-read--only-orange)
![Price](https://img.shields.io/badge/price-free-brightgreen)

## The problem it solves

Most repos do not fail on features. They fail on hygiene nobody checked: no tests, no CI, a lockfile that never got committed, an `.env.example` that quietly drifted from the code, a history of four giant commits. You cannot see it from inside the project, because you already know how everything works.

Meanwhile, the people evaluating your code from the outside, AI training data buyers, clients, technical reviewers, score exactly those things. Their reports are blunt, and by the time you read one, the first impression is already made.

Repo Health Audit gives you that outside score first, on your own machine, while you can still fix what it finds.

## What you get

Every audit produces one report with four parts:

1. **An overall score and grade** from 0 to 100, calibrated so that 70 is the line a serious buyer starts paying attention.
2. **Eight dimension scores**, each backed by measured evidence, not vibes.
3. **Five buyer-fit signals** (builds and tests at HEAD, task capacity, genuine history, self-contained, not a demo) marked pass, warn, or fail.
4. **A fix list ranked by expected score impact**, so you always know which repair buys you the most points per hour of work.

### A real run

This is an unedited result on a real public repository, produced by the skill running inside DeepSeek Harness:

```text
Repo Health Audit: prompt-brew
Overall Score: 39.9 / 100    Grade: F

D Architecture and Robustness    51
B Test Coverage                   0
K History and Maintenance        40
F Docs and Onboarding            50
C Code Cleanliness               48
I Security Hygiene               78
E Dependency Health              70
H CI/CD Maturity                  0

Top fix: add a Vitest test suite (largest single gain, in Test Coverage)
```

Brutal? Yes. Useful? Immediately. Every weakness is named, measured, and paired with the concrete fix. Cross-check: the same scanner, run under Muse on the same repository, returned identical metrics, and the eight dimension scores above add up under the rubric weights to exactly 39.9. The rubric does not move between runs or between agents.

## How it works

Two layers, the same architecture professional scoring services use:

1. **A mechanical scanner** (`scripts/audit_repo.py`) measures what can be counted: LOC, test ratios, CI presence, lockfiles, version pinning, env documentation gaps, god files, secret patterns, and the shape of your git history. It emits JSON. Python standard library only, zero dependencies to install.
2. **A judgment pass** by your agent, which reads the rubric and the code to weigh what a scanner cannot: layering, error handling, logging quality, and whether tests exercise real behavior. Every judgment cites file-level evidence.

Measurement first, opinion second, and the two never get mixed up.

## The eight dimensions

| Code | Dimension | Weight |
| --- | --- | --- |
| D | Architecture and Robustness | 0.18 |
| B | Test Coverage | 0.18 |
| K | History and Maintenance | 0.14 |
| F | Docs and Onboarding | 0.12 |
| C | Code Cleanliness | 0.12 |
| I | Security Hygiene | 0.10 |
| E | Dependency Health | 0.08 |
| H | CI/CD Maturity | 0.08 |

Scoring bands live in `references/rubric.md`. The full variable inventory behind the rubric, extracted from real published buyer score reports (DataFactor's assessment is the reference model, reverse-engineered from two real reports in October 2026), lives in `references/datafactor-variables.md`.

## Why teams keep the score, not just the report

- **It is a mirror, not a verdict.** Re-run it after fixes and the delta shows whether the work actually moved your repo, or just made it longer.
- **Your code never leaves your machine.** The audit runs locally and read-only. Secret findings are reported as file paths and hit counts, never as values.
- **No lock-in, no account, no token.** If you later choose to submit a repo to a third-party scorer, that is your decision, with a scoped token you delete afterwards (see the privacy note below).
- **It works where you already work.** One package, variants for every major agent host, shared scripts and references across all of them.

## Verified on

- **Muse**: built and tested here, discoverable as a native skill.
- **DeepSeek Harness (dsh)**: installed from this exact package and verified live in October 2026. Its prompt-brew report used metrics identical to a Muse-side scanner run on the same repository, and its dimension scores reconcile with the rubric weights to the decimal.

Packages are also included for Gemini CLI and Antigravity, Codex, Claude Code, and ChatGPT (see Install).

## Layout

- `SKILL.md` at the root is the standard agent-skills format (YAML frontmatter), used by Gemini CLI and Antigravity, Codex, DeepSeek Harness (dsh), Claude Code, and other compatible agents.
- `scripts/` and `references/` are shared by every variant.
- `claude/` holds the Muse variant: a frontmatter-free `SKILL.md` plus the `skill.yaml` descriptor Muse uses.
- `chatgpt/` holds paste-ready instructions for a Custom GPT or a Project, with the rubric and variable files uploaded as knowledge.

## Install

Clone this repository first, then run the block for your platform:

```bash
git clone https://github.com/nalakara/repo-health-audit.git
cd repo-health-audit
```

Gemini CLI and Antigravity:

```bash
mkdir -p ~/.gemini/config/skills/repo-health-audit
cp SKILL.md ~/.gemini/config/skills/repo-health-audit/
cp -r scripts references ~/.gemini/config/skills/repo-health-audit/
```

Codex:

```bash
mkdir -p ~/.codex/skills/repo-health-audit
cp SKILL.md ~/.codex/skills/repo-health-audit/
cp -r scripts references ~/.codex/skills/repo-health-audit/
```

DeepSeek Harness (dsh) and other `.agents` consumers:

```bash
mkdir -p ~/.agents/skills/repo-health-audit
cp SKILL.md ~/.agents/skills/repo-health-audit/
cp -r scripts references ~/.agents/skills/repo-health-audit/
```

Claude Code:

```bash
mkdir -p ~/.claude/skills/repo-health-audit
cp SKILL.md ~/.claude/skills/repo-health-audit/
cp -r scripts references ~/.claude/skills/repo-health-audit/
```

Muse:

```bash
mkdir -p ~/workspace/custom-skills/repo-health-audit
cp claude/SKILL.md claude/skill.yaml ~/workspace/custom-skills/repo-health-audit/
cp -r scripts references ~/workspace/custom-skills/repo-health-audit/
```

ChatGPT has no terminal route: paste `chatgpt/INSTRUCTIONS.md` into a Custom GPT or Project and upload the two files from `references/` as knowledge.

## Use

Ask your agent to audit a repository, by local path or GitHub URL:

> Audit this repo: https://github.com/you/your-repo

The scanner needs Python 3.11 or newer and git, and nothing else. Then take the fix list from the top, land each fix as its own small commit, and audit again. Watching one repo climb from the 30s past 70, one verified fix at a time, is the whole game.

## Calibration note

The weights and bands are an independent calibration fitted to the two reference reports (scores 39.6 and 33). Expect a ballpark match with any external scorer, not an exact one. The trend of a repository's score over repeated runs is the signal that matters. This skill is a self-evaluation mirror, not a licensing valuation and not a promise that any buyer will pay for your code.

## Privacy note

If a third-party scoring service asks for a GitHub token, use a fine-grained token scoped to selected repositories only, with the shortest expiry offered, and delete the token right after scoring. Never grant all-repositories access for a score.

## Start now

Pick the repo you are least proud of. That is the one this skill was built for. Audit it, fix the top item, audit it again. If the score helped you see your own code the way a buyer would, a star helps the next developer find it.
