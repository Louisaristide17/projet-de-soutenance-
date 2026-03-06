# ============================================================
#   SCRIPT : Liaison et fusion de 3 bases de données Excel
#   Fichiers sources :
#       1. incidents.xlsx              (25 incidents, Abidjan général)
#       2. agressions_adjame_2025.xlsx (100 agressions, Adjamé)
#       3. braquage.xlsx               (48 braquages, Cocody 2024-2026)
#
#   Résultat : incidents_unifies.db   (table unifiée + tables séparées)
# ============================================================

import pandas as pd
import sqlite3
import numpy as np
import os

# ──────────────────────────────────────────────────────────────
# ÉTAPE 1 — LECTURE DES FICHIERS EXCEL
# ──────────────────────────────────────────────────────────────
print("=" * 60)
print("  ÉTAPE 1 : Lecture des fichiers Excel")
print("=" * 60)

# --- Fichier 1 : incidents.xlsx ---
df1 = pd.read_excel('incidents.xlsx', header=0)
df1 = df1.dropna(how='all')
print(f"✅ incidents.xlsx          → {len(df1):>3} lignes lues")

# --- Fichier 2 : agressions_adjame_2025.xlsx ---
df2 = pd.read_excel('agressions_adjame_2025__1_.xlsx', header=0)
df2 = df2.dropna(how='all')
print(f"✅ agressions_adjame.xlsx  → {len(df2):>3} lignes lues")

# --- Fichier 3 : braquage.xlsx (titre sur ligne 1, colonnes ligne 3) ---
df3 = pd.read_excel('braquage.xlsx', header=2)
df3 = df3.dropna(how='all')
print(f"✅ braquage.xlsx           → {len(df3):>3} lignes lues")


# ──────────────────────────────────────────────────────────────
# ÉTAPE 2 — NORMALISATION DE CHAQUE FICHIER
#   On ramène chaque fichier vers un schéma commun :
#
#   id_original | source_fichier | date | heure | quartier |
#   commune | lieu | adresse | type_incident | categorie |
#   arme | suspects | victimes | blesses | deces |
#   montant_fcfa | arrestation | nb_arrestations |
#   mode_operatoire | vehicule | butin | description | source
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  ÉTAPE 2 : Normalisation des colonnes")
print("=" * 60)


# ─────────────────────────────────────
#  FICHIER 1 : incidents.xlsx
# ─────────────────────────────────────
def normaliser_incidents(df):
    """
    Colonnes d'origine :
    description, type_braquage, lieu, quartier, date, heure,
    nb_braqueurs, arme, morts, blesses, somme_fcfa,
    arrestation, nb_arrestations, source
    """
    n = pd.DataFrame()

    n['id_original']      = range(1, len(df) + 1)
    n['source_fichier']   = 'incidents.xlsx'
    n['date']             = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    n['heure']            = df['heure'].astype(str).str.strip().replace('nan', None)
    n['quartier']         = df['quartier'].astype(str).str.strip()
    n['commune']          = df['quartier'].astype(str).str.strip()  # même valeur ici
    n['lieu']             = df['lieu'].astype(str).str.strip()
    n['adresse']          = None
    n['type_incident']    = df['type_braquage'].astype(str).str.strip()
    n['categorie']        = 'braquage'
    n['arme']             = df['arme'].astype(str).str.strip().replace('nan', None)
    n['suspects']         = pd.to_numeric(df['nb_braqueurs'], errors='coerce')
    n['victimes']         = None   # non disponible dans ce fichier
    n['blesses']          = pd.to_numeric(df['blesses'], errors='coerce')
    n['deces']            = pd.to_numeric(df['morts'], errors='coerce')
    n['montant_fcfa']     = pd.to_numeric(df['somme_fcfa'], errors='coerce')
    n['arrestation']      = df['arrestation'].astype(str).str.lower().str.strip()
    n['nb_arrestations']  = pd.to_numeric(df['nb_arrestations'], errors='coerce')
    n['mode_operatoire']  = None
    n['vehicule']         = None
    n['butin']            = None
    n['description']      = df['description'].astype(str).str.strip()
    n['source']           = df['source'].astype(str).str.strip()

    return n

df1_norm = normaliser_incidents(df1)
print(f"✅ incidents.xlsx normalisé    → {len(df1_norm)} lignes")


# ─────────────────────────────────────
#  FICHIER 2 : agressions_adjame_2025.xlsx
# ─────────────────────────────────────
def normaliser_agressions(df):
    """
    Colonnes d'origine :
    ID, Date, Heure, Commune, Lieu, Type d'agression, Victime, Arme
    """
    n = pd.DataFrame()

    n['id_original']      = df['ID']
    n['source_fichier']   = 'agressions_adjame_2025.xlsx'
    n['date']             = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    n['heure']            = df['Heure'].astype(str).str.strip().replace('nan', None)
    n['quartier']         = df['Commune'].astype(str).str.strip()
    n['commune']          = df['Commune'].astype(str).str.strip()
    n['lieu']             = df['Lieu'].astype(str).str.strip()
    n['adresse']          = None
    n['type_incident']    = df["Type d'agression"].astype(str).str.strip()

    # Catégoriser automatiquement le type d'agression
    def categoriser(t):
        t = str(t).lower()
        if 'braquage' in t:       return 'braquage'
        if 'agression' in t:      return 'agression'
        if 'vol' in t:            return 'vol'
        if 'pickpocket' in t:     return 'vol'
        return 'agression'

    n['categorie']        = df["Type d'agression"].apply(categoriser)
    n['arme']             = df['Arme'].astype(str).str.strip().replace('nan', None)
    n['suspects']         = None  # non disponible
    n['victimes']         = df['Victime'].astype(str).str.strip()
    n['blesses']          = None
    n['deces']            = None
    n['montant_fcfa']     = None
    n['arrestation']      = None
    n['nb_arrestations']  = None
    n['mode_operatoire']  = None
    n['vehicule']         = None
    n['butin']            = None
    n['description']      = (
        df["Type d'agression"].astype(str) + ' — ' +
        df['Lieu'].astype(str) + ', ' +
        df['Commune'].astype(str)
    )
    n['source']           = 'agressions_adjame_2025.xlsx'

    return n

df2_norm = normaliser_agressions(df2)
print(f"✅ agressions_adjame normalisé → {len(df2_norm)} lignes")


# ─────────────────────────────────────
#  FICHIER 3 : braquage.xlsx
# ─────────────────────────────────────
def normaliser_braquage(df):
    """
    Colonnes d'origine :
    ID, Date, Heure, Jour, Quartier, Lieu, Adresse, Type braquage,
    Mode opératoire, Suspects, Armes utilisées, Victimes, Blessés,
    Décès, Butin, Montant (FCFA), Véhicule suspect, Signalement,
    Arrestation, Source
    """
    n = pd.DataFrame()

    n['id_original']      = df['ID']
    n['source_fichier']   = 'braquage.xlsx'
    n['date']             = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    n['heure']            = df['Heure'].astype(str).str.strip().replace('nan', None)
    n['quartier']         = df['Quartier'].astype(str).str.strip()
    n['commune']          = df['Quartier'].astype(str).str.extract(r'^(\w+)', expand=False).str.strip()
    n['lieu']             = df['Lieu'].astype(str).str.strip()
    n['adresse']          = df['Adresse'].astype(str).str.strip().replace('nan', None)
    n['type_incident']    = df['Type braquage'].astype(str).str.strip()
    n['categorie']        = 'braquage'
    n['arme']             = df['Armes utilisées'].astype(str).str.strip().replace('nan', None)
    n['suspects']         = pd.to_numeric(df['Suspects'], errors='coerce')
    n['victimes']         = pd.to_numeric(df['Victimes'], errors='coerce')
    n['blesses']          = pd.to_numeric(df['Blessés'], errors='coerce')
    n['deces']            = pd.to_numeric(df['Décès'], errors='coerce')
    n['montant_fcfa']     = pd.to_numeric(df['Montant (FCFA)'], errors='coerce')
    n['arrestation']      = df['Arrestation'].astype(str).str.lower().str.strip()
    n['nb_arrestations']  = None  # pas dans ce fichier
    n['mode_operatoire']  = df['Mode opératoire'].astype(str).str.strip().replace('nan', None)
    n['vehicule']         = df['Véhicule suspect'].astype(str).str.strip().replace('nan', None)
    n['butin']            = df['Butin'].astype(str).str.strip().replace('nan', None)
    n['description']      = (
        df['Type braquage'].astype(str) + ' — ' +
        df['Lieu'].astype(str) + ', ' +
        df['Quartier'].astype(str)
    )
    n['source']           = df['Source'].astype(str).str.strip()

    return n

df3_norm = normaliser_braquage(df3)
print(f"✅ braquage.xlsx normalisé     → {len(df3_norm)} lignes")


# ──────────────────────────────────────────────────────────────
# ÉTAPE 3 — FUSION EN UN SEUL DATAFRAME
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  ÉTAPE 3 : Fusion des 3 bases en une seule")
print("=" * 60)

df_uni = pd.concat([df1_norm, df2_norm, df3_norm], ignore_index=True)

# Ajouter un ID global unique
df_uni.insert(0, 'id_global', range(1, len(df_uni) + 1))

# Nettoyage final
df_uni['arme']           = df_uni['arme'].replace(['nan', 'None', 'NaN', ''], None)
df_uni['mode_operatoire']= df_uni['mode_operatoire'].replace(['nan', 'None', 'NaN', ''], None)
df_uni['vehicule']       = df_uni['vehicule'].replace(['nan', 'None', 'NaN', ''], None)
df_uni['adresse']        = df_uni['adresse'].replace(['nan', 'None', 'NaN', ''], None)
df_uni['butin']          = df_uni['butin'].replace(['nan', 'None', 'NaN', ''], None)
df_uni['heure']          = df_uni['heure'].replace(['nan', 'None', 'NaN', ''], None)

print(f"📊 Total lignes fusionnées : {len(df_uni)}")
print(f"   ├─ incidents.xlsx         : {len(df1_norm)}")
print(f"   ├─ agressions_adjame.xlsx : {len(df2_norm)}")
print(f"   └─ braquage.xlsx          : {len(df3_norm)}")
print(f"\n📋 Colonnes unifiées ({len(df_uni.columns)}) :")
for col in df_uni.columns:
    non_null = df_uni[col].notna().sum()
    print(f"   • {col:<22} → {non_null:>3} valeurs renseignées")


# ──────────────────────────────────────────────────────────────
# ÉTAPE 4 — CRÉATION DE LA BASE DE DONNÉES SQLite
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  ÉTAPE 4 : Écriture dans la base de données SQLite")
print("=" * 60)

connexion = sqlite3.connect('incidents_unifies.db')

# ── Table principale : tous les incidents fusionnés ──
df_uni.to_sql('incidents', connexion, if_exists='replace', index=False)
print(f"✅ Table 'incidents' créée  → {len(df_uni)} lignes")

# ── Tables séparées par source (pour garder les données brutes) ──
df1_norm.to_sql('incidents_abidjan_general', connexion, if_exists='replace', index=False)
df2_norm.to_sql('agressions_adjame',         connexion, if_exists='replace', index=False)
df3_norm.to_sql('braquages_cocody',          connexion, if_exists='replace', index=False)
print("✅ Tables séparées créées   → incidents_abidjan_general, agressions_adjame, braquages_cocody")

# ── Vue SQL pour interroger facilement ──
connexion.execute("DROP VIEW IF EXISTS vue_braquages")
connexion.execute("""
    CREATE VIEW vue_braquages AS
    SELECT
        id_global, date, heure, quartier, commune, lieu,
        type_incident, categorie, arme,
        suspects, victimes, blesses, deces,
        montant_fcfa, arrestation, source_fichier, source
    FROM incidents
    WHERE categorie = 'braquage'
    ORDER BY date DESC
""")
connexion.execute("DROP VIEW IF EXISTS vue_agressions")
connexion.execute("""
    CREATE VIEW vue_agressions AS
    SELECT
        id_global, date, heure, quartier, commune, lieu,
        type_incident, categorie, arme, victimes, source_fichier
    FROM incidents
    WHERE categorie IN ('agression', 'vol')
    ORDER BY date DESC
""")
print("✅ Vues SQL créées          → vue_braquages, vue_agressions")
connexion.commit()


# ──────────────────────────────────────────────────────────────
# ÉTAPE 5 — VÉRIFICATION ET STATISTIQUES CROISÉES
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  ÉTAPE 5 : Vérification et statistiques")
print("=" * 60)

cur = connexion.cursor()

# Total global
cur.execute("SELECT COUNT(*) FROM incidents")
print(f"\n📈 Total incidents unifiés : {cur.fetchone()[0]}")

# Par source
print("\n📂 Répartition par fichier source :")
cur.execute("SELECT source_fichier, COUNT(*) FROM incidents GROUP BY source_fichier")
for row in cur.fetchall():
    print(f"   • {row[0]:<38} → {row[1]} incidents")

# Par catégorie
print("\n🏷️  Répartition par catégorie :")
cur.execute("SELECT categorie, COUNT(*) FROM incidents GROUP BY categorie ORDER BY COUNT(*) DESC")
for row in cur.fetchall():
    print(f"   • {row[0]:<15} → {row[1]} incidents")

# Par commune
print("\n📍 Top 8 communes/quartiers :")
cur.execute("""
    SELECT commune, COUNT(*) as n
    FROM incidents
    GROUP BY commune
    ORDER BY n DESC LIMIT 8
""")
for row in cur.fetchall():
    print(f"   • {row[0]:<25} → {row[1]} incidents")

# Montants
cur.execute("SELECT SUM(montant_fcfa), COUNT(*) FROM incidents WHERE montant_fcfa IS NOT NULL")
res = cur.fetchone()
if res[0]:
    print(f"\n💰 Total dérobé (données disponibles) : {res[0]:,.0f} FCFA sur {res[1]} incidents")

# Doublons potentiels (même date + même lieu)
cur.execute("""
    SELECT date, lieu, COUNT(*) as c
    FROM incidents
    WHERE date IS NOT NULL AND lieu IS NOT NULL
    GROUP BY date, lieu
    HAVING c > 1
""")
doublons = cur.fetchall()
if doublons:
    print(f"\n⚠️  {len(doublons)} doublon(s) potentiel(s) détecté(s) (même date + même lieu) :")
    for d in doublons[:5]:
        print(f"   • {d[0]} | {d[1]} → {d[2]} fois")
else:
    print("\n✅ Aucun doublon détecté (par date + lieu)")

connexion.close()


# ──────────────────────────────────────────────────────────────
# ÉTAPE 6 — EXPORT EXCEL DE LA BASE UNIFIÉE (optionnel)
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  ÉTAPE 6 : Export Excel de synthèse")
print("=" * 60)

with pd.ExcelWriter('incidents_unifies.xlsx', engine='openpyxl') as writer:
    # Onglet 1 : tous les incidents
    df_uni.to_excel(writer, sheet_name='Tous les incidents', index=False)
    # Onglet 2 : uniquement les braquages
    df_uni[df_uni['categorie'] == 'braquage'].to_excel(
        writer, sheet_name='Braquages', index=False)
    # Onglet 3 : agressions et vols
    df_uni[df_uni['categorie'].isin(['agression', 'vol'])].to_excel(
        writer, sheet_name='Agressions & Vols', index=False)
    # Onglet 4 : résumé statistique
    resume = pd.DataFrame({
        'Fichier source': [
            'incidents.xlsx', 'agressions_adjame_2025.xlsx', 'braquage.xlsx', 'TOTAL'
        ],
        'Nombre de lignes': [
            len(df1_norm), len(df2_norm), len(df3_norm), len(df_uni)
        ],
        'Colonnes d\'origine': [14, 8, 20, '—'],
        'Colonnes unifiées': [len(df_uni.columns)] * 4,
    })
    resume.to_excel(writer, sheet_name='Résumé', index=False)

print("✅ incidents_unifies.xlsx créé avec 4 onglets")


# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  ✅ TERMINÉ !")
print("=" * 60)
print("""
Fichiers créés :
  📁 incidents_unifies.db    → Base SQLite avec 4 tables + 2 vues
  📁 incidents_unifies.xlsx  → Excel de synthèse avec 4 onglets

Tables SQLite disponibles :
  • incidents                  → Table principale unifiée (173 lignes)
  • incidents_abidjan_general  → Données brutes incidents.xlsx
  • agressions_adjame          → Données brutes agressions_adjame.xlsx
  • braquages_cocody           → Données brutes braquage.xlsx

Vues SQL disponibles :
  • vue_braquages    → SELECT * FROM vue_braquages
  • vue_agressions   → SELECT * FROM vue_agressions

Exemples de requêtes :
  SELECT * FROM incidents WHERE commune = 'Adjamé'
  SELECT * FROM incidents WHERE montant_fcfa > 1000000
  SELECT * FROM vue_braquages WHERE date >= '2025-01-01'
  SELECT quartier, COUNT(*) FROM incidents GROUP BY quartier
""")
