import re
import shutil
from pathlib import Path

# Mapping personnalisable des appareils vers les dossiers
DEVICE_MAPPING = {
    "iphone": "mobile",
    "android": "mobile",
    "ipad": "tablet",
    "tablet": "tablet",
}

def organiser_images():
    # Demande à l'utilisateur les répertoires de travail
    source_input = input("Dossier contenant les images [par défaut: .] : ").strip()
    dossier_source = Path(source_input) if source_input else Path(".")

    if not dossier_source.exists():
        print(f"Erreur : Le dossier source '{dossier_source}' n'existe pas.")
        return

    dest_input = input("Dossier de destination pour copier l'arborescence [par défaut: même dossier] : ").strip()
    dossier_dest = Path(dest_input) if dest_input else dossier_source

    # Format attendu : {numero}-{appareil}-{langue}.{extension}
    pattern = re.compile(r"^(\d+)_([a-zA-Z0-9]+)_([a-zA-Z]{2})\.(png|jpg|jpeg|webp)$", re.IGNORECASE)

    fichiers_traites = 0
    for fichier in dossier_source.iterdir():
        if not fichier.is_file():
            continue

        match = pattern.match(fichier.name)
        if match:
            numero, appareil, langue, ext = match.groups()
            
            categorie = DEVICE_MAPPING.get(appareil.lower(), appareil.lower())
            
            # Arborescence : destination / langue / categorie
            dossier_cible = dossier_dest / langue.lower() / categorie
            dossier_cible.mkdir(parents=True, exist_ok=True)
            
            nouveau_fichier = dossier_cible / f"{numero}.{ext.lower()}"
            
            # Utilisation de shutil.copy2 pour copier l'image tout en préservant ses métadonnées
            shutil.copy2(str(fichier), str(nouveau_fichier))
            print(f"Copié : {fichier.name} ➔ {nouveau_fichier}")
            fichiers_traites += 1

    print(f"\nOpération terminée. {fichiers_traites} image(s) copiée(s).")

if __name__ == "__main__":
    organiser_images()