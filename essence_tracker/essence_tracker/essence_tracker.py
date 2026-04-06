# -*- coding: utf-8 -*-
import sqlite3
import os
import csv

# Note: mss, pytesseract et PIL sont importés mais non utilisés dans cette logique de base
# import mss
# import pytesseract
# from PIL import Image      

# ___________________________________________________ GLOBALES _____________________________________________________
DB_NAME = ""

# ___________________________________________________ FONCTIONS _____________________________________________________

def connexion():
    return sqlite3.connect(DB_NAME)

def cree_table_base(table):
    """Initialise la structure des tables pour le jeu actuel."""
    if(table == "Arknigts_Endfield"):
        try:
            with connexion() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON")

                cursor.execute("CREATE TABLE IF NOT EXISTS stat_principal  (id_principal   INTEGER PRIMARY KEY AUTOINCREMENT, Attribut_principal         TEXT NOT NULL)")
                cursor.execute("CREATE TABLE IF NOT EXISTS stat_secondaire (id_secondaire  INTEGER PRIMARY KEY AUTOINCREMENT, Statistique_secondaires    TEXT NOT NULL)")
                cursor.execute("CREATE TABLE IF NOT EXISTS Competences     (id_competences INTEGER PRIMARY KEY AUTOINCREMENT, Statistique_de_competences TEXT NOT NULL)")
                cursor.execute("CREATE TABLE IF NOT EXISTS Type_arme       (id_type        INTEGER PRIMARY KEY AUTOINCREMENT, Type_arme                  TEXT NOT NULL)")

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS Armes(
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          Nom_armes TEXT NOT NULL,
                          Rarete INTEGER NOT NULL,
                          Possetion TEXT,
                          id_type INTEGER NOT NULL,
                          id_principal INTEGER NOT NULL,
                          id_secondaire INTEGER NOT NULL,
                          id_competences INTEGER NOT NULL,
                          FOREIGN KEY (id_type)        REFERENCES Type_arme(id_type),
                          FOREIGN KEY (id_principal)   REFERENCES stat_principal(id_principal),
                          FOREIGN KEY (id_secondaire)  REFERENCES stat_secondaire(id_secondaire),
                          FOREIGN KEY (id_competences) REFERENCES Competences(id_competences)
                     )"""
                )
                conn.commit()
                print(f"Base de données Arknight Endfield prête !")

        except Exception as e:
            print(f"Erreur initialisation table arknight endfield : {e}")

    elif(table == "Arknights") : 
        try:
            with connexion() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.execute("CREATE TABLE IF NOT EXISTS rareter   (id_rareter   INTEGER PRIMARY KEY, rareter   TEXT)")
                cursor.execute("CREATE TABLE IF NOT EXISTS potentiel (id_potentiel INTEGER PRIMARY KEY, potentiel INTEGER)")

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS operator (
                        id_operator INTEGER PRIMARY KEY AUTOINCREMENT,
                        nom TEXT,
                        id_rareter INTEGER,
                        id_potentiel INTEGER,
                        FOREIGN KEY(id_rareter) REFERENCES rareter(id_rareter),
                        FOREIGN KEY(id_potentiel) REFERENCES potentiel(id_potentiel)
                    )"""
                )

                tables_tags = ['class', 'qualification', 'position', 'affix']

                for table in tables_tags:
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} (id_{table} INTEGER PRIMARY KEY, nom_{table} TEXT)")

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS operator_tags (
                        id_operator INTEGER,
                        source_table TEXT, -- 'class', 'position', etc.
                        id_tag INTEGER,
                        FOREIGN KEY(id_operator) REFERENCES operator(id_operator)
                    )"""
                )
            print(f"Base Arknights prête !")
        except Exception as e:
            print(f"Erreur initialisation table arknight : {e}")




def importer_csv(dossier_csv="donnees_csv"):
    """
    Parcourt tous les fichiers .csv d'un dossier et remplit les tables correspondantes.
    """
    if not os.path.exists(dossier_csv):
        print(f"Erreur : Le dossier '{dossier_csv}' n'existe pas.")
        return

    try:
        with connexion() as conn:
            cursor = conn.cursor()
            
            # --- ÉTAPE 1 : Remplir les tables de base (Tags, Rareté, Potentiel) ---
            # On liste les tables simples qui n'ont pas de dépendances
            tables_simples = ['rareter', 'potentiel', 'class', 'qualification', 'position', 'affix']
            
            for table in tables_simples:
                chemin = os.path.join(dossier_csv, f"{table}.csv")
                if os.path.exists(chemin):
                    with open(chemin, mode='r', encoding='utf-8') as f:
                        reader = csv.reader(f, delimiter=';')
                        next(reader) # Saute l'entête
                        for row in reader:
                            # Génère dynamiquement la requête INSERT INTO table VALUES (?, ?)
                            placeholders = ", ".join(["?"] * len(row))
                            cursor.execute(f"INSERT OR IGNORE INTO {table} VALUES ({placeholders})", row)
                    print(f"Table '{table}' mise à jour.")

            # --- ÉTAPE 2 : Remplir la table 'operator' ---
            chemin_ops = os.path.join(dossier_csv, "operator.csv")
            if os.path.exists(chemin_ops):

                # ── Vide et réinsère proprement à chaque import ──
                cursor.execute("DELETE FROM operator")
                cursor.execute("DELETE FROM operator_tags")  # cascade manuelle

                with open(chemin_ops, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        cursor.execute(
                            "INSERT INTO operator (id_operator, nom, id_rareter, id_potentiel) VALUES (?, ?, ?, ?)",
                            (row['id_operator'], row['nom'], row['id_rareter'], row['id_potentiel'])
                        )
                print("Table 'operator' mise à jour.")

            # --- ÉTAPE 3 : operator_tags ---
            chemin_tags = os.path.join(dossier_csv, "operator_tags.csv")
            if os.path.exists(chemin_tags):
                cursor.execute("DELETE FROM operator_tags")

                with open(chemin_tags, mode='r', encoding='utf-8-sig') as f:
                    lignes = list(csv.DictReader(f, delimiter=';'))

                if not lignes:
                    print("  operator_tags.csv est vide.")
                else:
                    inseres = 0
                    ignores = 0
                    for row in lignes:
                        id_op    = int(row['id_operator'])
                        source   = row['source_table'].strip()
                        id_tag   = int(row['id_tag'])

                        # Vérifie que l'opérateur existe
                        cursor.execute("SELECT 1 FROM operator WHERE id_operator = ?", (id_op,))
                        if not cursor.fetchone():
                            ignores += 1
                            continue

                        cursor.execute(
                            "INSERT OR IGNORE INTO operator_tags (id_operator, source_table, id_tag) VALUES (?, ?, ?)",
                            (id_op, source, id_tag)
                        )
                        inseres += 1

                    print(f"  ✔ operator_tags : {inseres} ligne(s) insérée(s), {ignores} ignorée(s).")
                    if ignores > 0:
                        print(f"     → {ignores} id_operator introuvables dans la table operator.")

                conn.commit()
                print("\n  ✔ Import terminé !")

    except Exception as e:
        print(f"Erreur lors de l'import complet : {e}")


def recuperer_liste_tags():
    tags_disponibles = {}
    tables = ['class', 'qualification', 'position', 'affix']
    try:
        with connexion() as conn:
            cursor = conn.cursor()
            for table in tables:
                cursor.execute(f"SELECT nom_{table} FROM {table}")
                # On stocke { 'Medic': 'class', 'Ranged': 'position', ... }
                for row in cursor.fetchall():
                    tags_disponibles[row[0]] = table
        return tags_disponibles
    except:
        return {}


# _______________________________________ MAIN ____________________________________________________________


while True:
    print("\n=== BIENVENUE DANS LE TRACKER ===")
    choix_jeu = input("1: Arknights\n2: Arknights Endfield\n0: Quitter\n> ")

    if choix_jeu == "0": break
    
    if choix_jeu == "1":
        DB_NAME = "BDD_Arknights.db"
        jeu_key = "Arknights"
    else:
        DB_NAME = "BDD_Arknights_Endfield.db"
        jeu_key = "Arknights_Endfield"

    while True:
        print(f"\n--- Menu [{DB_NAME}] ---")
        print("1: Initialiser les tables")
        print("2: Ajouter une donnée")
        print("3: Afficher les données")
        print("4: Retour au choix du jeu")
        val = input("> ")


        if val == "1":
            cree_table_base(jeu_key)
        
        elif val == "2":
            if jeu_key == "Arknights":
                print("1: Ajouter via CSV (Auto)")
                print("2: Ajouter à la main")
                choix = input("> ")

                if choix == "1":
                    importer_csv("donnees_csv")

                elif choix == "2":
                    # _________________________________________Ta logique manuelle habituelle..._______________________________________________________________________
                    pass

            else:
                #_____________________________________________________________ Logique insertion armes Endfield___________________________________________________________________
                print("Fonction insertion arme à appeler ici...")
        
        elif val == "3":
            if jeu_key == "Arknights":
                print("\n--- OPTIONS D'AFFICHAGE ---")
                print("1: Afficher TOUT")
                print("2: Filtrer par un TAG spécifique")
                sub_choix = input("> ")

                tag_filtre = None
                if sub_choix == "2":
                    tags_dict = recuperer_liste_tags()
                    liste_noms = sorted(list(tags_dict.keys()))
                    for i, t in enumerate(liste_noms):
                        print(f"{i}: {t}")
                    try:
                        idx = int(input("Numéro du tag : "))
                        tag_filtre = liste_noms[idx]
                    except:
                        print("Choix invalide."); continue

                with connexion() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()

                    # ── Étape 1 : récupère tous les opérateurs ───────────
                    cursor.execute("""
                        SELECT o.id_operator, o.nom, r.rareter
                        FROM operator o
                        LEFT JOIN rareter r ON o.id_rareter = r.id_rareter
                        ORDER BY o.id_rareter DESC, o.nom ASC
                    """)
                    operateurs = cursor.fetchall()   # tout en mémoire, curseur libre

                    # ── Étape 2 : récupère TOUS les tags d'un coup ───────
                    cursor.execute("""
                        SELECT ot.id_operator,
                               CASE ot.source_table
                                   WHEN 'class'         THEN cl.nom_class
                                   WHEN 'position'      THEN po.nom_position
                                   WHEN 'qualification' THEN qu.nom_qualification
                                   WHEN 'affix'         THEN af.nom_affix
                               END AS tag_nom
                        FROM operator_tags ot
                        LEFT JOIN class         cl ON ot.source_table='class'         AND ot.id_tag=cl.id_class
                        LEFT JOIN position      po ON ot.source_table='position'      AND ot.id_tag=po.id_position
                        LEFT JOIN qualification qu ON ot.source_table='qualification' AND ot.id_tag=qu.id_qualification
                        LEFT JOIN affix         af ON ot.source_table='affix'         AND ot.id_tag=af.id_affix
                        WHERE tag_nom IS NOT NULL
                    """)
                    tags_rows = cursor.fetchall()   # tout en mémoire aussi

                # ── Étape 3 : regroupe les tags par opérateur en Python ──
                tags_par_op = {}
                for row in tags_rows:
                    id_op = row["id_operator"]
                    if id_op not in tags_par_op:
                        tags_par_op[id_op] = set()
                    tags_par_op[id_op].add(row["tag_nom"].strip())

                # ── Étape 4 : affichage ───────────────────────────────────
                print(f"\n{'NOM':<22} | {'RARETÉ':<8} | TAGS")
                print("-" * 75)
                affiches = 0
                for op in operateurs:
                    id_op  = op["id_operator"]
                    nom    = op["nom"]
                    rarete = op["rareter"] if op["rareter"] else "?"
                    tags   = tags_par_op.get(id_op, set())

                    if tag_filtre and tag_filtre not in tags:
                        continue

                    t_str = ", ".join(sorted(tags)) if tags else "Aucun tag"
                    print(f"{nom:<22} | {str(rarete):<8} | {t_str}")
                    affiches += 1

                print(f"\n  Total : {affiches} opérateur(s)")

        elif val == "4": break
