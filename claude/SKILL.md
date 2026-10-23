# Repo Health Audit

## When to use this skill

- Audit a code repository the user owns or is evaluating and report an objective health score across eight dimensions, with the gaps ranked by impact.

- Run it on a local repository path, or clone the repository first when the user gives a GitHub URL or repo name.

- Re-run it on the same repository after fixes land, and compare against the previous report to show the delta.

## Run the mechanical scan

- Run `python3 ~/workspace/custom-skills/repo-health-audit/scripts/audit_repo.py <repo-path> --out <workdir>/metrics.json` with `muse.exec` and read the JSON it writes.

- Add the `--history-secrets` flag only when the user asks for a history deep scan, because it walks the full git log and can take minutes on a large repository.

- Treat the scanner output as evidence, not as the verdict. It counts and detects, and it never prints secret values, only file paths and hit counts.

- Fall back to reading the repository by hand when the scanner fails on an unusual layout, and say which metrics are hand-collected in the report.

## Score with the rubric

- Read [the scoring rubric](references/rubric.md) and apply its bands exactly as written, dimension by dimension, from the scanner metrics.

- Keep the calibration stable across runs. A score that moves because the rubric moved teaches the user nothing.

- Read [the extracted DataFactor variables](references/datafactor-variables.md) when a dimension needs interpretation help or the user asks how an outside buyer would see the repository.

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

- Present the score as our own calibration that mirrors published buyer criteria, never as a DataFactor score and never as a promise of licensing value.

- Skip the urgency framing that sourcing funnels use. The point of the audit is the fix list and the trend over time, not a deadline.

## Available connectors

- [GitHub](/opt/hatch/connectors/github/CONNECTOR.md) for locating the user's repositories and reading their metadata before a clone.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Websites

- [DataFactor score page](https://datafactor.com/score) for the buyer criteria this rubric mirrors. Submit a repository there only with the user's explicit approval, a token scoped to selected repositories only, and token deletion right after scoring.
