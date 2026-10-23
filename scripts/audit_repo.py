#!/usr/bin/env python3
"""Repo health audit scanner.

Collects the mechanical metrics behind the repo-health-audit rubric
(8 dimensions, mirroring the variable set DataFactor publishes in its
score reports) and prints them as JSON. It never prints secret values:
secret findings are reported as counts and file paths only.

Usage:
    python3 audit_repo.py /path/to/repo
    python3 audit_repo.py /path/to/repo --out metrics.json
    python3 audit_repo.py /path/to/repo --history-secrets   (slow, optional)

Stdlib only. Works on any local git repository (falls back to a plain
directory walk when the folder is not a git repo).
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone

SOURCE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".vue", ".svelte",
    ".go", ".rs", ".java", ".kt", ".kts", ".swift", ".rb", ".php",
    ".c", ".h", ".cpp", ".hpp", ".cc", ".cs", ".sh", ".bash", ".sql",
    ".scala", ".pl", ".lua", ".r", ".ex", ".exs", ".clj", ".hs", ".ml",
    ".dart", ".m", ".mm",
}

EXCLUDE_DIRS = {
    ".git", "node_modules", ".next", "dist", "build", "out", "target",
    ".venv", "venv", "__pycache__", ".tox", ".mypy_cache", ".pytest_cache",
    "coverage", ".nyc_output", "Pods", ".dart_tool", ".gradle",
}

TEST_DIR_NAMES = {"test", "tests", "__tests__", "spec", "specs", "testing"}

LOCKFILES = [
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb",
    "poetry.lock", "uv.lock", "Pipfile.lock", "pdm.lock",
    "Cargo.lock", "go.sum", "Gemfile.lock", "composer.lock",
]

ENV_EXAMPLE_NAMES = {".env.example", ".env.sample", ".env.template",
                     "example.env", ".env.dist", ".env.example.txt"}

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|api[_-]?secret|client[_-]?secret|access[_-]?token|auth[_-]?token|private[_-]?key|secret[_-]?key|password|passwd)\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']"),
    re.compile(r"\b(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|gho_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_\-]{30,})\b"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
]

ENV_REF_PATTERNS = [
    re.compile(r"os\.environ\[['\"]([A-Z][A-Z0-9_]*)['\"]\]"),
    re.compile(r"os\.environ\.get\(['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"os\.getenv\(['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]*)"),
    re.compile(r"process\.env\[['\"]([A-Z][A-Z0-9_]*)['\"]\]"),
    re.compile(r"import\.meta\.env\.([A-Z][A-Z0-9_]*)"),
    re.compile(r"env\(['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"getenv\(['\"]([A-Z][A-Z0-9_]*)['\"]"),
    re.compile(r"System\.getenv\(['\"]([A-Z][A-Z0-9_]*)['\"]"),
]

CONVENTIONAL_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]*\))?(!)?:"
)

BOT_HINTS = ("[bot]", "dependabot", "renovate", "github-actions", "codecov")

# Runtime-provided variables that are never project configuration.
IGNORE_ENV_VARS = {"NODE_ENV", "CI", "PATH", "HOME", "PWD", "SHELL",
                   "USER", "LANG", "TERM", "HOSTNAME", "OLDPWD", "SHLVL"}


def run_git(repo, args):
    try:
        out = subprocess.run(
            ["git", "-C", repo] + args,
            capture_output=True, text=True, timeout=120,
        )
        if out.returncode != 0:
            return None
        return out.stdout
    except Exception:
        return None


def is_test_file(relpath):
    parts = relpath.replace("\\", "/").split("/")
    name = parts[-1]
    dirs = {p.lower() for p in parts[:-1]}
    if dirs & TEST_DIR_NAMES:
        return True
    if re.match(r"test_.*\.py$", name) or re.match(r".*_test\.py$", name):
        return True
    if re.match(r".*_test\.go$", name):
        return True
    if re.search(r"\.(test|spec)\.[tj]sx?$", name):
        return True
    if re.match(r".*Test\.java$", name) or re.match(r".*Tests\.cs$", name):
        return True
    if re.search(r"_spec\.rb$", name) or re.search(r"_test\.rb$", name):
        return True
    if re.search(r"\.test\.php$", name) or re.search(r"Test\.php$", name):
        return True
    return False


def list_files(repo, is_git):
    """Return list of repo-relative file paths (tracked files if git)."""
    if is_git:
        out = run_git(repo, ["ls-files"])
        if out is not None:
            return [ln for ln in out.splitlines() if ln.strip()]
    rels = []
    for root, dirs, names in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for n in names:
            rels.append(os.path.relpath(os.path.join(root, n), repo))
    return rels


def read_text(repo, rel, max_bytes=2_000_000):
    path = os.path.join(repo, rel)
    try:
        if os.path.getsize(path) > max_bytes:
            return None
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception:
        return None


def count_loc(text):
    return sum(1 for ln in text.splitlines() if ln.strip())


def has_any(files_set, names):
    return [n for n in names if n in files_set]


def collect_code_stats(repo, files):
    stats = {
        "source_files": 0, "source_loc": 0, "test_files": 0, "test_loc": 0,
        "languages": {}, "file_loc": [],
    }
    lang_loc = Counter()
    for rel in files:
        ext = os.path.splitext(rel)[1].lower()
        if ext not in SOURCE_EXTS:
            continue
        if rel.endswith((".min.js", ".min.css")) or rel.endswith(".map"):
            continue
        parts = set(rel.replace("\\", "/").split("/"))
        if parts & EXCLUDE_DIRS:
            continue
        text = read_text(repo, rel)
        if text is None:
            continue
        loc = count_loc(text)
        stats["file_loc"].append((rel, loc))
        lang_loc[ext] += loc
        if is_test_file(rel):
            stats["test_files"] += 1
            stats["test_loc"] += loc
        else:
            stats["source_files"] += 1
            stats["source_loc"] += loc
    stats["languages"] = dict(lang_loc.most_common())
    locs = sorted(loc for _, loc in stats["file_loc"])
    stats["median_file_loc"] = locs[len(locs) // 2] if locs else 0
    stats["top_largest_files"] = [
        {"file": f, "loc": n}
        for f, n in sorted(stats["file_loc"], key=lambda x: -x[1])[:5]
    ]
    stats["god_files_over_500_loc"] = sum(1 for _, n in stats["file_loc"] if n > 500)
    del stats["file_loc"]
    if stats["test_files"] and stats["source_files"]:
        stats["test_source_ratio"] = round(
            stats["source_files"] / stats["test_files"], 1)
    else:
        stats["test_source_ratio"] = None
    stats["volume_estimate"] = round(stats["source_loc"] / 280, 1)
    return stats


def detect_frameworks(repo, files_set, files):
    fw = set()
    blob = ""
    pkg = read_text(repo, "package.json") if "package.json" in files_set else None
    pkg_data = {}
    if pkg:
        try:
            pkg_data = json.loads(pkg)
        except Exception:
            pkg_data = {}
        blob = pkg
    pyproj = read_text(repo, "pyproject.toml") if "pyproject.toml" in files_set else ""
    reqtxt = ""
    for rel in files:
        if os.path.basename(rel).startswith("requirements"):
            reqtxt += (read_text(repo, rel) or "")
    haystack = (blob + "\n" + (pyproj or "") + "\n" + reqtxt).lower()
    for name in ("pytest", "unittest", "jest", "vitest", "mocha", "cypress",
                 "playwright", "ava", "tap", "rspec", "phpunit", "junit"):
        if name in haystack:
            fw.add(name)
    for rel in files:
        base = os.path.basename(rel).lower()
        if base.startswith(("jest.config", "vitest.config", "cypress.config",
                            "playwright.config", "pytest.ini", ".coveragerc")):
            fw.add(base.split(".")[0])
    if any(rel.endswith(".go") for rel in files):
        fw.add("go test (builtin)")
    if "Cargo.toml" in files_set:
        fw.add("cargo test (builtin)")
    return sorted(fw), pkg_data


def detect_coverage(repo, files_set, files, pkg_data, ci_texts):
    tooling = []
    haystack = ""
    for rel in ("pyproject.toml", "setup.cfg", "tox.ini", ".coveragerc",
                "codecov.yml", ".codecov.yml", "package.json"):
        if rel in files_set:
            haystack += (read_text(repo, rel) or "") + "\n"
    low = haystack.lower()
    for name in ("pytest-cov", "coverage", "nyc", "c8", "@vitest/coverage-v8",
                 "codecov", "coveralls", "jacoco"):
        if name in low:
            tooling.append(name)
    for rel in files:
        if os.path.basename(rel) in ("codecov.yml", ".codecov.yml"):
            tooling.append("codecov")
    gate = bool(re.search(r"cov-fail-under|fail_under|--fail-under", 
                          haystack + "\n".join(ci_texts)))
    return sorted(set(tooling)), gate


def collect_ci(repo, files_set, files):
    ci_files = []
    for rel in files:
        low = rel.lower()
        if low.startswith(".github/workflows/") and low.endswith((".yml", ".yaml")):
            ci_files.append(rel)
        elif low in (".gitlab-ci.yml", ".circleci/config.yml", "jenkinsfile",
                     "azure-pipelines.yml", ".travis.yml"):
            ci_files.append(rel)
        elif low.startswith(".buildkite/"):
            ci_files.append(rel)
    texts = []
    for rel in ci_files:
        texts.append(read_text(repo, rel) or "")
    joined = "\n".join(texts).lower()
    runs = {
        "tests": bool(re.search(r"pytest|jest|vitest|npm (run )?test|go test|cargo test|mvn test|phpunit|rspec", joined)),
        "lint": bool(re.search(r"ruff|flake8|eslint|pylint|golangci|clippy", joined)),
        "typecheck": bool(re.search(r"tsc|mypy|pyright", joined)),
        "security_audit": bool(re.search(r"pip-audit|npm audit|safety|trivy|codeql|snyk", joined)),
        "coverage": bool(re.search(r"cov|coverage|codecov", joined)),
    }
    return {
        "ci_present": bool(ci_files),
        "ci_config_files": ci_files,
        "ci_runs": runs,
    }, texts


def spec_style(spec):
    s = str(spec).strip()
    if s in ("*", "latest", "x", "") or s.startswith((">", "<", "http", "git", "file:")):
        return "loose"
    if s.startswith("^"):
        return "caret"
    if s.startswith("~"):
        return "tilde"
    if s.startswith("=") or re.match(r"^\d", s):
        return "pinned"
    return "other"


def collect_dependencies(repo, files_set, files, pkg_data):
    dep = {
        "package_managers": [], "lockfiles_found": [],
        "runtime_deps": 0, "dev_deps": 0, "version_spec_styles": {},
        "dep_update_tooling": "none", "manifests": [],
    }
    dep["lockfiles_found"] = [f for f in files if os.path.basename(f) in LOCKFILES]
    styles = Counter()

    if pkg_data:
        dep["package_managers"].append("npm/yarn/pnpm")
        dep["manifests"].append("package.json")
        deps = pkg_data.get("dependencies", {}) or {}
        dev = pkg_data.get("devDependencies", {}) or {}
        dep["runtime_deps"] += len(deps)
        dep["dev_deps"] += len(dev)
        for s in list(deps.values()) + list(dev.values()):
            styles[spec_style(s)] += 1

    try:
        import tomllib
    except ImportError:
        tomllib = None
    if "pyproject.toml" in files_set and tomllib is not None:
        dep["package_managers"].append("pip/poetry/uv")
        dep["manifests"].append("pyproject.toml")
        try:
            data = tomllib.loads(read_text(repo, "pyproject.toml") or "")
            proj = data.get("project", {})
            deps = proj.get("dependencies", []) or []
            opt = proj.get("optional-dependencies", {}) or {}
            dep["runtime_deps"] += len(deps)
            for group in opt.values():
                dep["dev_deps"] += len(group)
            for d in deps:
                styles["pinned" if "==" in d or "~=" in d else "loose"] += 1
            poetry = data.get("tool", {}).get("poetry", {})
            if poetry:
                dep["runtime_deps"] += len(poetry.get("dependencies", {}))
        except Exception:
            pass
    for rel in files:
        base = os.path.basename(rel)
        if base.startswith("requirements") and base.endswith(".txt"):
            dep["manifests"].append(rel)
            if "pip/poetry/uv" not in dep["package_managers"]:
                dep["package_managers"].append("pip")
            for line in (read_text(repo, rel) or "").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    dep["runtime_deps"] += 1
                    styles["pinned" if "==" in line else "loose"] += 1
    if "go.mod" in files_set:
        dep["package_managers"].append("go modules")
        dep["manifests"].append("go.mod")
    if "Cargo.toml" in files_set:
        dep["package_managers"].append("cargo")
        dep["manifests"].append("Cargo.toml")
    if "Gemfile" in files_set:
        dep["package_managers"].append("bundler")
        dep["manifests"].append("Gemfile")
    if "composer.json" in files_set:
        dep["package_managers"].append("composer")
        dep["manifests"].append("composer.json")

    if ".github/dependabot.yml" in files_set or ".github/dependabot.yaml" in files_set:
        dep["dep_update_tooling"] = "dependabot"
    for cand in ("renovate.json", ".renovaterc", ".renovaterc.json", ".github/renovate.json"):
        if cand in files_set:
            dep["dep_update_tooling"] = "renovate"
    dep["version_spec_styles"] = dict(styles)
    return dep


def collect_docs_env_lint(repo, files_set, files):
    docs = {"readme_file": None, "readme_lines": 0, "readme_sections": [],
            "contributing": False, "changelog": False, "dockerfile": False,
            "devcontainer": False, "docker_compose": False}
    for rel in files:
        base = os.path.basename(rel)
        low = base.lower()
        if "/" not in rel and low.startswith("readme"):
            docs["readme_file"] = rel
        if "/" not in rel and low.startswith("contributing"):
            docs["contributing"] = True
        if "/" not in rel and low.startswith("changelog"):
            docs["changelog"] = True
        if base == "Dockerfile" or low.startswith("dockerfile."):
            docs["dockerfile"] = True
        if base in ("docker-compose.yml", "docker-compose.yaml", "compose.yml"):
            docs["docker_compose"] = True
        if rel.replace("\\", "/").endswith(".devcontainer/devcontainer.json"):
            docs["devcontainer"] = True
    readme_text = ""
    if docs["readme_file"]:
        readme_text = read_text(repo, docs["readme_file"]) or ""
        docs["readme_lines"] = len(readme_text.splitlines())
        low = readme_text.lower()
        section_hints = {
            "install": ("install", "instalasi", "setup", "getting started", "prasyarat", "prerequisites"),
            "run": ("run", "menjalankan", "usage", "penggunaan", "start", "quick start"),
            "env": ("environment", "env var", ".env", "configuration", "konfigurasi"),
            "features": ("feature", "fitur"),
            "architecture": ("architecture", "arsitektur", "structure", "struktur"),
            "test": ("test", "testing", "pengujian"),
        }
        for sec, hints in section_hints.items():
            if any(h in low for h in hints):
                docs["readme_sections"].append(sec)

    env = {"env_example_file": None, "env_vars_in_example": [],
           "env_vars_referenced_in_source": [], "env_vars_missing_from_example": []}
    for rel in files:
        if os.path.basename(rel) in ENV_EXAMPLE_NAMES:
            env["env_example_file"] = rel
            text = read_text(repo, rel) or ""
            env["env_vars_in_example"] = sorted(set(re.findall(
                r"^([A-Z][A-Z0-9_]*)\s*=", text, flags=re.M)))
    referenced = set()
    for rel in files:
        if os.path.splitext(rel)[1].lower() not in SOURCE_EXTS:
            continue
        if is_test_file(rel):
            continue
        text = read_text(repo, rel)
        if not text:
            continue
        for pat in ENV_REF_PATTERNS:
            referenced.update(pat.findall(text))
    referenced -= IGNORE_ENV_VARS
    env["env_vars_referenced_in_source"] = sorted(referenced)
    if env["env_example_file"]:
        env["env_vars_missing_from_example"] = sorted(
            referenced - set(env["env_vars_in_example"]))
    else:
        env["env_vars_missing_from_example"] = sorted(referenced)

    lint = {"has_lint_config": False, "linters_and_formatters": [],
            "package_lint_script": None}
    lint_config_files = {
        ".eslintrc": "eslint", ".eslintrc.js": "eslint", ".eslintrc.json": "eslint",
        ".eslintrc.yml": "eslint", "eslint.config.js": "eslint",
        "eslint.config.mjs": "eslint", "eslint.config.ts": "eslint",
        ".prettierrc": "prettier", ".prettierrc.json": "prettier",
        "prettier.config.js": "prettier", ".flake8": "flake8",
        "ruff.toml": "ruff", ".ruff.toml": "ruff", ".golangci.yml": "golangci-lint",
        ".rubocop.yml": "rubocop", "phpcs.xml": "phpcs", ".editorconfig": "editorconfig",
    }
    found = set()
    for rel in files:
        base = os.path.basename(rel)
        if base in lint_config_files:
            found.add(lint_config_files[base])
    pyproj = read_text(repo, "pyproject.toml") if "pyproject.toml" in files_set else ""
    for tool in ("ruff", "flake8", "black", "isort", "mypy"):
        if pyproj and re.search(rf"\[tool\.{tool}\]", pyproj):
            found.add(tool)
    setup_cfg = read_text(repo, "setup.cfg") if "setup.cfg" in files_set else ""
    if setup_cfg and "flake8" in setup_cfg:
        found.add("flake8")
    lint["linters_and_formatters"] = sorted(found)
    lint["has_lint_config"] = bool(found - {"editorconfig"}) or "editorconfig" in found and len(found) > 1
    return docs, env, lint


def collect_security(repo, files_set, files):
    sec = {"hardcoded_secret_hits": 0, "secret_hit_files": [],
           "env_files_committed": [], "private_key_files": []}
    for rel in files:
        base = os.path.basename(rel)
        if re.match(r"^\.env($|\.)", base) and base not in ENV_EXAMPLE_NAMES:
            sec["env_files_committed"].append(rel)
        if os.path.splitext(rel)[1].lower() not in SOURCE_EXTS | {".json", ".yml", ".yaml", ".toml", ".txt", ".md", ""}:
            continue
        if base in LOCKFILES:
            continue
        text = read_text(repo, rel)
        if not text:
            continue
        hit_lines = set()
        for lineno, line in enumerate(text.splitlines(), 1):
            for pat in SECRET_PATTERNS:
                if pat.search(line):
                    hit_lines.add(lineno)
                    if "PRIVATE KEY-----" in line:
                        sec["private_key_files"].append(rel)
                    break
        if hit_lines:
            sec["hardcoded_secret_hits"] += len(hit_lines)
            sec["secret_hit_files"].append(rel)
    sec["private_key_files"] = sorted(set(sec["private_key_files"]))
    return sec


def collect_history(repo, is_git):
    hist = {"is_git_repo": is_git, "total_commits": 0, "human_authors": 0,
            "authors": [], "span_days": 0, "active_days": 0,
            "first_commit": None, "last_commit": None, "tag_count": 0,
            "conventional_rate_last_200": None,
            "commits_sampled": 0, "commits_touching_tests_and_source": 0,
            "bulk_commits_over_15_files": 0}
    if not is_git:
        return hist
    log = run_git(repo, ["log", "--format=%H|%an|%ae|%ad|%s", "--date=short"])
    if not log:
        return hist
    lines = [ln for ln in log.splitlines() if ln.strip()]
    hist["total_commits"] = len(lines)
    authors = Counter()
    dates = []
    subjects = []
    for ln in lines:
        parts = ln.split("|")
        if len(parts) < 5:
            continue
        name, email = parts[1], parts[2]
        authors[f"{name} <{email}>"] += 1
        dates.append(parts[3])
        subjects.append(parts[4])
    humans = {a: n for a, n in authors.items()
              if not any(h in a.lower() for h in BOT_HINTS)}
    hist["authors"] = sorted(humans, key=lambda a: -humans[a])
    hist["human_authors"] = len(humans)
    if dates:
        hist["first_commit"] = min(dates)
        hist["last_commit"] = max(dates)
        try:
            d0 = datetime.strptime(min(dates), "%Y-%m-%d")
            d1 = datetime.strptime(max(dates), "%Y-%m-%d")
            hist["span_days"] = (d1 - d0).days
        except Exception:
            pass
        hist["active_days"] = len(set(dates))
    tags = run_git(repo, ["tag", "--list"])
    hist["tag_count"] = len([t for t in (tags or "").splitlines() if t.strip()])
    sample = subjects[:200]
    if sample:
        conv = sum(1 for s in sample if CONVENTIONAL_RE.match(s))
        hist["conventional_rate_last_200"] = round(conv / len(sample), 2)

    names_log = run_git(repo, ["log", "-200", "--name-only", "--format=COMMIT %H"])
    if names_log:
        sampled = 0
        mineable = 0
        bulk = 0
        blocks = names_log.split("COMMIT ")[1:]
        # The root commit is an initial drop, not an incremental task.
        # When the sample covers the whole history, drop it from the
        # mineable count (it stays in the sampled count).
        root_excluded = len(blocks) >= hist["total_commits"] and len(blocks) > 0
        for idx, block in enumerate(blocks):
            changed = [ln.strip() for ln in block.splitlines()[1:] if ln.strip()]
            if not changed:
                continue
            sampled += 1
            if root_excluded and idx == len(blocks) - 1:
                continue
            has_test = any(is_test_file(f) for f in changed)
            has_src = any(
                os.path.splitext(f)[1].lower() in SOURCE_EXTS and not is_test_file(f)
                for f in changed)
            if has_test and has_src:
                mineable += 1
            if len(changed) > 15:
                bulk += 1
        hist["commits_sampled"] = sampled
        hist["commits_touching_tests_and_source"] = mineable
        hist["bulk_commits_over_15_files"] = bulk
    return hist


def collect_architecture_hints(repo, files, pkg_data, deps_manifest_text):
    hints = {"logging_library_files": 0, "print_or_console_files": 0,
             "health_endpoint_files": [], "validation_libraries": [],
             "layer_dirs": []}
    logging_hints = ("import logging", "from logging", "loguru", "structlog",
                     "winston", "pino", "bunyan", "log4j", "slf4j", "zap.",
                     "logging.getLogger", "createLogger")
    validation_libs = {"pydantic", "zod", "joi", "yup", "ajv", "marshmallow",
                       "attrs", "valibot", "superstruct"}
    manifest_low = deps_manifest_text.lower()
    for lib in sorted(validation_libs):
        if lib in manifest_low:
            hints["validation_libraries"].append(lib)
    top_dirs = set()
    for rel in files:
        parts = rel.replace("\\", "/").split("/")
        if len(parts) > 1:
            top_dirs.add(parts[0])
            if parts[0] in ("src", "app", "lib") and len(parts) > 2:
                top_dirs.add(parts[1])
        if os.path.splitext(rel)[1].lower() not in SOURCE_EXTS or is_test_file(rel):
            continue
        text = read_text(repo, rel)
        if not text:
            continue
        if any(h in text for h in logging_hints):
            hints["logging_library_files"] += 1
        if re.search(r"(^|\s)(print\(|console\.log\()", text):
            hints["print_or_console_files"] += 1
        if re.search(r"[\"'/](api/)?health[\"'/]", text) or "/healthz" in text:
            hints["health_endpoint_files"].append(rel)
    layer_names = {"api", "service", "services", "repositories", "repository",
                   "models", "domain", "core", "cli", "web", "handlers",
                   "controllers", "routes", "storage", "db", "utils", "lib"}
    hints["layer_dirs"] = sorted(d for d in top_dirs if d.lower() in layer_names)
    hints["health_endpoint_files"] = hints["health_endpoint_files"][:5]
    return hints


def history_secret_commit_count(repo):
    out = run_git(repo, ["log", "-p", "--format=COMMIT %H", "-S", "PRIVATE KEY",
                         "--", "."])
    count = 0
    if out:
        count = out.count("PRIVATE KEY-----")
    grep = run_git(repo, ["log", "-p", "--format=COMMIT %H",
                          "-G", r"(ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,})"])
    hits = 0
    if grep:
        hits = len(re.findall(r"ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}", grep))
    return {"history_private_key_mentions": count,
            "history_token_pattern_hits": hits,
            "note": "counts only, values never printed"}


def main():
    ap = argparse.ArgumentParser(description="Collect repo health metrics as JSON.")
    ap.add_argument("repo", help="Path to the repository")
    ap.add_argument("--out", help="Write JSON to this file instead of stdout")
    ap.add_argument("--history-secrets", action="store_true",
                    help="Also scan git history for key and token patterns (slow)")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    if not os.path.isdir(repo):
        print(f"not a directory: {repo}", file=sys.stderr)
        return 1
    is_git = os.path.isdir(os.path.join(repo, ".git")) or \
        (run_git(repo, ["rev-parse", "--git-dir"]) is not None)

    files = list_files(repo, is_git)
    files_set = set(files)

    code = collect_code_stats(repo, files)
    frameworks, pkg_data = detect_frameworks(repo, files_set, files)
    ci, ci_texts = collect_ci(repo, files_set, files)
    coverage_tooling, coverage_gate = detect_coverage(
        repo, files_set, files, pkg_data, ci_texts)
    deps = collect_dependencies(repo, files_set, files, pkg_data)
    docs, env, lint = collect_docs_env_lint(repo, files_set, files)
    if pkg_data:
        scripts = pkg_data.get("scripts", {}) or {}
        if "lint" in scripts:
            lint["package_lint_script"] = scripts["lint"]
    sec = collect_security(repo, files_set, files)
    hist = collect_history(repo, is_git)
    manifest_text = ""
    for rel in ("package.json", "pyproject.toml", "go.mod", "Cargo.toml",
                "composer.json", "Gemfile"):
        if rel in files_set:
            manifest_text += (read_text(repo, rel) or "") + "\n"
    arch = collect_architecture_hints(repo, files, pkg_data, manifest_text)

    result = {
        "repo": {"path": repo, "name": os.path.basename(repo.rstrip("/")) or repo,
                 "is_git_repo": is_git,
                 "scanned_at": datetime.now(timezone.utc).isoformat()},
        "code": code,
        "tests": {
            "test_spec_files": code["test_files"],
            "test_loc": code["test_loc"],
            "test_frameworks": frameworks,
            "test_source_ratio": code["test_source_ratio"],
            "coverage_tooling": coverage_tooling,
            "coverage_gate": coverage_gate,
        },
        "ci": ci,
        "dependencies": deps,
        "docs": docs,
        "env": env,
        "lint": lint,
        "security": sec,
        "history": hist,
        "architecture_hints": arch,
        "buyer_fit_raw": {
            "builds_and_tests_at_head": bool(code["test_files"] and frameworks),
            "task_capacity_proxy_mineable_commits": hist["commits_touching_tests_and_source"],
            "genuine_history_multi_author": hist["human_authors"] >= 2,
            "self_contained_container": bool(docs["dockerfile"] or docs["devcontainer"]),
        },
    }
    if args.history_secrets and is_git:
        result["security"]["history_scan"] = history_secret_commit_count(repo)

    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload)
        print(f"wrote {args.out}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
