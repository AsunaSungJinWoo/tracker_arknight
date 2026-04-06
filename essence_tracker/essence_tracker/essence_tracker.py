# -*- coding: utf-8 -*-
import sqlite3
import os
import csv

DB_NAME = ""

def connexion():
    return sqlite3.connect(DB_NAME)


def cree_table_base(jeu):
    try:
        with connexion() as conn:
            cursor = conn.cursor()

            if jeu == "Arknights":
                for t in ['operator_tags', 'operator', 'rareter', 'potentiel',
                          'class', 'qualification', 'position', 'affix']:
                    cursor.execute(f"DROP TABLE IF EXISTS {t}")

                cursor.execute("CREATE TABLE rareter   (id_rareter   INTEGER PRIMARY KEY, rareter   TEXT)")
                cursor.execute("CREATE TABLE potentiel (id_potentiel INTEGER PRIMARY KEY, potentiel INTEGER)")
                cursor.execute("""
                    CREATE TABLE operator (
                        id_operator  INTEGER PRIMARY KEY,
                        nom          TEXT NOT NULL,
                        id_rareter   INTEGER,
                        id_potentiel INTEGER,
                        FOREIGN KEY(id_rareter)   REFERENCES rareter(id_rareter),
                        FOREIGN KEY(id_potentiel) REFERENCES potentiel(id_potentiel)
                    )""")
                for t in ['class', 'qualification', 'position', 'affix']:
                    cursor.execute(f"CREATE TABLE {t} (id_{t} INTEGER PRIMARY KEY, nom_{t} TEXT)")
                cursor.execute("""
                    CREATE TABLE operator_tags (
                        id_operator  INTEGER,
                        source_table TEXT,
                        id_tag       INTEGER,
                        UNIQUE(id_operator, source_table, id_tag),
                        FOREIGN KEY(id_operator) REFERENCES operator(id_operator)
                    )""")

            elif jeu == "Arknights_Endfield":
                for t in ['Armes', 'Type_arme', 'stat_principal', 'stat_secondaire', 'Competences']:
                    cursor.execute(f"DROP TABLE IF EXISTS {t}")

                cursor.execute("CREATE TABLE stat_principal  (id_principal   INTEGER PRIMARY KEY AUTOINCREMENT, Attribut_principal         TEXT NOT NULL)")
                cursor.execute("CREATE TABLE stat_secondaire (id_secondaire  INTEGER PRIMARY KEY AUTOINCREMENT, Statistique_secondaires    TEXT NOT NULL)")
                cursor.execute("CREATE TABLE Competences     (id_competences INTEGER PRIMARY KEY AUTOINCREMENT, Statistique_de_competences TEXT NOT NULL)")
                cursor.execute("CREATE TABLE Type_arme       (id_type        INTEGER PRIMARY KEY AUTOINCREMENT, Type_arme                  TEXT NOT NULL)")
                cursor.execute("""
                    CREATE TABLE Armes (
                        id             INTEGER PRIMARY KEY AUTOINCREMENT,
                        Nom_armes      TEXT NOT NULL,
                        Rarete         INTEGER NOT NULL,
                        Possetion      TEXT,
                        id_type        INTEGER NOT NULL,
                        id_principal   INTEGER NOT NULL,
                        id_secondaire  INTEGER NOT NULL,
                        id_competences INTEGER NOT NULL,
                        FOREIGN KEY (id_type)        REFERENCES Type_arme(id_type),
                        FOREIGN KEY (id_principal)   REFERENCES stat_principal(id_principal),
                        FOREIGN KEY (id_secondaire)  REFERENCES stat_secondaire(id_secondaire),
                        FOREIGN KEY (id_competences) REFERENCES Competences(id_competences)
                    )""")

            conn.commit()
            print("  ✔ Tables réinitialisées et recréées proprement !")
    except Exception as e:
        print(f"  ✘ Erreur : {e}")


def importer_csv(dossier_csv="donnees_csv"):
    if not os.path.exists(dossier_csv):
        print(f"  ✘ Le dossier '{dossier_csv}' n'existe pas.")
        return
    try:
        with connexion() as conn:
            cursor = conn.cursor()

            for table in ['rareter', 'potentiel', 'class', 'qualification', 'position', 'affix']:
                chemin = os.path.join(dossier_csv, f"{table}.csv")
                if os.path.exists(chemin):
                    with open(chemin, mode='r', encoding='utf-8-sig') as f:
                        reader = csv.reader(f, delimiter=';')
                        next(reader)
                        for row in reader:
                            placeholders = ", ".join(["?"] * len(row))
                            cursor.execute(f"INSERT OR IGNORE INTO {table} VALUES ({placeholders})", row)
                    print(f"  ✔ '{table}' mis à jour.")

            chemin_ops = os.path.join(dossier_csv, "operator.csv")
            if os.path.exists(chemin_ops):
                cursor.execute("DELETE FROM operator_tags")
                cursor.execute("DELETE FROM operator")
                with open(chemin_ops, mode='r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    inseres = 0
                    for row in reader:
                        cursor.execute(
                            "INSERT INTO operator (id_operator, nom, id_rareter, id_potentiel) VALUES (?, ?, ?, ?)",
                            (int(row['id_operator']), row['nom'], row['id_rareter'], row['id_potentiel'])
                        )
                        inseres += 1
                print(f"  ✔ 'operator' : {inseres} importé(s).")

            chemin_tags = os.path.join(dossier_csv, "operator_tags.csv")
            if os.path.exists(chemin_tags):
                with open(chemin_tags, mode='r', encoding='utf-8-sig') as f:
                    lignes = list(csv.DictReader(f, delimiter=';'))
                inseres = ignores = 0
                for row in lignes:
                    id_op  = int(row['id_operator'])
                    source = row['source_table'].strip()
                    id_tag = int(row['id_tag'])
                    cursor.execute("SELECT 1 FROM operator WHERE id_operator = ?", (id_op,))
                    if not cursor.fetchone():
                        ignores += 1
                        continue
                    cursor.execute(
                        "INSERT OR IGNORE INTO operator_tags (id_operator, source_table, id_tag) VALUES (?, ?, ?)",
                        (id_op, source, id_tag)
                    )
                    inseres += 1
                print(f"  ✔ 'operator_tags' : {inseres} insérée(s), {ignores} ignorée(s).")

            conn.commit()
            print("  ✔ Import terminé !")
    except Exception as e:
        print(f"  ✘ Erreur import : {e}")


def recuperer_liste_tags():
    tags = {}
    try:
        with connexion() as conn:
            cursor = conn.cursor()
            for table in ['class', 'qualification', 'position', 'affix']:
                cursor.execute(f"SELECT nom_{table} FROM {table}")
                for row in cursor.fetchall():
                    if row[0]:
                        tags[row[0]] = table
    except:
        pass
    return tags


def afficher_operators(tag_filtre=None):
    with connexion() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.id_operator, o.nom, r.rareter
            FROM operator o
            LEFT JOIN rareter r ON o.id_rareter = r.id_rareter
            ORDER BY o.id_rareter DESC, o.nom ASC
        """)
        operateurs = cursor.fetchall()
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
        tags_rows = cursor.fetchall()

    tags_par_id = {}
    for row in tags_rows:
        tags_par_id.setdefault(row["id_operator"], set()).add(row["tag_nom"].strip())

    print(f"\n{'NOM':<22} | {'RARETÉ':<8} | TAGS")
    print("-" * 75)
    affiches = 0
    for op in operateurs:
        id_op = op["id_operator"]
        tags  = tags_par_id.get(id_op, set())
        if tag_filtre and tag_filtre not in tags:
            continue
        rarete = op["rareter"] if op["rareter"] else "?"
        t_str  = ", ".join(sorted(tags)) if tags else "Aucun tag"
        print(f"{op['nom']:<22} | {str(rarete):<8} | {t_str}")
        affiches += 1
    print(f"\n  Total : {affiches} opérateur(s)")


def mettre_a_jour_csv_potentiel(modifications, dossier_csv="donnees_csv"):
    """
    modifications : liste de tuples (id_operator, potentiel)
    Ouvre le CSV une seule fois et met à jour toutes les lignes concernées.
    """
    chemin = os.path.join(dossier_csv, "operator.csv")
    if not os.path.exists(chemin):
        print(f"  ⚠ '{chemin}' introuvable, CSV non mis à jour.")
        return

    with open(chemin, mode='r', encoding='utf-8-sig') as f:
        lignes = list(csv.DictReader(f, delimiter=';'))

    if not lignes:
        return

    fieldnames = list(lignes[0].keys())
    # Dictionnaire id_operator → ligne CSV pour accès rapide
    index = {int(r['id_operator']): r for r in lignes}

    for id_op, potentiel in modifications:
        if id_op in index:
            index[id_op]['id_potentiel'] = str(potentiel + 1)
        else:
            print(f"  ⚠ id_operator {id_op} non trouvé dans le CSV.")

    with open(chemin, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(index.values())

    print(f"  ✔ CSV mis à jour ({len(modifications)} ligne(s)).")


def modifier_potentiel():
    print("\n1: Modifier un seul operator")
    print("2: Saisir tous les potentiels")
    choix = input("> ")

    if choix == "1":
        nom = input("  Nom de l'operator : ").strip()
        with connexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_operator, nom FROM operator WHERE nom = ?", (nom,))
            op = cursor.fetchone()
        if not op:
            print(f"  ✘ Operator '{nom}' introuvable.")
            return
        while True:
            p = input(f"  Potentiel de {op[1]} (0 à 6) : ").strip()
            if p in [str(i) for i in range(7)]:
                potentiel = int(p)
                break
            print("  ✘ Entre un chiffre entre 0 et 6.")
        with connexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE operator SET id_potentiel = ? WHERE id_operator = ?",
                (potentiel + 1, op[0])
            )
            conn.commit()
        mettre_a_jour_csv_potentiel([(op[0], potentiel)])
        print(f"  ✔ Potentiel de '{op[1]}' mis à jour : {potentiel}")

    elif choix == "2":
        with connexion() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id_operator, nom FROM operator ORDER BY nom ASC")
            operateurs = cursor.fetchall()

        print(f"  {len(operateurs)} operators à renseigner (Entrée = garder 0) :")
        modifications = []

        with connexion() as conn:
            cursor = conn.cursor()
            for op in operateurs:
                while True:
                    p = input(f"  {op['nom']:<22} potentiel (0-6) : ").strip()
                    if p == "":
                        p = "0"
                    if p in [str(i) for i in range(7)]:
                        potentiel = int(p)
                        break
                    print("  ✘ Entre 0 à 6.")
                cursor.execute(
                    "UPDATE operator SET id_potentiel = ? WHERE id_operator = ?",
                    (potentiel + 1, op['id_operator'])
                )
                modifications.append((op['id_operator'], potentiel))
            conn.commit()

        print(f"  ✔ {len(modifications)} potentiels mis à jour en BDD.")
        mettre_a_jour_csv_potentiel(modifications)


def tag_manuel():
    tags_disponibles = recuperer_liste_tags()
    liste_noms = sorted(tags_disponibles.keys())

    while True:
        print("\n  Tags disponibles :")
        for t in liste_noms:
            print(f"    - {t}")

        tags_choisis = []
        print("\n  Entre jusqu'à 6 tags. 'ok' pour lancer la recherche, '0' pour quitter.")

        while len(tags_choisis) < 6:
            val = input(f"  Tag {len(tags_choisis)+1}/6 : ").strip()

            if val == "0":
                return

            if val.lower() == "ok":
                break

            match = next((t for t in liste_noms if t.lower() == val.lower()), None)
            if match is None:
                suggestions = [t for t in liste_noms if val.lower() in t.lower()]
                if suggestions:
                    print(f"  ✘ Inconnu. Vouliez-vous dire : {', '.join(suggestions)} ?")
                else:
                    print(f"  ✘ '{val}' introuvable.")
            elif match in tags_choisis:
                print(f"  ⚠ '{match}' déjà sélectionné.")
            else:
                tags_choisis.append(match)
                print(f"  ✔ '{match}' ajouté.")

        if not tags_choisis:
            print("  ✘ Aucun tag sélectionné.")
            continue

        # ── Recherche ────────────────────────────────────────────
        print(f"\n  Recherche pour : {', '.join(tags_choisis)}...")

        with connexion() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.id_operator, o.nom, r.rareter, p.potentiel
                FROM operator o
                LEFT JOIN rareter   r ON o.id_rareter   = r.id_rareter
                LEFT JOIN potentiel p ON o.id_potentiel = p.id_potentiel
            """)
            operateurs = cursor.fetchall()
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
            tags_rows = cursor.fetchall()

        tags_par_id = {}
        for row in tags_rows:
            tags_par_id.setdefault(row["id_operator"], set()).add(row["tag_nom"].strip())

        resultats = []
        for op in operateurs:
            id_op      = op["id_operator"]
            tags_op    = tags_par_id.get(id_op, set())
            tags_match = [t for t in tags_choisis if t in tags_op]

            if not tags_match:
                continue

            if op["potentiel"] is not None and int(op["potentiel"]) >= 6:
                continue

            if "Top Operator" in tags_op:
                ordre_quali = 0
            elif "Senior Operator" in tags_op:
                ordre_quali = 1
            else:
                ordre_quali = 2

            resultats.append({
                "nom":         op["nom"],
                "rarete":      op["rareter"] if op["rareter"] else "?",
                "potentiel":   op["potentiel"] if op["potentiel"] is not None else 0,
                "tags_match":  tags_match,
                "nb_match":    len(tags_match),
                "ordre_quali": ordre_quali,
            })

        resultats.sort(key=lambda x: (
            x["ordre_quali"],
            -x["nb_match"],
            -int(x["rarete"]) if str(x["rarete"]).isdigit() else 0
        ))

        # ── Affichage ─────────────────────────────────────────────
        if not resultats:
            print("\n  Aucun operator trouvé pour ces tags.")
        else:
            print(f"\n{'NOM':<22} | {'★':<6} | {'POT':<4} | TAGS CORRESPONDANTS")
            print("-" * 70)
            for r in resultats:
                etoiles = "★" * int(r["rarete"]) if str(r["rarete"]).isdigit() else r["rarete"]
                t_str   = ", ".join(sorted(r["tags_match"]))
                print(f"{r['nom']:<22} | {etoiles:<6} | {str(r['potentiel']):<4} | {t_str}")
            print(f"\n  {len(resultats)} résultat(s).")

        # ── Nouvelle recherche ou quitter ─────────────────────────
        print("\n  1: Nouvelle recherche   0: Quitter")
        if input("> ").strip() != "1":
            break

# ___________________________________________________ MAIN _____________________________________________________

while True:
    print("\n=== BIENVENUE DANS LE TRACKER ===")
    choix_jeu = input("1: Arknights\n2: Arknights Endfield\n0: Quitter\n> ")

    if choix_jeu == "0":
        break

    DB_NAME = "BDD_Arknights.db"  if choix_jeu == "1" else "BDD_Arknights_Endfield.db"
    jeu_key = "Arknights"         if choix_jeu == "1" else "Arknights_Endfield"

    while True:
        print(f"\n--- Menu [{DB_NAME}] ---")
        print("1: Initialiser les tables")
        print("2: Ajouter une donnée")
        print("3: Afficher les données")
        print("4: Modifier le potentiel des operators")
        print("5: Recherche de tags manuel")
        print("6: Recherche de tags auto")
        print("7: Retour")
        val = input("> ")

        if val == "1":
            cree_table_base(jeu_key)

        elif val == "2":
            if jeu_key == "Arknights":
                print("1: Ajouter via CSV\n2: Ajouter à la main")
                choix = input("> ")
                if choix == "1":
                    importer_csv("donnees_csv")
                elif choix == "2":
                    pass
            else:
                pass

        elif val == "3":
            if jeu_key == "Arknights":
                print("\n1: Afficher TOUT\n2: Filtrer par TAG")
                sub = input("> ")
                tag_filtre = None
                if sub == "2":
                    tags_dict  = recuperer_liste_tags()
                    liste_noms = sorted(tags_dict.keys())
                    for i, t in enumerate(liste_noms):
                        print(f"  {i}: {t}")
                    try:
                        tag_filtre = liste_noms[int(input("Numéro du tag : "))]
                    except:
                        print("Choix invalide."); continue
                afficher_operators(tag_filtre)

        elif val == "4":
            if jeu_key == "Arknights":
                modifier_potentiel()
            else:
                print("  Non disponible pour Endfield.")

        elif val == "5":
             if jeu_key == "Arknights":
                tag_manuel()
             else:
                print("  Non disponible pour Endfield.")

        elif val == "6":
            break

        elif val == "7":
            break
