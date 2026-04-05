# -*- coding: utf-8 -*-
#___________________________________________importation des library_______________________________________________
import sqlite3
import mss
import pytesseract
from PIL import Image      
#___________________________________________________fonction_____________________________________________________

def connexion():
    return sqlite3.connect("BDD_armes.db")

def cree_table_arknight_endfield():
    try:
        with connexion() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stat_principal(
                    id_principal INTEGER PRIMARY KEY AUTOINCREMENT,
                    Attribut_principal TEXT NOT NULL
                )""")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stat_secondaire(
                    id_secondaire INTEGER PRIMARY KEY AUTOINCREMENT,
                    Statistique_secondaires TEXT NOT NULL
                )""")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Competences(
                    id_competences INTEGER PRIMARY KEY AUTOINCREMENT,
                    Statistique_de_competences TEXT NOT NULL
                )""")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Type_arme(
                    id_type INTEGER PRIMARY KEY AUTOINCREMENT,
                    Type_arme TEXT NOT NULL
                )""")

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
                 )""")
            conn.commit()
            print("Tables crees avec succes !")
    except Exception as e:
        print(f"Erreur pendant la creation des tables : {e}")

def insere_donnees(nom, type_arme, rarete, attribut_principal, stats_secondaires, stats_competences):
    try:
        with connexion() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")

            cursor.execute("INSERT INTO Type_arme (Type_arme) VALUES (?)", (type_arme,))
            id_type = cursor.lastrowid

            cursor.execute("INSERT INTO stat_principal (Attribut_principal) VALUES (?)", (attribut_principal,))
            id_principal = cursor.lastrowid

            cursor.execute("INSERT INTO stat_secondaire (Statistique_secondaires) VALUES (?)", (stats_secondaires,))
            id_secondaire = cursor.lastrowid

            cursor.execute("INSERT INTO Competences (Statistique_de_competences) VALUES (?)", (stats_competences,))
            id_competences = cursor.lastrowid

            cursor.execute("""
                INSERT INTO Armes (Nom_armes, Rarete, Possetion, id_type, id_principal, id_secondaire, id_competences)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (nom, rarete, None, id_type, id_principal, id_secondaire, id_competences))

            conn.commit()
            print("Arme ajoutee avec succes !")
    except Exception as e:
        print(f"Erreur pendant l'insertion : {e}")

def modifier_donnees():
    try:
        while True:
            armes = Selection_de_donnees()
            if armes:
                for items in armes:
                    print(f"ID:{items[0]} | {items[1]}")
            else:
                print("Aucune arme trouvee.")
                return

            id_arme = input("Entre l'ID de l'arme a modifier (0 pour quitter) : ")

            if id_arme == "0":
                break

            choix = input("\nQue voulez-vous modifier ?\n"
                          "1 : Nom\n"
                          "2 : Rarete\n"
                          "> ")

            colonnes = {
                "1": "Nom_armes",
                "2": "Rarete",
            }

            if choix in colonnes:
                nouvelle_valeur = input("Nouvelle valeur : ")
                with connexion() as conn:
                    cursor = conn.cursor()
                    sql = f"UPDATE Armes SET {colonnes[choix]} = ? WHERE id = ?"
                    cursor.execute(sql, (nouvelle_valeur, id_arme))
                    conn.commit()
                    print("Arme modifiee avec succes !")
            else:
                print("Choix invalide !")

    except Exception as e:
        print(f"Erreur lors de la modification : {e}")

def Selection_de_donnees():
    try:
        with connexion() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT Armes.id, Armes.Nom_armes, Type_arme.Type_arme, Armes.Rarete, 
                       stat_principal.Attribut_principal, 
                       stat_secondaire.Statistique_secondaires, 
                       Competences.Statistique_de_competences
                FROM Armes
                JOIN Type_arme       ON Armes.id_type       = Type_arme.id_type
                JOIN stat_principal  ON Armes.id_principal  = stat_principal.id_principal
                JOIN stat_secondaire ON Armes.id_secondaire = stat_secondaire.id_secondaire
                JOIN Competences     ON Armes.id_competences= Competences.id_competences
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        print(f"Erreur lors de la selection : {e}")
        return None

def exporter_en_txt():
    armes = Selection_de_donnees()
    if not armes:
        print("Aucune donnee a exporter.")
        return
    try:
        with open("liste_armes.txt", "w", encoding="utf-8") as f:
            f.write("=== CATALOGUE DES ARMES ===\n\n")
            for item in armes:
                etoiles = "*" * int(item[3])
                f.write(f"ID: {item[0]}\n")
                f.write(f"Nom: {item[1]} ({item[2]})\n")
                f.write(f"Rarete: {etoiles}\n")
                f.write(f"Attribut Principal: {item[4]}\n")
                f.write(f"Stats Secondaires: {item[5]}\n")
                f.write(f"Competences: {item[6]}\n")
                f.write("-" * 30 + "\n")
        print("Donnees exportees dans 'liste_armes.txt' !")
    except Exception as e:
        print(f"Erreur lors de l'ecriture : {e}")


#_______________________________________main____________________________________________________________
while True:
    val = input("\n________________menu_______________\n"
                "\n quitter : 0\n"
                "\n cree une table //init : 1\n"
                "\n ajouter une arme : 2\n"
                "\n modifier une valeur : 3\n"
                "\n recupere des donnees : 4\n"
                "\n exporter en fichier texte : 5\n")
    
    if val == "0":
        break
    elif val == "1":
        cree_table_arknight_endfield()
    elif val == "2":
        nom = input("Nom de l'arme : ")

        while True:
            rarete_input = input("Rarete (4, 5 ou 6 etoiles) : ")
            if rarete_input in ("4", "5", "6"):
                rarete = int(rarete_input)
                break
            else:
                print("Erreur : entre uniquement 4, 5 ou 6 !")

        type_armes = input("Type armes : ")
        attr = input("Attribut principal : ")
        sec  = input("Statistique secondaire : ")
        comp = input("Statistique de competence : ")

        insere_donnees(nom, type_armes, rarete, attr, sec, comp)
    elif val == "3":
        modifier_donnees()
    elif val == "4":
        armes = Selection_de_donnees()
        if armes:
            for items in armes:
                etoiles = "*" * int(items[3])
                print(f"ID:{items[0]} | {items[1]} | {items[2]} | {etoiles} | {items[4]} | {items[5]} | {items[6]}")
        else:
            print("Aucune arme trouvee.")
    elif val == "5":
        exporter_en_txt()