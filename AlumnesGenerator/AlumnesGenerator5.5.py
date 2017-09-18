#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""AlumnesGenerator5.5.py
Fitxers d'entrada:
    - alumnes.csv:
        * CSV extret de SAGA amb els camps:
            - NOM
            - DATA NAIXEMENT
        * el fitxer ha de portar capçalera;
Fitxers de sortida:
    - correu_puig.csv: CSV amb adreça Xeill, nom, cognom i contrasenya
                      provisional dels alumnes
    - usuari_moodle.csv: CSV amb usuari, contrasenya provisional, nom, cognom i
                        adreça Xeill dels alumnes
"""

import csv
import os
import re

DOMINI = '@elpuig.xeill.net'
FILE_MOODLE = 'usuari_moodle.csv'
FILE_XEILL = 'correu_puig.csv'
PASSWORD = 'Noteolvid3$'
SOURCE_FILE_SAGA = 'alumnes.csv'


def correu_puig_generator():
    """def correu_puig_generator()
    Descripció: Genera el fitxer FILE_XEILL.
    Entrada:    Cap.
    Sortida:    Fitxer FILE_XEILL.
    """
    with open(SOURCE_FILE_SAGA, 'r', encoding='latin-1') as llistat_alumnes:
        file_dialect = csv.Sniffer().sniff(llistat_alumnes.read(),
                                           delimiters=";,\t")
        llistat_alumnes.seek(0)
        alumnes_reader = csv.DictReader(llistat_alumnes, dialect=file_dialect)
        with open(FILE_XEILL, 'w', encoding='utf-8') as correu_puig:
            correu_writer = csv.writer(correu_puig, delimiter=',')

            # Encapçalats
            correu_writer.writerow(
                                   ["EMAIL",
                                    "FIRST NAME",
                                    "LAST NAME",
                                    "PASSWORD"])

            for alumnes_row in alumnes_reader:
                alumnes_row = suppress_number_in_dict_keys(**alumnes_row)
                cognoms_nom = compound_surname_processor(
                                    alumnes_row["NOM"].replace(' ,', ','))
                data_naixement = alumnes_row["DATA NAIXEMENT"]

                first_name, last_name = name_splitter(cognoms_nom)

                """Restitueix els espais als '_' generats per compound_surname_processor
                   i suprimeix la conjunció 'i' entre cognoms per generar el
                   nom d'usuari
                """
                email = generate_username(
                                          first_name,
                                          last_name,
                                          data_naixement) + DOMINI

                # Restitueix els espais als '_' generats
                # per compound_surname_processor
                correu_writer.writerow(
                                       [email,
                                        first_name.replace('_', ' '),
                                        last_name.replace('_', ' '),
                                        PASSWORD])


def moodle_user_generator():
    """def moodle_user_generator()
    Descripció: Genera el fitxer FILE_MOODLE.
    Entrada:    Cap.
    Sortida:    Fitxer FILE_MOODLE.
    """
    with open(FILE_XEILL, 'r', encoding='utf-8') as correu_puig:
        with open(FILE_MOODLE, 'w', encoding='utf-8') as usuari_moodle:
            correu_reader = csv.DictReader(correu_puig, delimiter=',')
            usuari_moodle_writer = csv.writer(usuari_moodle, delimiter=',')

            # Encapçalats
            usuari_moodle_writer.writerow(
                                          ["USERNAME",
                                           "PASSWORD",
                                           "FIRST NAME",
                                           "LAST NAME",
                                           "EMAIL"])

            for correuRow in correu_reader:
                email = correuRow["EMAIL"]
                first_name = correuRow["FIRST NAME"]
                last_name = correuRow["LAST NAME"]

                username = email.split('@')[0]

                usuari_moodle_writer.writerow(
                                              [username,
                                               PASSWORD,
                                               first_name,
                                               last_name,
                                               email])


def compound_surname_processor(surname):
    """def compound_surname_processor(surname)
    Descripció: Reemplaça els espais per '_' als cognoms amb articles
                i/o preposicions; elimina els espais als guions.
    Entrada:    String amb estructura «Cognom1 Cognom2, Nom».
    Sortida:    String amb estructura «Cognom1 Cognom2, Nom» amb la substitució
                especificada.
    Exemple:    "De la Rosa Alemany - Llopis, Maria del Carme" retorna
                "De_la_Rosa Alemany-Llopis, Maria del_Carme"
    """

    # Llistat d'articles i conjuncions de cognoms
    surname_particles = [
                         "De", "de", "Del", "del", "El", "el", "Ep", "ep", "I",
                         "i", "La", "la", "Las", "las"]
    surname_particles_index_list = []

    # Busca si l'string conté alguna/s de les partícules de la llista
    for e in surname_particles:
        # En cas afirmatiu, desa el seu index
        if re.search(r'(\s|^|$)'+e+r'(\s|^|$)', surname):
            surname_particles_index_list += [(re.search(
                                              r'(\s|^|$)'+e+r'(\s|^|$)',
                                              surname)
                                              ).end()]

    # Substitueix els espais entre partícules, conjuncions i cognoms per '_'
    for e in surname_particles_index_list:
        surname = surname[:e-1] + '_' + surname[e:]

    # Elimina els espais davant i darrer dels guions als cognoms
    surname = surname.replace(' - ', '-')

    return surname


def name_splitter(fullName):
    """def name_splitter(fullName)
    Descripció: Reemplaça els caràcters que no pertanyen al codi ASCII.
    Entrada:    String amb estructura «Cognom1 Cognom2, Nom».
                Admet 2 cognoms, un únic cognom seguit de coma, un únic cognom
                seguit d'espai i coma, i 2 noms.
    Sortida:    1r string corresponent al/s nom/s.
                2n string corresponent al/s cognom/s.
    Exemple:    "Planelles Saura, Ana Maria" retorna "Ana María",
                "Planelles Saura"
    """

    surnames = fullName.split(',')[0]
    firstSurname = fullName.split(' ')[0]  # CANVI*******

    # Alumnes amb 3 cognoms
    if surnames.count(' ') == 2 and\
       fullName[fullName.index(' ', fullName.index(' ') + 1)
                + 1] != ',':
        # Alumnes amb 2 noms
        try:
            first_name = fullName.split(' ')[3] + ' ' + fullName.split(' ')[4]
        # Alumnes amb 1 nom
        except IndexError:
            first_name = fullName.split(' ')[3]
        last_name = fullName.split(' ')[0] + ' ' +\
            fullName.split(' ')[1] + ' ' +\
            fullName.split(' ')[2][:-1]

    # Alumnes amb 2 cognoms
    elif (firstSurname[len(firstSurname) - 1] != ',') and\
         (fullName.split(' ')[1] != ','):
        # Alumnes amb 2 noms
        try:
            first_name = fullName.split(' ')[2] + ' ' + fullName.split(' ')[3]
        # Alumnes amb 1 nom
        except IndexError:
            first_name = fullName.split(' ')[2]
        last_name = fullName.split(' ')[0] + ' ' + fullName.split(' ')[1][:-1]
    else:
        # Alumnes amb un 1 cognom
        firstSurname = fullName.split(' ')[1][0] + firstSurname
        # Alumnes amb 2 noms
        try:
            first_name = fullName.split(' ')[1] + ' ' +\
                         fullName.split(' ')[2]
        # Alumnes amb 1 nom
        except IndexError:
            first_name = fullName.split(' ')[1]
        last_name = fullName.split(' ')[0][:-1]

    return first_name, last_name


def generate_username(first_name, last_name, data_naixement):
    """def generate_username(s)
    Descripció: Genera un nom d'usuari vàlid basat en el nom/s, cognom/s
                i data de naixement.
    Entrada:    1r string amb el nom/s
                2n string amb el/s cognom/s.
                3r string amb la data de naixement.
    Sortida:    String en minúscules i caràcters ASCII format per:
                - primera lletra de cada nom (ja tingui 1 o 2 noms)
                - 1r cognom complet
                - 1a lletra del 2n cognom (si en té)
                - darreres 2 xifres de l'any de naixement
    Exemple:    "Ernest Albert, Barrabes Pla, 17/9/1999" retorna
                "eabarrabesp99"
                "El Louah i Garcia, Chaimae, 9/11/2000" retorna "clouahg00"
    """
    # Suprimeix els articles, preposicions i conjuncions de nom/s i cognom/s
    surname_particles = ["De_", "de_", "Del_", "del_", "El_",
                         "el_", "Ep_", "ep_", "I_", "i_",
                         "La_", "la_", "Las_", "las_"]
    for e in surname_particles:
        first_name = re.sub(e, '', first_name)
        last_name = re.sub(e, '', last_name)

    # Alumnes amb 2 noms
    try:
        nom = first_name.split(' ')[0][0] + first_name.split(' ')[1][0]
    # Alumnes amb 1 nom
    except IndexError:
        nom = first_name.split(' ')[0][0]

    # Alumnes amb 2 cognoms
    try:
        cognoms = last_name.split(' ')[0] + last_name.split(' ')[1][0]
    # Alumnes amb 1 cognom
    except IndexError:
        cognoms = last_name.split(' ')[0]

    # Retorna caràcters ASCII en minúscula amb les 2 darreres xifres de l'any
    # de naixement afegides
    return normalize_char(nom + cognoms).lower() +\
        data_naixement[len(data_naixement) - 2:len(data_naixement)]


def normalize_char(s):
    """def normalize_char(s)
    Descripció: Reemplaça els caràcters que no pertanyen al codi ASCII.
    Entrada:    String amb caràctes no pertanyents al codi ASCII.
    Sortida:    String amb tots els caràctes pertanyents al codi ASCII.
    Exemple:    "àñ-çü,í" retorna "ancui"
    """
    letter_equivalences = [("À", "A"), ("Á", "A"), ("Ã", "A"), ("Ç", "C"),
                           ("È", "E"), ("É", "E"), ("Í", "I"), ("Ï", "I"),
                           ("L·L", "LL"), ("Ñ", "N"), ("Ò", "O"), ("Ó", "O"),
                           ("Ú", "U"), ("Ü", "U"), ("à", "a"), ("á", "a"),
                           ("ç", "c"), ("è", "e"), ("é", "e"), ("í", "i"),
                           ("ï", "i"), ("l·l", "ll"), ("ñ", "n"), ("ò", "o"),
                           ("ó", "o"), ("ú", "u"), ("ü", "u"), (",", ""),
                           ("-", ""), ("�", ""), ("º", ""), ("³", ""),
                           ("¡", ""), ("±", ""), ("€", ""), ("©", ""),
                           ("¿", ""), ("·", ""), ("”", ""), ("  ", " "),
                           ("™", ""), ("ª", ""), (".", "")]

    for k, v in letter_equivalences:
        s = s.replace(k, v)

    return s


def suppress_number_in_dict_keys(**csv_dict):
    """def arrange_SOURCE_FILE_SAGA_fieldnames()
    Descripció: Reescriu les claus al diccionari per suprimir la numeració
                variable als camps del fitxer de SAGA en cas que existeixin.
    Entrada:    Diccionari amb les claus numerades segons ordre en què van ser
                ser afegides al fitxer original.
    Sortida:    Diccionari amb els noms sense numeració.
    Exemple:    La clau "07_DOC. IDENTITAT" retorna la clau "DOC. IDENTITAT".
    """
    for k, v in csv_dict.copy().items():
        if find_saga_numeration_in_field_name(k):
            csv_dict[k[3:]] = csv_dict.pop(k)

    return csv_dict


def find_saga_numeration_in_field_name(s):
    """def find_saga_numeration_in_field_name(s)
    Descripció: Comprova que si a un string comença amb 2 nombres i un guió
                baix.
    Entrada:    String.
    Sortida:    True/False.
    Exemple:    "07_DOC. IDENTITAT" retorna True.
                "DOC. IDENTITAT" retorna False.
    """
    if re.search(r'^\d\d_', s):
        return True
    else:
        return False


def offer_navigation_menu_for_troublesome_source_files(source_file):
    """def offer_navigation_menu_for_troublesome_source_files(source_file)
    Descripció: Ofereix a l'usuari l'opció de solucionar un problema amb els
                fitxers d'entrada i continuar amb l'execució del programa, o bé
                interrompre'l.
    Entrada:    String amb el nom del fitxer d'entrada.
    Sortida:    Executa una determinada funció segons l'opció triada.
    """
    option = input("\nQuè voleu fer?:"
                   "\n\t1. Solucionar el problema i seguir "
                   "executant el programa"
                   "\n\t2. Voleu sortir del programa"
                   "\nTrieu una opció (1/2): ")

    if option == "1":
        input("\nSi us plau, assegureu-vos de què heu "
              "solucionat el problema i premeu «Enter».")
        check_source_file(source_file)
    elif option == "2":
        exit()
    else:
        print("\nATENCIÓ: Si us plau, trieu «1» o «2».")
        offer_navigation_menu_for_troublesome_source_files(source_file)


def check_source_file(source_file):
    """def check_source_file(source_file)
    Descripció: Comprova que el fitxer d'entrada existeix i no està buit.
    Entrada:    String amb el nom del fitxer d'entrada.
    Sortida:    Cap o crida a la funció
                offer_navigation_menu_for_troublesome_source_files(source_file).
    """
    if not os.path.exists(source_file):
        print("\nNo s'ha trobat a la carpeta el fitxer «%s»." % source_file)
        offer_navigation_menu_for_troublesome_source_files(source_file)

    if os.path.getsize(source_file) == 0:
        print("\nEl fitxer «%s» està buit." % source_file)
        offer_navigation_menu_for_troublesome_source_files(source_file)


if __name__ == '__main__':
    check_source_file(SOURCE_FILE_SAGA)
    correu_puig_generator()
    moodle_user_generator()
