#!/usr/bin/env python3
import argparse, hashlib, json, shutil, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHILOSOPHIES = ["engineering", "work", "personal", "writing", "research"]
BASE_FILES = ["BUILD.md", "STATUS.md", "VERSIONS.md", "READ_ME_FIRST.txt", "languages.csv"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_config(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    chosen = data.get("philosophies", [])
    unknown = sorted(set(chosen) - set(PHILOSOPHIES))
    if unknown: raise SystemExit(f"Unknown philosophies: {', '.join(unknown)}")
    if data.get("language") != "en": raise SystemExit("Controlroom currently requires language=en")
    return data

def choose():
    print("Controlroom must ask before installing anything.")
    print("Which Controlroom philosophies should this repository follow?")
    print("Core language, integrity, safety, and change-control rules are mandatory.")
    print("0) Core only\nA) All philosophies")
    for i, name in enumerate(PHILOSOPHIES, 1): print(f"{i}) {name.title()}")
    raw = input("Choose All, Core only, or comma-separated numbers: ").strip().lower()
    if raw in ("a", "all"): chosen = PHILOSOPHIES[:]; profile = "all"
    elif raw in ("0", "core"): chosen = []; profile = "core-only"
    elif not raw: raise SystemExit("No selection made. Nothing was installed.")
    else:
        try: chosen = [PHILOSOPHIES[int(x.strip())-1] for x in raw.split(",")]
        except (ValueError, IndexError): raise SystemExit("Invalid selection")
        chosen = list(dict.fromkeys(chosen)); profile = "custom"
    return {"schema_version":1,"profile":profile,"philosophies":chosen,"language":"en","workflow":{"development_branch":"dev","release_branch":"main","require_independent_review":True}}

def generate_agents(config, project=None):
    parts = [(ROOT/"templates/AGENTS.header.md").read_text(), "\n# Mandatory Repo-Starter base philosophy\n", (ROOT/"philosophies/repo-starter/instructions.md").read_text(), "\n# Mandatory core\n"]
    for p in sorted((ROOT/"core").glob("*.md")): parts.append(p.read_text())
    parts.append((ROOT/"templates/AGENTS.workflow.md").read_text())
    if config["philosophies"]:
        parts.append("\n# Selected philosophies\n")
        for name in config["philosophies"]: parts.append((ROOT/f"philosophies/{name}/instructions.md").read_text())
    parts.append(project if project else (ROOT/"templates/PROJECT.md").read_text())
    return "\n\n".join(x.strip() for x in parts) + "\n"

def project_section(path):
    if not path.exists(): return None
    text = path.read_text(encoding="utf-8")
    marker = "## Project"
    return text[text.index(marker):] if marker in text else None

def wanted(config):
    paths = BASE_FILES + ["CLAUDE.md", ".github/copilot-instructions.md", ".github/pull_request_template.md", ".github/ISSUE_TEMPLATE/plan.yml", ".github/workflows/ci.yml", ".github/workflows/release.yml", ".claude/agents/code-reviewer.md"]
    paths += [str(p.relative_to(ROOT)) for p in (ROOT/".claude/skills").rglob("*") if p.is_file()]
    return paths

def write_lock(target, installed, config):
    lock={"schema_version":1,"product":"Controlroom","config":config,"files":{p:sha(target/p) for p in installed}}
    (target/".controlroom.lock").write_text(json.dumps(lock,indent=2)+"\n",encoding="utf-8")

def install(target, config, update=False):
    target=Path(target).resolve(); target.mkdir(parents=True,exist_ok=True)
    lock_path=target/".controlroom.lock"; old={}
    if lock_path.exists(): old=json.loads(lock_path.read_text()).get("files",{})
    elif (target/".repo-starter.lock").exists():
        try: old=json.loads((target/".repo-starter.lock").read_text()).get("files",{})
        except json.JSONDecodeError: raise SystemExit("Legacy .repo-starter.lock is invalid; stop and inspect it manually.")
    project=project_section(target/"AGENTS.md")
    generated={"AGENTS.md":generate_agents(config,project)}
    installed=[]; conflicts=[]
    for rel in wanted(config):
        src=ROOT/rel; dst=target/rel
        if dst.exists() and rel in old and sha(dst)!=old[rel]: conflicts.append(rel); continue
        if dst.exists() and rel not in old and rel not in ("CLAUDE.md",): conflicts.append(rel); continue
        dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst); installed.append(rel)
    for rel,text in generated.items():
        dst=target/rel
        if dst.exists() and rel in old and sha(dst)!=old[rel]: conflicts.append(rel); continue
        if dst.exists() and rel not in old and project is None: conflicts.append(rel); continue
        dst.write_text(text,encoding="utf-8"); installed.append(rel)
    cr=target/".controlroom"; cr.mkdir(exist_ok=True)
    (cr/"config.json").write_text(json.dumps(config,indent=2)+"\n",encoding="utf-8"); installed.append(".controlroom/config.json")
    for folder in ("core","philosophies"):
        for src in (ROOT/folder).rglob("*.md"):
            if folder=="philosophies" and src.parent.name != "repo-starter" and src.parent.name not in config["philosophies"]: continue
            rel=Path(".controlroom")/src.relative_to(ROOT); dst=target/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst); installed.append(str(rel))
    for d in ("changes","status"): (target/d).mkdir(exist_ok=True)
    write_lock(target,sorted(set(installed)),config)
    if (target/".repo-starter.lock").exists(): (target/".repo-starter.lock").rename(target/".repo-starter.lock.migrated")
    print(f"Installed {len(set(installed))} files. Philosophies: {', '.join(config['philosophies']) or 'core only'}")
    if conflicts: print("Preserved local files requiring manual review:\n- " + "\n- ".join(sorted(set(conflicts))))

def uninstall(target):
    target=Path(target).resolve(); lp=target/".controlroom.lock"
    if not lp.exists(): raise SystemExit("No .controlroom.lock found. Refusing to guess what Controlroom owns.")
    lock=json.loads(lp.read_text()); kept=[]; removed=[]
    for rel,expected in lock.get("files",{}).items():
        p=target/rel
        if p.exists() and sha(p)==expected: p.unlink(); removed.append(rel)
        elif p.exists(): kept.append(rel)
    lp.unlink()
    print(f"Removed {len(removed)} unchanged files. Preserved {len(kept)} edited files.")
    if kept: print("Preserved:\n- " + "\n- ".join(kept))

def validate(target):
    target=Path(target); errors=[]
    for f in ["AGENTS.md","CLAUDE.md","BUILD.md","STATUS.md","VERSIONS.md"]:
        if not (target/f).is_file(): errors.append(f"Missing {f}")
    lp=target/".controlroom.lock"
    if lp.exists():
        try:
            lock=json.loads(lp.read_text())
            for rel,h in lock.get("files",{}).items():
                p=target/rel
                if not p.exists(): errors.append(f"Locked file missing: {rel}")
                elif sha(p)!=h: errors.append(f"Locked file changed: {rel}")
        except Exception as e: errors.append(f"Invalid lock: {e}")
    if errors: print("Validation failed:\n- " + "\n- ".join(errors)); return 1
    print("Validation passed."); return 0

def package(output):
    out=Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for p in ROOT.rglob("*"):
            if p.is_file() and ".git" not in p.parts and p.resolve()!=out.resolve(): z.write(p,p.relative_to(ROOT.parent))
    print(out)

def self_test():
    with tempfile.TemporaryDirectory() as d:
        cfg={"schema_version":1,"profile":"test","philosophies":["engineering","work"],"language":"en"}
        install(d,cfg); assert (Path(d)/"AGENTS.md").is_file(); assert validate(d)==0; uninstall(d); assert not (Path(d)/"AGENTS.md").exists()
    print("Self-test passed.")

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("configure")
    p=sub.add_parser("install"); p.add_argument("target"); p.add_argument("--config"); p.add_argument("--non-interactive",action="store_true")
    p=sub.add_parser("update"); p.add_argument("target"); p.add_argument("--config"); p.add_argument("--non-interactive",action="store_true")
    p=sub.add_parser("uninstall"); p.add_argument("target")
    p=sub.add_parser("validate"); p.add_argument("target")
    p=sub.add_parser("package"); p.add_argument("--output",required=True)
    sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="configure":
        cfg=choose(); out=Path("controlroom.config.json"); out.write_text(json.dumps(cfg,indent=2)+"\n"); print(f"Wrote {out}. Review it before installation.")
    elif a.cmd == "install":
        if a.non_interactive:
            if not a.config: raise SystemExit("--non-interactive requires --config")
            cfg=load_config(a.config)
        else:
            if a.config: raise SystemExit("To bypass the question, --config must be combined with --non-interactive")
            cfg=choose()
        install(a.target,cfg,False)
    elif a.cmd == "update":
        if a.non_interactive:
            if not a.config: raise SystemExit("--non-interactive requires --config")
            cfg=load_config(a.config)
        elif a.config:
            raise SystemExit("To use --config during update, also pass --non-interactive")
        else:
            existing=Path(a.target)/".controlroom/config.json"
            if existing.exists():
                cfg=load_config(existing)
                print("Keeping the existing Controlroom philosophy selection.")
            else:
                cfg=choose()
        install(a.target,cfg,True)
    elif a.cmd=="uninstall": uninstall(a.target)
    elif a.cmd=="validate": raise SystemExit(validate(a.target))
    elif a.cmd=="package": package(a.output)
    elif a.cmd=="self-test": self_test()
if __name__=="__main__": main()
