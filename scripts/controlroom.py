#!/usr/bin/env python3
"""Controlroom reference installer: install, update, uninstall, validate, parity, package."""
import argparse, hashlib, json, re, shutil, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHILOSOPHIES = ["engineering", "work", "personal", "writing", "research"]
# Rule files of other tools: pre-existing content is moved under "## Project", never lost.
RULE_FILES = ["AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md"]
PROJECT_RE = re.compile(r"^## Project[ \t]*$", re.M)


def manifest(root=ROOT):
    lines = (root / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    version = lines[0].removeprefix("# version").strip() if lines and lines[0].startswith("# version") else "2.0.0"
    return version, [l.strip() for l in lines if l.strip() and not l.startswith("#")]


VERSION, MANIFEST = manifest()


def above_project(text):
    m = PROJECT_RE.search(text)
    return text[:m.start()] if m else text


def project_section(text):
    m = PROJECT_RE.search(text)
    return text[m.start():] if m else None


def sha(path):
    # AGENTS.md: hash only the text above "## Project", because Setup fills that section.
    data = path.read_bytes()
    if path.name == "AGENTS.md":
        data = above_project(data.decode("utf-8")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_config(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    unknown = sorted(set(data.get("philosophies", [])) - set(PHILOSOPHIES))
    if unknown: raise SystemExit(f"Unknown philosophies: {', '.join(unknown)}")
    if data.get("language") != "en": raise SystemExit("Controlroom currently requires language=en")
    return data


def choose():
    print("Controlroom must ask before installing anything.")
    print("Which Controlroom philosophies should this repository follow?")
    print("Repo-Starter and Controlroom Core are always included.")
    print("0) Core only\nA) All philosophies")
    for i, name in enumerate(PHILOSOPHIES, 1): print(f"{i}) {name.title()}")
    raw = input("Choose All, Core only, or comma-separated numbers: ").strip().lower()
    if raw in ("a", "all"): chosen = PHILOSOPHIES[:]; profile = "all"
    elif raw in ("0", "core"): chosen = []; profile = "core-only"
    elif not raw: raise SystemExit("No selection made. Nothing was installed.")
    else:
        try: chosen = [PHILOSOPHIES[int(x.strip()) - 1] for x in raw.split(",")]
        except (ValueError, IndexError): raise SystemExit("Invalid selection")
        chosen = list(dict.fromkeys(chosen)); profile = "custom"
    return {"schema_version": 1, "profile": profile, "philosophies": chosen, "language": "en",
            "workflow": {"development_branch": "dev", "release_branch": "main", "require_independent_review": True}}


def generate_agents(config, project=None):
    parts = [(ROOT / "templates/AGENTS.header.md").read_text(encoding="utf-8"),
             "# Mandatory Repo-Starter base philosophy",
             (ROOT / "philosophies/repo-starter/instructions.md").read_text(encoding="utf-8"),
             "# Mandatory core"]
    parts += [p.read_text(encoding="utf-8") for p in sorted((ROOT / "core").glob("[0-9]*.md"))]
    parts.append((ROOT / "templates/AGENTS.workflow.md").read_text(encoding="utf-8"))
    if config["philosophies"]:
        parts.append("# Selected philosophies")
        parts += [(ROOT / f"philosophies/{n}/instructions.md").read_text(encoding="utf-8") for n in config["philosophies"]]
    body = "\n\n".join(x.strip() for x in parts) + "\n\n"
    return body + (project if project else (ROOT / "templates/PROJECT.md").read_text(encoding="utf-8"))


def read_lock(target):
    """Return (files, legacy). Reads .controlroom.lock (JSON) or repo-starter's plain-text lock."""
    lp = target / ".controlroom.lock"
    if lp.exists(): return json.loads(lp.read_text(encoding="utf-8")).get("files", {}), False
    lp = target / ".repo-starter.lock"
    if not lp.exists(): return {}, False
    files = {}
    for line in lp.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if not parts or parts[0] == "version": continue
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[1]):
            raise SystemExit(f"Legacy .repo-starter.lock line not understood: {line!r}. Stop and inspect it manually.")
        files[parts[0]] = parts[1]
    return files, True


def install(target, config):
    target = Path(target).resolve(); target.mkdir(parents=True, exist_ok=True)
    old, legacy = read_lock(target)
    agents = target / "AGENTS.md"
    project = project_section(agents.read_text(encoding="utf-8")) if agents.exists() else None
    # Pre-existing rule files Controlroom does not own: quote them under "## Project" before overwriting.
    moved = []
    for rel in RULE_FILES:
        dst = target / rel
        if not dst.exists() or rel in old: continue
        text = above_project(dst.read_text(encoding="utf-8")) if rel == "AGENTS.md" else dst.read_text(encoding="utf-8")
        if rel != "AGENTS.md" and text == (ROOT / rel).read_text(encoding="utf-8"): continue
        if text.strip(): moved.append(f"\n### Previous rules from `{rel}` (moved at install, review and trim)\n\n" + "\n".join("> " + l for l in text.strip().splitlines()) + "\n")
    if moved:
        project = (project or (ROOT / "templates/PROJECT.md").read_text(encoding="utf-8")).rstrip("\n") + "\n" + "".join(moved)
    installed, conflicts = [], []
    for rel in MANIFEST:
        dst = target / rel
        locked_changed = dst.exists() and rel in old and sha(dst) != old[rel]
        unowned = dst.exists() and rel not in old and rel not in RULE_FILES
        if locked_changed or unowned:
            conflicts.append(rel); continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel == "AGENTS.md": dst.write_text(generate_agents(config, project), encoding="utf-8")
        else: shutil.copy2(ROOT / rel, dst)
        installed.append(rel)
    cr = target / ".controlroom"; cr.mkdir(exist_ok=True)
    (cr / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8"); installed.append(".controlroom/config.json")
    for folder in ("core", "philosophies"):
        for src in (ROOT / folder).rglob("*.md"):
            if folder == "philosophies" and src.parent.name != "repo-starter" and src.parent.name not in config["philosophies"]: continue
            rel = Path(".controlroom") / src.relative_to(ROOT); dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst); installed.append(rel.as_posix())
    for d in ("changes", "status"): (target / d).mkdir(exist_ok=True)
    installed = sorted(set(installed))
    lock = {"schema_version": 1, "product": "Controlroom", "version": VERSION, "config": config,
            "files": {p: sha(target / p) for p in installed}}
    (target / ".controlroom.lock").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    if legacy: (target / ".repo-starter.lock").rename(target / ".repo-starter.lock.migrated")
    print(f"Controlroom {VERSION}: installed {len(installed)} files. Philosophies: {', '.join(config['philosophies']) or 'core only'}")
    if legacy: print("Migrated from repo-starter: .repo-starter.lock renamed to .repo-starter.lock.migrated")
    if moved: print("Moved pre-existing rules under '## Project' in AGENTS.md; quote them in the pull request.")
    if conflicts: print("Preserved local files requiring manual review:\n- " + "\n- ".join(conflicts))
    return conflicts


def uninstall(target, assume_yes=False):
    target = Path(target).resolve(); lp = target / ".controlroom.lock"
    if not lp.exists(): raise SystemExit("No .controlroom.lock found. Refusing to guess what Controlroom owns.")
    files = json.loads(lp.read_text(encoding="utf-8")).get("files", {}); kept, removed = [], []
    for rel, expected in files.items():
        p = target / rel
        if not p.exists(): continue
        if sha(p) != expected: kept.append(rel); continue
        if rel == "AGENTS.md" and not assume_yes and input("AGENTS.md holds the Project section. Delete it? [y/N] ").strip().lower() != "y":
            kept.append(rel); continue
        p.unlink(); removed.append(rel)
    folders = []
    for rel in sorted(removed, key=lambda r: -r.count("/")):
        d = (target / rel).parent
        while d != target and d.exists() and not any(d.iterdir()):
            d.rmdir(); folders.append(str(d.relative_to(target))); d = d.parent
    lp.unlink()
    print(f"Removed {len(removed)} unchanged files. Kept {len(kept)} files. Removed {len(folders)} empty folders.")
    if kept: print("Kept (changed or declined):\n- " + "\n- ".join(kept))


def validate(target):
    target = Path(target); errors = []
    for f in ["AGENTS.md", "CLAUDE.md", "BUILD.md", "STATUS.md", "VERSIONS.md"]:
        if not (target / f).is_file(): errors.append(f"Missing {f}")
    lp = target / ".controlroom.lock"
    if lp.exists():
        try:
            for rel, h in json.loads(lp.read_text(encoding="utf-8")).get("files", {}).items():
                p = target / rel
                if not p.exists(): errors.append(f"Locked file missing: {rel}")
                elif sha(p) != h: errors.append(f"Locked file changed: {rel}")
        except Exception as e: errors.append(f"Invalid lock: {e}")
    if errors: print("Validation failed:\n- " + "\n- ".join(errors)); return 1
    print("Validation passed."); return 0


def sections(text):
    """Map '## N. Title' headings to their bodies."""
    out = {}
    for m in re.finditer(r"^(## \d+\..*?)$(.*?)(?=^## |\Z)", text, re.M | re.S): out[m.group(1)] = m.group(2).strip()
    return out


def parity(rs):
    """Gate for the repo-starter -> Controlroom transfer. rs = path to a repo-starter checkout."""
    rs = Path(rs).resolve(); errors = []
    _, rs_files = manifest(rs)
    for rel in rs_files:
        if rel not in MANIFEST: errors.append(f"repo-starter file not in Controlroom MANIFEST: {rel}")
        elif rel.startswith((".claude/", ".github/workflows/")) and (ROOT / rel).read_bytes() != (rs / rel).read_bytes():
            if rel != ".github/workflows/labels.yml" or (ROOT / rel).read_text().splitlines()[1:] != (rs / rel).read_text().splitlines()[1:]:
                errors.append(f"Differs from repo-starter: {rel}")
    base = sections((ROOT / "philosophies/repo-starter/instructions.md").read_text(encoding="utf-8"))
    for head, body in sections((rs / "AGENTS.md").read_text(encoding="utf-8")).items():
        if base.get(head) != body: errors.append(f"AGENTS.md section missing or changed in base philosophy: {head}")
    # Simulate a repo-starter install with a filled Project section, then migrate it.
    with tempfile.TemporaryDirectory() as d:
        t = Path(d)
        for rel in rs_files:
            (t / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(rs / rel, t / rel)
        agents = (t / "AGENTS.md").read_text(encoding="utf-8")
        project = project_section(agents).replace("- Stack: Markdown.", "- Stack: Parity test stack.")
        (t / "AGENTS.md").write_text(above_project(agents) + project, encoding="utf-8")
        version = (rs / "MANIFEST.txt").read_text().splitlines()[0].removeprefix("# version").strip()
        (t / ".repo-starter.lock").write_text(f"version {version}\n" + "".join(f"{r} {sha(t / r)}\n" for r in rs_files), encoding="utf-8")
        (t / ".claude/skills/tdd/SKILL.md").write_text("owner edit\n", encoding="utf-8")
        conflicts = install(t, {"schema_version": 1, "profile": "parity", "philosophies": ["engineering"], "language": "en"})
        if project_section((t / "AGENTS.md").read_text(encoding="utf-8")) != project: errors.append("Migration did not keep '## Project' byte for byte")
        if conflicts != [".claude/skills/tdd/SKILL.md"]: errors.append(f"Migration conflicts wrong: {conflicts}")
        if (t / ".claude/skills/tdd/SKILL.md").read_text() != "owner edit\n": errors.append("Migration overwrote an owner-edited file")
        if (t / ".repo-starter.lock").exists(): errors.append("Legacy lock was not retired")
        for rel in rs_files:
            if not (t / rel).exists(): errors.append(f"File lost in migration: {rel}")
    if errors: print("Parity failed:\n- " + "\n- ".join(errors)); return 1
    print(f"Parity passed: Controlroom {VERSION} covers repo-starter {version}."); return 0


def package(output):
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in ROOT.rglob("*"):
            if p.is_file() and ".git" not in p.parts and p.resolve() != out.resolve(): z.write(p, p.relative_to(ROOT.parent))
    print(out)


def self_test():
    missing = [rel for rel in MANIFEST if not (ROOT / rel).is_file()]
    assert not missing, f"MANIFEST paths missing from Controlroom: {missing}"
    cfg = {"schema_version": 1, "profile": "test", "philosophies": ["engineering", "work"], "language": "en"}
    with tempfile.TemporaryDirectory() as d:
        t = Path(d)
        (t / "CLAUDE.md").write_text("Use tabs.\n", encoding="utf-8")
        install(t, cfg)
        agents = (t / "AGENTS.md").read_text(encoding="utf-8")
        assert "> Use tabs." in project_section(agents), "pre-existing CLAUDE.md rules were not moved under Project"
        assert validate(t) == 0
        (t / "AGENTS.md").write_text(above_project(agents) + "## Project\n\n- Goal: kept\n", encoding="utf-8")
        assert validate(t) == 0, "filling Project must not count as a change"
        install(t, cfg)
        assert project_section((t / "AGENTS.md").read_text(encoding="utf-8")) == "## Project\n\n- Goal: kept\n"
        uninstall(t, assume_yes=True)
        assert not (t / "AGENTS.md").exists() and not (t / ".claude").exists() and not (t / ".controlroom.lock").exists()
    print("Self-test passed.")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("configure")
    for name in ("install", "update"):
        p = sub.add_parser(name); p.add_argument("target"); p.add_argument("--config"); p.add_argument("--non-interactive", action="store_true")
    p = sub.add_parser("uninstall"); p.add_argument("target"); p.add_argument("--yes", action="store_true", help="delete AGENTS.md without asking")
    p = sub.add_parser("validate"); p.add_argument("target")
    p = sub.add_parser("parity", help="check Controlroom covers a repo-starter checkout"); p.add_argument("repo_starter")
    p = sub.add_parser("package"); p.add_argument("--output", required=True)
    sub.add_parser("self-test")
    sub.add_parser("version")
    a = ap.parse_args()
    if a.cmd == "configure":
        out = Path("controlroom.config.json"); out.write_text(json.dumps(choose(), indent=2) + "\n"); print(f"Wrote {out}. Review it before installation.")
    elif a.cmd in ("install", "update"):
        if a.config and not a.non_interactive: raise SystemExit("To bypass the question, --config must be combined with --non-interactive")
        if a.non_interactive:
            if not a.config: raise SystemExit("--non-interactive requires --config")
            cfg = load_config(a.config)
        elif a.cmd == "update" and (Path(a.target) / ".controlroom/config.json").exists():
            cfg = load_config(Path(a.target) / ".controlroom/config.json"); print("Keeping the existing Controlroom philosophy selection.")
        else: cfg = choose()
        install(a.target, cfg)
    elif a.cmd == "uninstall": uninstall(a.target, a.yes)
    elif a.cmd == "validate": raise SystemExit(validate(a.target))
    elif a.cmd == "parity": raise SystemExit(parity(a.repo_starter))
    elif a.cmd == "package": package(a.output)
    elif a.cmd == "self-test": self_test()
    elif a.cmd == "version": print(VERSION)


if __name__ == "__main__": main()
