#!/usr/bin/env python3
"""Wendet das Viking-Code-Branding auf einen frischen MiMo-Code-Stand an.

Wird vom Sync-Workflow nach jedem Abgleich mit dem Original ausgeführt. Das
Branding liegt bewusst NICHT als Commit-Historie im Repo, sondern wird jedes
Mal neu aufgetragen — dadurch kann es beim Nachziehen der Upstream-Änderungen
keine Merge-Konflikte geben.

Angefasst wird nur der nach außen sichtbare Name. Technische Kennungen bleiben
unberührt, weil sie die Anbindung an Xiaomis Dienste tragen:

  * ``.mimocode/``      — Konfigverzeichnis (813 Fundstellen)
  * ``mimo-v2.5-pro``   — Modell-Kennungen der API
  * ``api.xiaomimimo.com`` und alle Repo-URLs
  * "MiMo Token Plan"   — Xiaomis Abo-Produkt, kein Branding von uns

Aufruf:
    python script/viking-branding.py            # anwenden
    python script/viking-branding.py --check    # nur prüfen, nichts schreiben
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Nur der Anzeigename. "MiMo Token Plan" enthält kein "MiMo Code" und bleibt
# damit automatisch unangetastet; Repo-URLs nutzen "MiMo-Code" mit Bindestrich
# und sind ebenfalls nicht betroffen.
TEXT_REPLACEMENTS = [
    ("MiMo Code", "Viking Code"),
]

SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".json", ".jsonc", ".md", ".go",
            ".txt", ".yml", ".yaml", ".toml"}

# Rechtliche und organisatorische Texte von Xiaomi — nicht umschreiben.
# Dazu die eigenen Werkzeugdateien: dort steht "MiMo Code" als Verweis auf das
# Originalprojekt und muss stehen bleiben, sonst schreibt sich das Skript bei
# jedem Lauf selbst um ("Spiegelung von Xiaomis Viking Code").
SKIP_FILES = {"LICENSE", "USE_RESTRICTIONS.md", "SECURITY.md", "CONTRIBUTING.md",
              "viking-branding.py", "viking-sync.yml"}
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".turbo", ".bundle"}

LOGO_PATH = REPO / "packages" / "opencode" / "src" / "cli" / "logo.ts"
PACKAGE_JSON = REPO / "packages" / "opencode" / "package.json"
OWN_WORKFLOW = "viking-sync.yml"

# VIKING im Zeichenstil des Originals. Alle Zeilen eines Blocks müssen exakt
# gleich lang sein, sonst verrutscht das Layout im Terminal.
LOGO_BLOCK = '''export const logo = {
  left: [
    "                                           ",
    "                                           ",
    " ██╗   ██╗██╗██╗  ██╗██╗███╗   ██╗ ██████╗ ",
    " ██║   ██║██║██║ ██╔╝██║████╗  ██║██╔════╝ ",
    " ██║   ██║██║█████╔╝ ██║██╔██╗ ██║██║  ███╗",
    " ╚██╗ ██╔╝██║██╔═██╗ ██║██║╚██╗██║██║   ██║",
    "  ╚████╔╝ ██║██║  ██╗██║██║ ╚████║╚██████╔╝",
    "   ╚═══╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ",
  ],
  right: [
    "                            RoGSlaqZ",
    "                                    ",
    " ██████╗  ██████╗  ██████╗  ███████╗",
    "██╔════╝ ██╔═══██╗ ██╔══██╗ ██╔════╝",
    "██║      ██║   ██║ ██║  ██║ █████╗  ",
    "██║      ██║   ██║ ██║  ██║ ██╔══╝  ",
    "╚██████╗ ╚██████╔╝ ██████╔╝ ███████╗",
    " ╚═════╝  ╚═════╝  ╚═════╝  ╚══════╝",
  ],
}'''

LOGO_THIN_BLOCK = '''export const logoThin = {
  left: [
    "                        ",
    "                        ",
    "█   █ █ █ █ █ █▄  █ █▀▀▀",
    "▀▄ ▄▀ █ █▀▄ █ █ ▀▄█ █ ▀█",
    "  ▀   ▀ ▀ ▀ ▀ ▀   ▀ ▀▀▀▀",
  ],
  right: [
    "            RoGSlaqZ",
    "                    ",
    "  █▀▀ █▀▀█ █▀▀▄ █▀▀▀",
    "  █   █  █ █  █ █▀▀ ",
    "  ▀▀▀ ▀▀▀▀ ▀▀▀  ▀▀▀▀",
  ],
}'''


def iter_files():
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in SUFFIXES:
            continue
        if path.name in SKIP_FILES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(REPO).parts):
            continue
        yield path


def apply_text(check: bool) -> list[str]:
    """Anzeigename ersetzen. Gibt die geänderten Dateien zurück."""
    touched = []
    for path in iter_files():
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        text = original
        for old, new in TEXT_REPLACEMENTS:
            text = text.replace(old, new)
        if text != original:
            touched.append(str(path.relative_to(REPO)).replace("\\", "/"))
            if not check:
                path.write_text(text, encoding="utf-8", newline="\n")
    return touched


def apply_logo(check: bool) -> bool:
    """Logo-Blöcke ersetzen, den Rest der Datei unangetastet lassen."""
    if not LOGO_PATH.exists():
        print(f"  ! {LOGO_PATH.relative_to(REPO)} fehlt — Logo übersprungen")
        return False
    original = LOGO_PATH.read_text(encoding="utf-8")
    text = re.sub(r"export const logo = \{.*?\n\}", LOGO_BLOCK, original,
                  count=1, flags=re.S)
    text = re.sub(r"export const logoThin = \{.*?\n\}", LOGO_THIN_BLOCK, text,
                  count=1, flags=re.S)
    if text == original:
        return False
    if not check:
        LOGO_PATH.write_text(text, encoding="utf-8", newline="\n")
    return True


def apply_bin(check: bool) -> bool:
    """``viking`` als Befehl ergänzen — ``mimo`` bleibt zusätzlich bestehen.

    Ergänzen statt ersetzen, damit Build- und Installationsskripte, die den
    alten Namen erwarten, weiterhin funktionieren.
    """
    if not PACKAGE_JSON.exists():
        return False
    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    binspec = data.get("bin")
    if not isinstance(binspec, dict) or "viking" in binspec:
        return False
    target = binspec.get("mimo") or next(iter(binspec.values()), None)
    if not target:
        return False
    # viking zuerst, damit es als primärer Name gilt
    data["bin"] = {"viking": target, **binspec}
    if not check:
        PACKAGE_JSON.write_text(json.dumps(data, indent=2) + "\n",
                                encoding="utf-8", newline="\n")
    return True


def strip_upstream_workflows(check: bool) -> list[str]:
    """Xiaomis CI-Workflows entfernen, den eigenen Sync behalten.

    Sonst laufen im Fork bei jedem Push fremde Test- und Release-Workflows
    mit, die hier weder gebraucht werden noch durchlaufen können.
    """
    wf_dir = REPO / ".github" / "workflows"
    if not wf_dir.is_dir():
        return []
    removed = []
    for path in sorted(wf_dir.iterdir()):
        if path.name == OWN_WORKFLOW or not path.is_file():
            continue
        removed.append(path.name)
        if not check:
            path.unlink()
    return removed


def strip_git_hooks(check: bool) -> bool:
    """Die husky-Hooks des Projekts entfernen.

    Der pre-push-Hook lässt ``bun typecheck`` über das gesamte Monorepo
    laufen. Das schlägt schon im unveränderten Original fehl (tsgo, der
    experimentelle TypeScript-Compiler, stolpert über
    packages/app/src/custom-elements.d.ts) und würde hier jeden Push
    blockieren — für einen Fork, in dem nur gebrandet und nicht entwickelt
    wird, ist diese Prüfung ohnehin nicht der richtige Ort.
    """
    husky = REPO / ".husky"
    if not husky.is_dir():
        return False
    if not check:
        shutil.rmtree(husky)
    return True


def main() -> int:
    check = "--check" in sys.argv
    print(f"Viking-Branding — {'Prüflauf' if check else 'anwenden'}")
    print(f"Repo: {REPO}")

    files = apply_text(check)
    print(f"  Anzeigename : {len(files)} Datei(en)")
    for f in files[:8]:
        print(f"      {f}")
    if len(files) > 8:
        print(f"      … und {len(files) - 8} weitere")

    print(f"  Logo        : {'geändert' if apply_logo(check) else 'schon aktuell'}")
    print(f"  CLI-Befehl  : {'viking ergänzt' if apply_bin(check) else 'schon vorhanden'}")

    workflows = strip_upstream_workflows(check)
    print(f"  Fremd-CI    : {len(workflows)} Workflow(s) entfernt")

    hooks = strip_git_hooks(check)
    print(f"  Git-Hooks   : {'husky entfernt' if hooks else 'schon entfernt'}")

    if check and (files or workflows or hooks):
        print("\nPrüflauf: Branding fehlt noch an den obigen Stellen.")
        return 1
    print("\nFertig." if not check else "\nPrüflauf: Branding ist vollständig.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
