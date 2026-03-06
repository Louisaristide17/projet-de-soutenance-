"""
╔═════════════════════════════════════════════════════╗
║  RISQUE BRAQUAGE ABIDJAN — Serveur Flask            ║
║  Démarrer : python app.py                           ║
║  Accès     : http://localhost:5000                  ║
╚═════════════════════════════════════════════════════╝

Architecture :
  /               → sert static/index.html
  /style.css      → sert static/style.css
  /script.js      → sert static/script.js
  /api/zones      → données calculées depuis la DB (JSON)
"""

from flask import Flask, jsonify, send_from_directory
import sqlite3, os

app = Flask(__name__, static_folder="static")
DB  = os.path.join(os.path.dirname(__file__), "incidents_unifies.db")


# ──────────────────────────────────────────────────────────
#  Utilitaire : requête SQLite
# ──────────────────────────────────────────────────────────
def q(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ──────────────────────────────────────────────────────────
#  Calcul du risque pour une commune donnée
# ──────────────────────────────────────────────────────────
def calcul_zone(commune, total_db, fallback=None, communes_extra=None):
    """
    Retourne un dict compatible avec la structure attendue par script.js :
      { nom, base, nuit, jour, conseil }
    communes_extra : liste de communes supplémentaires à inclure dans le calcul
    """
    # Construire la clause WHERE pour inclure communes satellites
    toutes = [commune] + (communes_extra or [])
    placeholders = ",".join("?" * len(toutes))

    stats = q(f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN CAST(substr(heure,1,2) AS INT) >= 18
                      OR CAST(substr(heure,1,2) AS INT) <  6
                     THEN 1 ELSE 0 END) AS nuit_count,
            SUM(CASE WHEN CAST(substr(heure,1,2) AS INT) BETWEEN 6 AND 17
                     THEN 1 ELSE 0 END) AS jour_count
        FROM incidents
        WHERE commune IN ({placeholders})
    """, tuple(toutes))

    nb = stats[0]["total"] if stats else 0

    # ── Si aucune donnée : utiliser les valeurs de secours ──
    if nb == 0:
        return fallback

    nuit_count = stats[0]["nuit_count"] or 0
    jour_count = stats[0]["jour_count"] or 0

    # ── Calcul du score de base (0–95) ──
    #    Normalisé sur la commune la plus risquée (Adjamé : 100 incidents = référence)
    #    Plancher à 30 : données limitées ≠ zone sûre (biais de signalement)
    MAX_INCIDENTS = 100
    base = max(30, min(88, round((nb / MAX_INCIDENTS) * 85)))

    # ── Scores nuit / jour ──
    total_avec_heure = nuit_count + jour_count
    if total_avec_heure > 0:
        ratio_nuit = nuit_count / total_avec_heure
        ratio_jour = jour_count / total_avec_heure
    else:
        ratio_nuit = 0.65  # valeur par défaut (majorité nocturne)
        ratio_jour = 0.35

    nuit = min(95, round(base * (0.6 + ratio_nuit * 0.8)))
    jour = max(8,  round(base * (0.2 + ratio_jour * 0.7)))

    # ── Conseil construit depuis les vraies données ──
    top_type = q(f"""
        SELECT type_incident, COUNT(*) n
        FROM incidents WHERE commune IN ({placeholders})
        GROUP BY type_incident ORDER BY n DESC LIMIT 1
    """, tuple(toutes))

    top_arme = q(f"""
        SELECT lower(trim(arme)) arme, COUNT(*) n
        FROM incidents WHERE commune IN ({placeholders}) AND arme IS NOT NULL
        GROUP BY lower(trim(arme)) ORDER BY n DESC LIMIT 1
    """, tuple(toutes))

    top_lieu = q(f"""
        SELECT lieu, COUNT(*) n
        FROM incidents WHERE commune IN ({placeholders})
        GROUP BY lieu ORDER BY n DESC LIMIT 1
    """, tuple(toutes))

    type_str = top_type[0]["type_incident"] if top_type else "incidents"
    arme_str = top_arme[0]["arme"]          if top_arme else "armes diverses"
    lieu_str = top_lieu[0]["lieu"]          if top_lieu else "voie publique"

    # Construire un conseil naturel
    parties = [
        f"Risque principal : {type_str.lower()} ({top_type[0]['n'] if top_type else '?'} cas recensés).",
        f"Arme la plus signalée : {arme_str}.",
        f"Zone la plus exposée : {lieu_str}.",
    ]
    if nuit > 75:
        parties.append("Évitez absolument de circuler seul(e) après 20h.")
    elif nuit > 55:
        parties.append("Redoublez de vigilance en soirée et gardez vos objets de valeur cachés.")
    else:
        parties.append("Restez vigilant(e) et privilégiez les axes éclairés.")

    conseil = " ".join(parties)

    return {
        "nom":     commune,
        "base":    base,
        "nuit":    nuit,
        "jour":    jour,
        "conseil": conseil,
    }


# ──────────────────────────────────────────────────────────
#  PAGE PRINCIPALE + FICHIERS STATIQUES
# ──────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/style.css")
def css():
    return send_from_directory("static", "style.css")

@app.route("/script.js")
def js():
    return send_from_directory("static", "script.js")


# ──────────────────────────────────────────────────────────
#  API — /api/zones
#  Retourne exactement la structure attendue par script.js :
#  { adjame: {nom, base, nuit, jour, conseil}, cocody: {...}, ... }
# ──────────────────────────────────────────────────────────
@app.route("/api/zones")
def api_zones():

    total_db = q("SELECT COUNT(*) n FROM incidents")[0]["n"]

    # ── Valeurs de secours pour les zones sans données (Abobo) ──
    #    Basées sur les rapports publics de sécurité d'Abidjan
    fallback_abobo = {
        "nom":     "Abobo",
        "base":    68,
        "nuit":    84,
        "jour":    42,
        "conseil": (
            "Zone à haut risque. Données limitées mais incidents fréquents rapportés. "
            "Ne marchez jamais seul(e) la nuit. Évitez la gare routière et PK18 après 20h. "
            "Privilégiez un taxi de confiance."
        ),
    }

    # ── Calcul des 4 zones ──
    zones = {
        "adjame":   calcul_zone("Adjamé",   total_db),
        "cocody":   calcul_zone("Cocody",   total_db),
        # Yopougon : inclut Niangon (commune limitrophe, même zone urbaine)
        "yopougon": calcul_zone("Yopougon", total_db, communes_extra=["Niangon"]),
        "abobo":    calcul_zone("Abobo",    total_db, fallback=fallback_abobo),
    }

    return jsonify(zones)


# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 52)
    print("  RISQUE BRAQUAGE ABIDJAN — Serveur démarré")
    print("  → Ouvrir : http://localhost:5000")
    print("=" * 52 + "\n")
    app.run(debug=True, port=5000)
