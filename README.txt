╔═══════════════════════════════════════════════════════╗
║  RISQUE BRAQUAGE ABIDJAN — Guide de démarrage         ║
╚═══════════════════════════════════════════════════════╝

STRUCTURE DU PROJET
───────────────────
  projet/
  │
  ├── app.py                      ← Serveur Flask (NOUVEAU)
  ├── fusion_bases.py             ← Script de fusion Excel → DB
  ├── incidents_unifies.db        ← Base de données SQLite (générée)
  │
  ├── incidents.xlsx              ← Source 1
  ├── agressions_adjame_2025__1_.xlsx  ← Source 2
  ├── braquage.xlsx               ← Source 3
  │
  └── static/
      ├── index.html  ← INCHANGÉ (copie exacte de votre fichier)
      ├── style.css   ← INCHANGÉ (copie exacte de votre fichier)
      └── script.js   ← MODIFIÉ UNIQUEMENT : "const zones = {...}"
                        remplacé par fetch('/api/zones')
                        Toutes les fonctions (calculer, afficher,
                        animer, reset) sont conservées à l'identique.

INSTALLATION (une seule fois)
──────────────────────────────
  pip install flask pandas openpyxl

LANCEMENT
──────────
  1. python app.py
  2. Ouvrir → http://localhost:5000

CE QUI A CHANGÉ vs L'ORIGINAL
───────────────────────────────
  Avant  : script.js contenait des données codées en dur
           (base, nuit, jour hardcodés pour chaque quartier)

  Après  : script.js récupère ces valeurs depuis /api/zones
           Flask calcule les scores depuis les vraies données :
           • Adjamé   : 100 incidents réels → base=85%, nuit=95%
           • Cocody   :  48 incidents réels → base=41%, nuit=57%
           • Yopougon :  12 incidents réels → base=30%, nuit=42%
           • Abobo    :   0 données → valeurs estimées conservées

  L'interface HTML et le CSS sont strictement inchangés.

URGENCES
────────
  Police 110  ·  Gendarmerie 111  ·  SAMU 185
