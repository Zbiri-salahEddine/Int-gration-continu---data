"""Rejoue un scénario d'échec ou de panne sur une copie temporaire du projet.

    python scenarios/scenario.py bug_generation
    python scenarios/scenario.py --injecter-seulement bug_traitement   # utilisé en CI

Attention : chaque scénario repart d'un environnement vide (docker compose down -v).
La sortie est enregistrée dans captures/<scenario>.log.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CAPTURES = RACINE / "captures"
EXCLUS = shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache", "captures", "*.pdf")

BUGS = {
    "bug_generation": ("pipeline/generation.py", '"7500.75"', '"7500,75"'),
    "bug_traitement": ("pipeline/traitement.py", "t.montant > seuil", "t.montant >= seuil"),
}

PIPELINE = ["run_pipeline.py"]
SCENARIOS = {
    "bug_generation": [PIPELINE],
    "bug_traitement": [PIPELINE],
    "panne_insertion": [[*PIPELINE, "--simuler-pannes-insertion", "2"]],
    "panne_insertion_definitive": [
        [*PIPELINE, "--simuler-pannes-insertion", "99"],
        ["run_pipeline.py", "traitement"],
        ["run_pipeline.py", "tests-integration"],
    ],
    "panne_telechargement": [[*PIPELINE, "--simuler-pannes-telechargement", "3"]],
}


def injecter(nom: str, racine: Path) -> None:
    fichier, ancien, nouveau = BUGS[nom]
    chemin = racine / fichier
    texte = chemin.read_text(encoding="utf-8")
    if ancien not in texte:
        sys.exit(f"Texte à remplacer introuvable dans {fichier} : {ancien}")
    chemin.write_text(texte.replace(ancien, nouveau, 1), encoding="utf-8")
    print(f"Bug injecté dans {fichier} : {ancien}  ->  {nouveau}", flush=True)


def executer(commande: list[str], dossier: Path, journal) -> int:
    def ecrire(texte: str) -> None:
        sys.stdout.write(texte)
        sys.stdout.flush()
        journal.write(texte)

    environnement = {**os.environ, "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
    ecrire(f"\n$ python {' '.join(commande)}\n")
    processus = subprocess.Popen(
        [sys.executable, *commande], cwd=dossier, env=environnement, text=True, encoding="utf-8",
        errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    for ligne in processus.stdout:
        ecrire(ligne)
    code = processus.wait()
    ecrire(f"[code de sortie : {code}]\n")
    return code


def compose_down() -> None:
    subprocess.run(["docker", "compose", "down", "-v"], cwd=RACINE, check=True, capture_output=True)


def lancer(nom: str) -> int:
    CAPTURES.mkdir(exist_ok=True)
    compose_down()
    try:
        with tempfile.TemporaryDirectory(prefix="scenario-", ignore_cleanup_errors=True) as temporaire:
            copie = Path(temporaire) / "projet"
            shutil.copytree(RACINE, copie, ignore=EXCLUS)
            if nom in BUGS:
                injecter(nom, copie)
            with (CAPTURES / f"{nom}.log").open("w", encoding="utf-8", newline="\n") as journal:
                if nom in BUGS:
                    fichier, ancien, nouveau = BUGS[nom]
                    journal.write(f"Bug injecté dans {fichier} : {ancien}  ->  {nouveau}\n")
                codes = [executer(commande, copie, journal) for commande in SCENARIOS[nom]]
            return codes[-1]
    finally:
        compose_down()


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parseur.add_argument("scenario", choices=sorted(SCENARIOS))
    parseur.add_argument("--injecter-seulement", action="store_true", help="modifie le code en place, sans rien lancer")
    args = parseur.parse_args()
    if args.injecter_seulement:
        if args.scenario not in BUGS:
            sys.exit(f"{args.scenario} n'injecte pas de bug dans le code")
        injecter(args.scenario, RACINE)
        return
    sys.exit(lancer(args.scenario))


if __name__ == "__main__":
    main()
