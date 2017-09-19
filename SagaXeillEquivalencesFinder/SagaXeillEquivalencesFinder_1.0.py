#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""SagaXeillEquivalencesFinder_1.0.py
Fitxers d'entrada:
    - saga.csv:
        * CSV extret de Saga amb els camps:
            - NOM
            - DATA NAIXEMENT
    - xeill.csv:
        * CSV extret de Xeill amb els camps:
            - First Name
            - Last Name
            - Email Address
Fitxers de sortida:
    finals:
        * alumnes_xeill_trobats.csv: conté els alumnes de Saga dels quals s'ha
                                     trobat un usuari Xeill ja existent
        * nous_alumnes.csv: conté els alumnes de Saga dels quals no s'ha trobat
                            cap usuari Xeill
    control:
        * control_file_1.txt: conté la comparació entre tots els alumnes de
                              Saga i Xeill i el resultat de la seva avaluació
        * control_file_1.txt: conté l'avaluació final de cada alumne de Saga
"""
import csv
import os
import re

CONTROL_FILE_1 = 'control_file_1.txt'  # Control constant
CONTROL_FILE_2 = 'control_file_2.txt'  # Control constant
FILE_FOUND_XEILL_USERS = 'alumnes_Xeill_trobats.csv'
FILE_NEW_STUDENTS = 'nous_alumnes.csv'
OPTION_CONTROL_FILES = True
OPTION_FOUND_XEILL_USERS = True
SOURCE_FILE_SAGA = 'saga.csv'
SOURCE_FILE_XEILL = 'xeill.csv'


def set_appart_registered_and_unregistered_students():
    """def set_appart_registered_and_unregistered_students()
    Descripció: Separa els alumnes sense usuari previ a Xeill dels que sí ho
                tenen.
    Entrada:    Cap.
    Sortida:    Fitxers FILE_FOUND_XEILL_USERS, FILE_NEW_STUDENTS, i
                CONTROL_FILE_1 i CONTROL_FILE_1 si està seleccionada l'opció.
    """
    global OPTION_CONTROL_FILES
    global OPTION_FOUND_XEILL_USERS

    with open(SOURCE_FILE_SAGA, 'r', encoding='latin-1') as saga:
        saga_reader = csv.DictReader(saga, delimiter=',')

        found_students = []
        for saga_row in saga_reader:
            saga_row = suppress_saga_number_in_dict_keys(**saga_row)
            saga_student = saga_row['NOM']
            max_score = 0
            list_position = 0
            xeill_info = []
            control_xeill_alias = ""  # Control var

            with open(SOURCE_FILE_XEILL, 'r', encoding='ISO 8859-1') as xeill:
                xeill_reader = csv.DictReader(xeill, delimiter=',')

                for xeill_row in xeill_reader:
                    xeill_student = (xeill_row["Last Name"] +
                                     ", " +
                                     xeill_row["First Name"])
                    score = compare_names(saga_student, xeill_student)
                    if score >= 2 and score > max_score:
                        xeill_info = [xeill_row["Last Name"]]
                        xeill_info.append(xeill_row["First Name"])
                        xeill_info.append(xeill_row["Email Address"])
                        control_xeill_alias = xeill_student
                        try:
                            found_students[list_position] = saga_row['NOM']
                        except IndexError:
                            found_students.append(saga_row['NOM'])
                        max_score = score

                    if OPTION_CONTROL_FILES:
                        with open(CONTROL_FILE_1, 'a') as control_file_1:
                            control_file_1.write(
                                                "Saga STUDENT: " +
                                                saga_student + '\n' +
                                                "XEILL STUDENT: " +
                                                xeill_student + '\n' +
                                                str(score) + '\n' + '\n')

            list_position += 1

            if max_score < 2:
                with open(FILE_NEW_STUDENTS, 'a', encoding='UTF-8')\
                 as new_students:
                    new_students_writer = csv.writer(new_students)
                    new_students_writer.writerow(
                                                 [saga_row['NOM'],
                                                  saga_row['DATA NAIXEMENT']])
                if OPTION_CONTROL_FILES:
                    with open(CONTROL_FILE_2, 'a') as control_file_2:
                        control_file_2.write(
                                           "FINAL Saga STUDENT: " +
                                           saga_student + '\n' +
                                           "NO SIMILARITIES FOUND" + '\n' +
                                           str(max_score) + '\n' + '\n')

            else:
                if OPTION_FOUND_XEILL_USERS:
                    with open(FILE_FOUND_XEILL_USERS, 'a', encoding='UTF-8')\
                       as current_users:
                        current_users_writer = csv.writer(current_users)
                        current_users_writer.writerow(
                                                      [xeill_info[0],
                                                       xeill_info[1],
                                                       saga_row['NOM'],
                                                       xeill_info[2]])
                if OPTION_CONTROL_FILES:
                    with open(CONTROL_FILE_2, 'a') as control_file_2:
                        control_file_2.write(
                                           "FINAL Saga STUDENT: " +
                                           saga_student + '\n' +
                                           "FINAL XEILL STUDENT: " +
                                           control_xeill_alias + '\n'
                                           + str(max_score) + '\n' + '\n')


def compare_names(saga_name, xeill_name):
    """def compare_names(saga_name, xeill_name)
    Descripció: Compara els noms d'un usuari de Saga i un de Xeill i els
                avalua.
    Entrada:    2 strings amb el nom complet d'un usuari de Saga i uh de Xeill.
    Sortida:    Puntuació amb nombre d'elements comuns als noms.
    """
    if check_two_surnames(saga_name) and\
       check_two_surnames(xeill_name):
        score = evaluate_surnames_consistency(saga_name, xeill_name)
    else:
        saga_name_list = generate_regex_groups_list(saga_name)
        xeill_name_list = generate_regex_groups_list(xeill_name)
        score = evaluate_names_similarity(saga_name_list, xeill_name_list)

    return score


def evaluate_names_similarity(saga_name_list, xeill_name_list):
    """def evaluate_names_similarity(saga_name_list, xeill_name_list)
    Descripció: Treu la puntuació de la comparació de tots els elements que
                componen un nom.
    Entrada:    2 llistes amb tots els elements que componen cadascun dels
                noms.
    Sortida:    Puntuació amb nombre d'elements comuns als noms.
    """
    score = 0
    for saga_name_list_portion in saga_name_list:
        if saga_name_list_portion != "":
            for xeill_name_list_portion in xeill_name_list:
                if xeill_name_list_portion != "":
                    if non_special_chars(saga_name_list_portion) and\
                         non_special_chars(xeill_name_list_portion):
                        if remove_special_chars(saga_name_list_portion) ==\
                           remove_special_chars(xeill_name_list_portion):
                            score += 1
                            saga_name_list.remove(saga_name_list_portion)
                    else:
                        if just_consonants(saga_name_list_portion) ==\
                                just_consonants(xeill_name_list_portion):
                            score += 1
                            saga_name_list.remove(saga_name_list_portion)

    return score


def generate_regex_groups_list(name):
    """def generate_regex_groups_list(name)
    Descripció: Cerca a un nom tots els elements que el componen i el retorna
                en forma de llista.
    Entrada:    String amb un nom.
    Sortida:    Llista amb tots els elements que componen un nom.
    """
    name_regex = re.compile(r'(^[a-zA-ZÀ-ÿ]+)'
                            '([a-zA-ZÀ-ÿ ]*)'
                            ', '
                            '([a-zA-ZÀ-ÿ]+)'
                            '([a-zA-ZÀ-ÿ ]*$)')

    name_groups = name_regex.search(name)

    name_list = []
    for i in range(1, 10):
        try:
            try:
                name_list.append(name_groups.group(i).strip())
            except AttributeError:
                break
        except IndexError:
            break

    return name_list


def evaluate_surnames_consistency(saga_name, xeill_name):
    """def evaluate_surnames_consistency(saga_name, xeill_name)
    Descripció: Comprova si els 2 cognoms d'un estudiant de Saga i un altre de
                Xeill coincideixen completament o només parcialment, i en el
                segon cas els descarta, evaluant també la similitud del nom. En
                el cas de què coincideixin tots 2 cognoms, però cap nom elimina
                la puntuació pel cas dels germans.
    Entrada:    2 strings amb els noms d'un estudiant de Saga i un altre de
                Xeill.
    Sortida:    Puntuació amb un 0 per alumnes amb 2 cognoms que no
                coincideixen, sumada a la que correspongui a la similitud del
                seu nom.
    """
    saga_surnames = get_surname(saga_name)
    xeill_surnames = get_surname(xeill_name)

    score = 0
    surnames_score = 0
    first_name_score = 0
    if non_special_chars(saga_surnames) and\
       non_special_chars(xeill_surnames):
        if remove_special_chars(saga_surnames) ==\
                remove_special_chars(xeill_surnames):
            surnames_score += 2
        saga_first_names_list = get_first_names_list(saga_name)
        xeill_first_names_list = get_first_names_list(xeill_name)
        first_name_score = evaluate_names_similarity(
                                          saga_first_names_list,
                                          xeill_first_names_list)

    else:
        if just_consonants(saga_surnames) ==\
                     just_consonants(xeill_surnames):
            surnames_score += 2
        saga_first_names_list = get_first_names_list(saga_name)
        xeill_first_names_list = get_first_names_list(xeill_name)
        first_name_score = evaluate_names_similarity(
                                          saga_first_names_list,
                                          xeill_first_names_list)

    if first_name_score == 0 and surnames_score == 2:
        score = 0
    else:
        score = surnames_score + first_name_score

    return score


def check_two_surnames(full_name):
    """def check_two_surnames(full_name)
    Descripció: Comprova si un nom complet conté 2 cognoms.
    Entrada:    String amb un nom complet.
    Sortida:    True/False.
    """
    if len(full_name.replace(' ,', ',').split(',')[0].split(' ')) >= 2:
        return True
    else:
        return False


def get_surname(full_name):
    """def get_surname(full_name)
    Descripció: Aïlla el/s cognom/s d'un nom complet.
    Entrada:    String amb un nom complet.
    Sortida:    String amb el/s cognoms/s.
    """
    return full_name.replace(' ,', ',').split(',')[0]


def get_first_names_list(full_name):
    """def get_first_names_list(full_name)
    Descripció: Aïlla el/s nom/s d'un nom complet i els retorna com a llista.
    Entrada:    String amb un nom complet.
    Sortida:    Llista amb el/s nom/s.
    """
    return list(full_name.split(',')[1].strip().split(' '))


def non_special_chars(name):
    """def non_special_chars(name)
    Descripció: Comprova si un string conté caràcters aliens al català o
                castellà.
    Entrada:    String amb un nom complet.
    Sortida:    True/False.
    """
    if re.search(r'^[a-zA-ZÁÉÍÓÚÀÈÒÏÜÇÑáéíóúàèòïüçñ, \s-]+$', name):
        return True
    else:
        return False


def remove_special_chars(s):
    """def remove_special_chars(s)
    Descripció: Elimina accents i dièresi, i converteix totes les lletres en
                minúscules; a més subsititueix les «ch» per «c», i les «th» per
                «t» per homogeneitzar noms escrits de diferent manera (per
                exemple, "Christian" per "Cristian" o "Judith" per "Judit").
    Entrada:    String.
    Sortida:    String.
    """
    s = s.lower()

    accented_chars_equivalences = [("à", "a"), ("á", "a"),
                                   ("è", "e"), ("é", "e"),
                                   ("í", "i"), ("ï", "i"),
                                   ("ò", "o"), ("ó", "ò"),
                                   ("ú", "u"), ("ü", "u"),
                                   ("ç", "c"), ("ñ", "n")]

    for k, v in accented_chars_equivalences:
        s = s.replace(k, v)

    s = s.replace("ch", "c")

    s = s.replace("th", "t")

    return s


def just_consonants(s):
    """def just_consonants(s)
    Descripció: Elimina totes les vocals i caràcters especials en un text, i
                converteix totes les lletres en minúscules; a més subsititueix
                les «ch» per «c», i les «th» per «t» per homogeneitzar noms
                escrits de diferent manera (per exemple, "Christian" per
                "Cristian" o "Judith" per "Judit").
    Entrada:    String.
    Sortida:    String.
    """
    special_chars_equivalences = [
               ("À", ""), ("Á", ""), ("Ã", ""), ("Â", ""), ("A", ""),
               ("Ç", ""), ("È", ""), ("É", ""), ("E", ""), ("Ì", ""),
               ("Í", ""), ("Ï", ""), ("I", ""), ("Ñ", ""), ("Ò", ""),
               ("Ó", ""), ("O", ""), ("Ú", ""), ("Ü", ""), ("Û", ""),
               ("U", ""), ("à", ""), ("á", ""), ("a", ""), ("ç", ""),
               ("è", ""), ("é", ""), ("e", ""), ("í", ""), ("ï", ""),
               ("i", ""), ("ñ", ""), ("ò", ""), ("ó", ""), ("o", ""),
               ("ú", ""), ("ü", ""), ("u", ""), ("y", ""), ("-", ""),
               ("·", ""), ("�", ""), ("º", ""), ("³", ""), ("¡", ""),
               ("±", ""), ("€", ""), ("©", ""), ("¿", ""), ("·", ""),
               ("”", ""), ("…", ""), ("  ", " "), (",", ""), ("™", ""),
               ("ª", ""), (".", ""), (" ,", ","),  ('', ''),
               ('\xa0', ''), ('\xa1', ''),
               ("\xa2", ""), ("\xa3", ""), ("\xa4", ""), ("\xa5", ""),
               ("\xa6", ""), ("\xa7", ""), ("\xa8", ""), ("\xa9", ""),
               ("\xaa", ""), ("\xab", ""), ("\xac", ""), ("\xad", ""),
               ("\xae", ""), ("\xaf", ""), ("\xb0", ""), ("\xb1", ""),
               ("\xb2", ""), ("\xb3", ""), ("\xb4", ""), ("\xb5", ""),
               ("\xb6", ""), ("\xb7", ""), ("\xb8", ""), ("\xb9", ""),
               ("\xba", ""), ("\xbb", ""), ("\xbc", ""), ("\xbd", ""),
               ("\xbe", ""), ("\xbf", ""), ("\xc0", ""), ("\xc1", ""),
               ("\xc2", ""), ("\xc3", ""), ("\xc4", ""), ("\xc5", ""),
               ("\xc6", ""), ("\xc7", ""), ("\xc8", ""), ("\xc9", ""),
               ("\xca", ""), ("\xcb", ""), ("\xcc", ""), ("\xcd", ""),
               ("\xce", ""), ("\xcf", ""), ("\xd0", ""), ("\xd1", ""),
               ("\xd2", ""), ("\xd3", ""), ("\xd4", ""), ("\xd5", ""),
               ("\xd6", ""), ("\xd7", ""), ("\xd8", ""), ("\xd9", ""),
               ("\xda", ""), ("\xdb", ""), ("\xdc", ""), ("\xdd", ""),
               ("\xde", ""), ("\xdf", ""), ("\xe0", ""), ("\xe1", ""),
               ("\xe2", ""), ("\xe3", ""), ("\xe4", ""), ("\xe5", ""),
               ("\xe6", ""), ("\xe7", ""), ("\xe8", ""), ("\xe9", ""),
               ("\xea", ""), ("\xeb", ""), ("\xec", ""), ("\xed", ""),
               ("\xee", ""), ("\xef", ""), ("\xf0", ""), ("\xf1", ""),
               ("\xf2", ""), ("\xf3", ""), ("\xf4", ""), ("\xf5", ""),
               ("\xf6", ""), ("\xf7", ""), ("\xf8", ""), ("\xf9", ""),
               ("\xfa", ""), ("\xfb", ""), ("\xfc", ""), ("\xfd", ""),
               ("\xfe", ""), ("\xff", "")]

    for k, v in special_chars_equivalences:
        s = s.replace(k, v).lower()

    s = s.replace("ch", "c")

    s = s.replace("th", "t")

    return s


def suppress_saga_number_in_dict_keys(**csv_dict):
    """def arrange_SOURCE_FILE_SAGA_fieldnames()
    Descripció: Reescriu les claus al diccionari per suprimir la numeració
                variable als camps del fitxer de Saga en cas que existeixin.
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


def setup_current_users_file():
    """def setup_current_users_file()
    Descripció: Crea el fitxer pels usuaris de Xeill detectats i escriu la
                capçalera.
    Entrada:    Cap.
    Sortida:    Fitxer de sortida.
    """
    with open(FILE_FOUND_XEILL_USERS, 'w', encoding='UTF-8') as current_users:
        current_users_writer = csv.writer(current_users)

        current_users_writer.writerow(
                                      ["XEILL LAST NAME",
                                       "XEILL FIRST NAME",
                                       "Saga NAME",
                                       "EMAIL"])


def setup_new_students_file():
    """def setup_new_students_file()
    Descripció: Crea el fitxer pels usuaris de Saga sense usuari a Xeill
                detectat, i escriu la capçalera.
    Entrada:    Cap.
    Sortida:    Fitxer de sortida.
    """
    with open(FILE_NEW_STUDENTS, 'w', encoding='UTF-8') as new_students:
        new_students_writer = csv.writer(new_students)

        new_students_writer.writerow(
                                     ["NOM",
                                      "DATA NAIXEMENT"])


def setup_control_files():
    """def setup_control_files()
    Descripció: Crea els fitxers de control.
    Entrada:    Cap.
    Sortida:    Fitxers de control.
    """
    control_file_1 = open(CONTROL_FILE_1, 'w')
    control_file_1.close()

    control_file_2 = open(CONTROL_FILE_2, 'w')
    control_file_2.close()


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


if __name__ == "__main__":
    check_source_file(SOURCE_FILE_SAGA)
    check_source_file(SOURCE_FILE_XEILL)
    if OPTION_CONTROL_FILES:
        setup_control_files()  # Control function
    if OPTION_FOUND_XEILL_USERS:
        setup_current_users_file()
    setup_new_students_file()
    set_appart_registered_and_unregistered_students()
