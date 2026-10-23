# Repo Health Audit

An agent skill that scores a code repository from 0 to 100 across eight
engineering health dimensions and returns an impact-ranked fix list.

It mirrors the criteria that AI-training data buyers publish in their
repository score reports (DataFactor's assessment is the reference model,
reverse-engineered from two real reports in October 2026). The point is
self-evaluation: a stable, objective mirror for a repository's hygiene,
not a licensing valuation.

Two layers, like the original:

1. A mechanical scanner (`scripts/audit_repo.py`, Python standard library
   only) that measures LOC, test ratios, CI presence, lockfiles, version
   pinning, env documentation gaps, god files, secret patterns, and git
   history shape, and emits JSON.
2. A judgment pass by the agent, which reads the rubric and the code to
   weigh layering, error handling, logging, and test quality, citing
   file-level evidence.

## The eight dimensions

- D Architecture and Robustness (weight 0.18)
- B Test Coverage (0.18)
- K History and Maintenance (0.14)
- F Docs and Onboarding (0.12)
- C Code Cleanliness (0.12)
- I Security Hygiene (0.10)
- E Dependency Health (0.08)
- H CI/CD Maturity (0.08)

Scoring bands live in `references/rubric.md`. The full variable inventory
extracted from the reference reports lives in
`references/datafactor-variables.md`.

## Layout

- `SKILL.md` at the root is the standard agent-skills format (YAML
  frontmatter), used by Gemini CLI and Antigravity, Codex, DeepSeek
  Harness (dsh), Claude Code, and other compatible agents.
- `scripts/` and `references/` are shared by every variant.
- `claude/` holds the Muse variant: a frontmatter-free `SKILL.md` plus
  the `skill.yaml` descriptor Muse uses.
- `chatgpt/` holds paste-ready instructions for a Custom GPT or a
  Project, with the rubric and variable files uploaded as knowledge.

## Install

Copy the root `SKILL.md` together with `scripts/` and `references/` into
the platform's skill folder:

- Gemini CLI and Antigravity: `~/.gemini/config/skills/repo-health-audit/`
- Codex: `~/.codex/skills/repo-health-audit/`
- DeepSeek Harness (dsh) and other `.agents` consumers: `~/.agents/skills/repo-health-audit/`
- Claude Code: `~/.claude/skills/repo-health-audit/`
- Muse: copy `claude/SKILL.md` and `claude/skill.yaml` plus `scripts/` and
  `references/` into `~/workspace/custom-skills/repo-health-audit/`
- ChatGPT: paste `chatgpt/INSTRUCTIONS.md` into a Custom GPT or Project
  and upload the two files from `references/` as knowledge

## Use

Ask the agent to audit a repository, by local path or GitHub URL. The
scanner needs Python 3.11 or newer and git, and nothing else. The audit is
read-only and never prints secret values, only file paths and hit counts.

## Calibration note

The weights and bands are an independent calibration fitted to the two
reference reports (scores 39.6 and 33). Expect a ballpark match with any
external scorer, not an exact one. The trend of a repository's score over
repeated runs is the signal that matters.

## Privacy note

If a third-party scoring service asks for a GitHub token, use a
fine-grained token scoped to selected repositories only, the shortest
expiry offered, and delete the token right after scoring. Never grant
all-repositories access for a score.
