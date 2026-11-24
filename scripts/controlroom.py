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
    raw = ask("Choose All, Core only, or comma-separated numbers: ").strip().lower()
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


def ask(prompt):
    """input() that treats a missing terminal (agents, CI) as an empty answer."""
    try: return input(prompt)
    except EOFError: return ""


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
        # Agents wrote either "<path> <sha256>" or sha256sum order "<sha256>  <path>".
        hashes = [x for x in parts if re.fullmatch(r"[0-9a-f]{64}", x)]
        if len(parts) != 2 or len(hashes) != 1:
            raise SystemExit(f"Legacy .repo-starter.lock line not understood: {line!r}. Stop and inspect it manually.")
        files[parts[0] if parts[1] == hashes[0] else parts[1]] = hashes[0]
    return files, True


def is_v1(target, old):
    """repo-starter v1: no lock, CLAUDE.md is a full copy of AGENTS.md."""
    a, c = target / "AGENTS.md", target / "CLAUDE.md"
    return not old and a.exists() and c.exists() and \
        above_project(c.read_text(encoding="utf-8")).strip() == above_project(a.read_text(encoding="utf-8")).strip()


def install(target, config):
    target = Path(target).resolve(); target.mkdir(parents=True, exist_ok=True)
    old, legacy = read_lock(target)
    v1 = is_v1(target, old)
    agents = target / "AGENTS.md"
    project = project_section(agents.read_text(encoding="utf-8")) if agents.exists() else None
    # Plan every write first (path -> bytes), so nothing is written when the migration must stop.
    plan = {rel: (ROOT / rel).read_bytes() for rel in MANIFEST if rel != "AGENTS.md"}
    plan[".controlroom/config.json"] = (json.dumps(config, indent=2) + "\n").encode("utf-8")
    for folder in ("core", "philosophies"):
        for src in (ROOT / folder).rglob("*.md"):
            if folder == "philosophies" and src.parent.name != "repo-starter" and src.parent.name not in config["philosophies"]: continue
            plan[(Path(".controlroom") / src.relative_to(ROOT)).as_posix()] = src.read_bytes()
    # Pre-existing rule files Controlroom does not own: quote them under "## Project" before overwriting.
    moved = []
    for rel in RULE_FILES:
        dst = target / rel
        if not dst.exists() or rel in old or (v1 and rel in ("AGENTS.md", "CLAUDE.md")): continue
        text = dst.read_text(encoding="utf-8")
        if rel == "AGENTS.md": text = above_project(text)
        elif text.encode("utf-8") == plan[rel]: continue
        if text.strip(): moved.append(f"\n### Previous rules from `{rel}` (moved at install, review and trim)\n\n" + "\n".join("> " + l for l in text.strip().splitlines()) + "\n")
    if moved:
        project = (project or (ROOT / "templates/PROJECT.md").read_text(encoding="utf-8")).rstrip("\n") + "\n" + "".join(moved)
    plan["AGENTS.md"] = generate_agents(config, project).encode("utf-8")
    conflicts = []
    for rel in sorted(plan):
        dst = target / rel
        if not dst.exists(): continue
        if rel in old:
            if sha(dst) != old[rel]: conflicts.append(rel)
        elif rel in RULE_FILES: continue
        elif rel.startswith(".controlroom/") and dst.read_bytes() == plan[rel]: continue
        else: conflicts.append(rel)
    if "AGENTS.md" in conflicts:
        raise SystemExit("AGENTS.md was edited above '## Project' since it was installed. Nothing was changed. "
                         "Move those edits under '## Project' (or restore the installed text), then run again.")
    for rel in conflicts: del plan[rel]
    for rel, data in plan.items():
        dst = target / rel; dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(data)
    # Files the old lock owned that are no longer installed (e.g. a deselected philosophy): delete if unchanged.
    stale = [rel for rel, h in old.items() if rel not in plan and rel not in conflicts and (target / rel).exists() and sha(target / rel) == h]
    for rel in stale: (target / rel).unlink()
    prune(target, stale)
    for d in ("changes", "status"): (target / d).mkdir(exist_ok=True)
    lock = {"schema_version": 1, "product": "Controlroom", "version": VERSION, "config": config,
            "files": {p: sha(target / p) for p in sorted(plan)}}
    (target / ".controlroom.lock").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    if legacy: (target / ".repo-starter.lock").rename(target / ".repo-starter.lock.migrated")
    print(f"Controlroom {VERSION}: installed {len(plan)} files. Philosophies: {', '.join(config['philosophies']) or 'core only'}")
    if legacy: print("Migrated from repo-starter: .repo-starter.lock renamed to .repo-starter.lock.migrated")
    if v1: print("Migrated from repo-starter v1: CLAUDE.md copy of the canon replaced.")
    if moved: print("Moved pre-existing rules under '## Project' in AGENTS.md; quote them in the pull request.")
    if stale: print("Removed files no longer installed:\n- " + "\n- ".join(stale))
    if conflicts: print("Preserved local files requiring manual review:\n- " + "\n- ".join(conflicts))
    return conflicts


def prune(target, removed):
    """Delete folders that held removed files, only when now empty."""
    folders = []
    for rel in sorted(removed, key=lambda r: -r.count("/")):
        d = (target / rel).parent
        while d != target and d.exists() and not any(d.iterdir()):
            d.rmdir(); folders.append(str(d.relative_to(target))); d = d.parent
    return folders


def uninstall(target, keep_agents=None):
    """keep_agents: None = ask (no terminal = keep), True = keep AGENTS.md, False = delete it."""
    target = Path(target).resolve(); lp = target / ".controlroom.lock"
    if not lp.exists(): raise SystemExit("No .controlroom.lock found. Refusing to guess what Controlroom owns.")
    files = json.loads(lp.read_text(encoding="utf-8")).get("files", {}); kept, removed = [], []
    if keep_agents is None and (target / "AGENTS.md").exists():
        keep_agents = ask("AGENTS.md holds the Project section. Delete it? [y/N] ").strip().lower() != "y"
    for rel, expected in files.items():
        p = target / rel
        if not p.exists(): continue
        if sha(p) != expected or (rel == "AGENTS.md" and keep_agents): kept.append(rel); continue
        p.unlink(); removed.append(rel)
    folders = prune(target, removed)
    lp.unlink()
    print(f"Removed {len(removed)} unchanged files. Kept {len(kept)} files. Removed {len(folders)} empty folders.")
    if kept: print("Kept (changed or declined):\n- " + "\n- ".join(kept))


def validate(target):
    target = Path(target); errors = []
    for f in ["AGENTS.md", "CLAUDE.md"]:
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
    version = (rs / "MANIFEST.txt").read_text().splitlines()[0].removeprefix("# version").strip()
    cfg = {"schema_version": 1, "profile": "parity", "philosophies": ["engineering"], "language": "en"}

    def fake_install(t, lock_order="path-first"):
        """A repo-starter install as its paste prompt produces it, with a filled Project section."""
        for rel in rs_files:
            (t / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(rs / rel, t / rel)
        agents = (t / "AGENTS.md").read_text(encoding="utf-8")
        project = project_section(agents).replace("- Stack: Markdown.", "- Stack: Parity test stack.")
        (t / "AGENTS.md").write_text(above_project(agents) + project, encoding="utf-8")
        rows = [(r, sha(t / r)) for r in rs_files]
        body = "".join(f"{r} {h}\n" if lock_order == "path-first" else f"{h}  {r}\n" for r, h in rows)
        if lock_order != "none": (t / ".repo-starter.lock").write_text(f"version {version}\n" + body, encoding="utf-8")
        return project

    def case(name, fn):
        with tempfile.TemporaryDirectory() as d:
            try: fn(Path(d))
            except AssertionError as e: errors.append(f"{name}: {e}")
            except SystemExit as e: errors.append(f"{name}: stopped: {e}")

    def migrate(t):
        project = fake_install(t)
        (t / ".claude/skills/tdd/SKILL.md").write_text("owner edit\n", encoding="utf-8")
        conflicts = install(t, cfg)
        assert project_section((t / "AGENTS.md").read_text(encoding="utf-8")) == project, "'## Project' not kept byte for byte"
        assert conflicts == [".claude/skills/tdd/SKILL.md"], f"conflicts wrong: {conflicts}"
        assert (t / ".claude/skills/tdd/SKILL.md").read_text() == "owner edit\n", "owner-edited file overwritten"
        assert not (t / ".repo-starter.lock").exists(), "legacy lock not retired"
        assert all((t / rel).exists() for rel in rs_files), "file lost in migration"
        assert validate(t) == 0

    def sha256sum_order(t):
        fake_install(t, "hash-first"); install(t, cfg)
        assert (t / ".controlroom.lock").exists()

    def edited_canon_stops(t):
        fake_install(t)
        (t / "AGENTS.md").write_text("Owner canon edit.\n" + (t / "AGENTS.md").read_text(encoding="utf-8"), encoding="utf-8")
        (t / "GEMINI.md").write_text("Owner Gemini rules.\n", encoding="utf-8")
        before = {p: p.read_bytes() for p in t.rglob("*") if p.is_file()}
        try: install(t, cfg); raise AssertionError("migration went ahead over an edited AGENTS.md")
        except SystemExit: pass
        assert before == {p: p.read_bytes() for p in t.rglob("*") if p.is_file()}, "files changed although migration stopped"

    def v1_upgrade(t):
        # v1 shipped only AGENTS.md and a full copy as CLAUDE.md; anything else is the owner's.
        fake_install(t, "none")
        shutil.rmtree(t / ".claude"); shutil.rmtree(t / ".github")
        shutil.copy2(t / "AGENTS.md", t / "CLAUDE.md")
        (t / ".github").mkdir()
        (t / ".github/copilot-instructions.md").write_text("Owner Copilot rule.\n", encoding="utf-8")
        (t / ".github/pull_request_template.md").write_text("Owner template.\n", encoding="utf-8")
        conflicts = install(t, cfg)
        agents = (t / "AGENTS.md").read_text(encoding="utf-8")
        assert (t / "CLAUDE.md").read_bytes() == (ROOT / "CLAUDE.md").read_bytes(), "v1 CLAUDE.md not replaced"
        assert "Previous rules from `CLAUDE.md`" not in agents and "Previous rules from `AGENTS.md`" not in agents, "v1 canon copy quoted"
        assert "> Owner Copilot rule." in project_section(agents), "owner Copilot rules lost"
        assert (t / ".github/pull_request_template.md").read_text() == "Owner template.\n", "owner PR template overwritten"
        assert ".github/pull_request_template.md" in conflicts, "owner PR template not reported"

    for name, fn in [("migration", migrate), ("sha256sum-order lock", sha256sum_order),
                     ("edited AGENTS.md", edited_canon_stops), ("v1 upgrade", v1_upgrade)]:
        case(name, fn)
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
        (t / ".controlroom/core/00-language.md").write_text("owner edit\n", encoding="utf-8")
        install(t, dict(cfg, philosophies=["engineering"]))
        assert (t / ".controlroom/core/00-language.md").read_text() == "owner edit\n", "edited .controlroom file overwritten"
        assert not (t / ".controlroom/philosophies/work").exists(), "deselected philosophy left behind"
        (t / ".controlroom/core/00-language.md").write_bytes((ROOT / "core/00-language.md").read_bytes())
        sys.stdin = open("/dev/null") if Path("/dev/null").exists() else sys.stdin
        uninstall(t)
        assert (t / "AGENTS.md").exists(), "no terminal must mean keep AGENTS.md"
        (t / ".controlroom.lock").write_text("{}", encoding="utf-8")
        install(t, cfg)
        uninstall(t, keep_agents=False)
        assert not (t / "AGENTS.md").exists() and not (t / ".claude").exists() and not (t / ".controlroom.lock").exists()
    print("Self-test passed.")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("configure")
    for name in ("install", "update"):
        p = sub.add_parser(name); p.add_argument("target"); p.add_argument("--config"); p.add_argument("--non-interactive", action="store_true")
    p = sub.add_parser("uninstall"); p.add_argument("target")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--yes", dest="keep_agents", action="store_false", default=None, help="owner said: delete AGENTS.md")
    g.add_argument("--keep-agents", dest="keep_agents", action="store_true", help="owner said: keep AGENTS.md")
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
    elif a.cmd == "uninstall": uninstall(a.target, a.keep_agents)
    elif a.cmd == "validate": raise SystemExit(validate(a.target))
    elif a.cmd == "parity": raise SystemExit(parity(a.repo_starter))
    elif a.cmd == "package": package(a.output)
    elif a.cmd == "self-test": self_test()
    elif a.cmd == "version": print(VERSION)


if __name__ == "__main__": main()
