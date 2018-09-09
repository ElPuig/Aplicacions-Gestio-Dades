#!/usr/bin/python3.6
# -*- coding: UTF-8 -*-

import csv
import os
import re

# PENDENT:
# any últim nivell aprovat
# email alumne
# GM: Test (responsables?, telèfon responsable?, correu responsable?)

"""FitxesGeneratorGM_1.4.py
Fitxers d'entrada:
    - alumnes.csv:
        * CSV extret de SAGA amb els camps:
            - NOM
            - DOC. IDENTITAT
            - DATA NAIXEMENT
            - GRUPSCLASSE
            - NACIONALITAT
            - ADREÇA
            - LOCALITAT
            - CP
            - CORREU ELECTRÒNIC
            - RESPONSABLE 1
            - PARENTIU RESP. 1
            - TELÈFON RESP. 1
            - RESPONSABLE 2
            - PARENTIU RESP. 2
            - TELÈFON RESP. 2
            - ALTRES TELÈFONS
            - MATRICULADES
            - CONVALIDACIONS
            - EXEMPCIONS
            - PROCEDÈNCIA ACADÈMICA
            - TREBALLA
        * separador de camps: tabulador
        * el fitxer ha de portar capçalera;
Fitxers de sortida:
    - fitxes_grau_complet.csv:
        * CSV amb els camps:
            "CURS", "COGNOMS", "NOM", "DATA NAIXEMENT", "NOMBRE ID",
            "TIPUS ID", "NACIONALITAT", "EMAIL", "TELÈFON", "RESPONSABLES",
            "ADREÇA", "POBLACIÓ", "CP", "MODE D'ACCÉS", "TREBALLA",
            "CONVALIDACIONS", "EXEMPCIONS", "MP01", "MP02", "MP03", "MP04",
            "MP05", "MP06", "MP07", "MP08", "MP09", "MP10", "MP11", "MP12",
            "MP13", "MP14", "MP15", "MP16"
    - "fitxes_" + nom_de_grup.csv:
        * Genera un fitxer CSV per cadascun dels grups inclosos al fitxer
          d'entrada.
        * Inclou els següents camps:
            "COGNOMS", "NOM", "DATA NAIXEMENT", "NOMBRE ID", "TIPUS ID",
            "NACIONALITAT", "EMAIL", "TELÈFON", "RESPONSABLES", "ADREÇA",
            "POBLACIÓ", "CP", "MODE D'ACCÉS", "TREBALLA", EXEMPCIONS",
            "CONVALIDACIONS", "EXEMPCIONS", "MP01", "MP02", "MP03", "MP04",
            "MP05", "MP06", "MP07", "MP08", "MP09", "MP10", "MP11", "MP12",
            "MP13", "MP14", "MP15", "MP16"
"""

SOURCE_FILE_SAGA = 'alumnesGM.csv'
MP_LIST = ["MP01", "MP02", "MP03", "MP04", "MP05", "MP06", "MP07", "MP08",
           "MP09", "MP10", "MP11", "MP12", "MP13", "MP14", "MP15", "MP16"]
WHOLE_LEVEL_FILE = 'Fitxes_GM.csv'


def generate_whole_level_file():
    """def generate_whole_level_file()
    Descripció: Emplena el fitxer 'fitxes_grau_complet.csv'.
    Entrada:    Cap.
    Sortida:    Fitxer 'fitxes_grau_complet.csv'.
    """
    setup_whole_level_file()

    with open(SOURCE_FILE_SAGA, 'r', encoding='latin-1') as saga_file:
        file_dialect = csv.Sniffer().sniff(saga_file.read(), delimiters=";,\t")
        saga_file.seek(0)
        saga_file_reader = csv.DictReader(saga_file, dialect=file_dialect)
        for saga_row in saga_file_reader:
            saga_row = suppress_number_in_dict_keys(**saga_row)
            student_info = get_student_data(**saga_row)

            with open(WHOLE_LEVEL_FILE, 'a', encoding='utf-8') as result_file:
                result_file_writer = csv.writer(result_file)
                result_file_writer.writerow(student_info)


def generate_groups_files():
    """def generate_groups_files()
    Descripció: Emplena un fitxer 'fitxes_' + nom_de_grup + '.csv' per cada
                grup del fitxer d'entrada.
    Entrada:    Cap.
    Sortida:    Cap.
    """
    groups_list = get_groups_list()

    for group in groups_list:
        group_file = setup_group_file(group)

        with open(WHOLE_LEVEL_FILE, 'r', encoding='utf-8')\
                as all_groups_file:
            all_groups_file_reader = csv.reader(all_groups_file)

            for all_groups_row in all_groups_file_reader:
                all_groups_group = all_groups_row[0]

                if all_groups_group == group:
                    student_info = []
                    student_info = all_groups_row[1:]  # Exclude group name

                    with open(group_file, 'a', encoding='utf-8')\
                            as one_group_file:
                        one_group_file_writer = csv.writer(one_group_file)
                        one_group_file_writer.writerow(student_info)


def get_student_data(**saga_dict):
    """def get_student_data(**saga_dict)
    Descripció: Genera un fitxer 'fitxes_' + nom_de_grup + '.csv' per cada grup
                del fitxer d'entrada.
    Entrada:    Diccionari generat per DictReader amb la informació continguda
                a una filera del fitxer d'entrada
    Sortida:    Llista amb la informació extraïda i processada.
    """
    grup = get_group(saga_dict["GRUPSCLASSE"])
    cognoms = get_surnames(saga_dict["NOM"])
    nom = get_name(saga_dict["NOM"])
    data_naixement = saga_dict["DATA NAIXEMENT"]
    nombre_id = get_id_number(saga_dict["DOC. IDENTITAT"])
    tipus_id = get_id_card_type(saga_dict["DOC. IDENTITAT"])
    nacionalitat = get_nationality(saga_dict["NACIONALITAT"])
    telefon = remove_phone_prefixes(saga_dict["ALTRES TELÈFONS"])
    email = saga_dict["CORREU ELECTRÒNIC"]
    in_charge = get_person_in_charge(saga_dict["RESPONSABLE 1"],
                                     saga_dict["PARENTIU RESP. 1"],
                                     saga_dict["TELÈFON RESP. 1"],
                                     saga_dict["RESPONSABLE 2"],
                                     saga_dict["PARENTIU RESP. 2"],
                                     saga_dict["TELÈFON RESP. 2"])
    adreca = get_address(saga_dict["ADREÇA"])
    poblacio = saga_dict["LOCALITAT"]
    cp = format_zip_code(saga_dict["CP"])
    mode_acces = saga_dict["PROCEDÈNCIA ACADÈMICA"]
    treballa = saga_dict["TREBALLA"]
    convalidacions = saga_dict["CONVALIDACIONS"]
    exempcions = saga_dict["EXEMPCIONS"]
    enrolled_ufs = get_ufs_enrolled(grup, saga_dict["MATRICULADES"])

    student_info = []
    student_info.extend(
        (grup, cognoms, nom, data_naixement, nombre_id, tipus_id,
         nacionalitat, email, telefon, in_charge, adreca, poblacio, cp,
         mode_acces, treballa, convalidacions, exempcions))
    student_info.extend(enrolled_ufs)

    return student_info


def suppress_number_in_dict_keys(**csv_dict):
    """def arrange_saga_file_fieldnames()
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


def get_group(group_info):
    """def get_group
    Descripció: Retorna el nom del grup ignorant la resta d'informació
                administrativa.
    Entrada:    String amb el nom del curs/grup i informació del pla d'estudis.
    Sortida:    String amb el nom del curs/grup.
    Exemple:    "SMX (IC10) 1C TARDA" retorna "SMX 1C TARDA".
    """
    try:
        group_info = (group_info.split('(')[0] + group_info.split(')')[1])
    except IndexError:
        pass

    group_info = ' '.join(group_info.split()).strip()

    return group_info


def get_name(full_name):
    """def get_name(full_name)
    Descripció: Retorna el/s nom/s.
    Entrada:    String amb el/s cognom/s i nom/s.
    Sortida:    String amb el nom/s.
    Exemple:    "Jordán Cedillo, Mayte Alejandra" retorna "Mayte Alejandra".
    """
    try:
        return full_name.split(',')[1].strip()
    except IndexError:
        return "SENSE INFORMACIÓ"


def get_surnames(full_name):
    """def get_surnames(full_name)
    Descripció: Retorna el/s cognom/s
    Entrada:    String amb el/s cognom/s i nom/ss.
    Sortida:    String amb el cognom/s.
    Exemple:    "Jordán Cedillo, Mayte Alejandra" retorna "Jordán Cedillo".
    """
    if re.search('[a-zA-Z0-9]', full_name):
        return full_name.split(',')[0].strip()
    else:
        return "SENSE INFORMACIÓ"


def get_id_number(id_document):
    """def get_id_number(id_document)
    Descripció: Retorna el nombre del document oficial d'identificació.
    Entrada:    String amb el tipus de document i el seu nombre.
    Sortida:    String amb el nombre del document.
    Exemple:    "Passaport: C189172" retorna "C189172".
    """
    try:
        return id_document.split(':')[1].strip()
    except IndexError:
        return "SENSE INFORMACIÓ"


def get_id_card_type(id_document):
    """def get_id_card_type(id_document)
    Descripció: Retorna el tipus de document oficial d'identificació.
    Entrada:    String amb el tipus de document i el seu nombre.
    Sortida:    String amb el tipus de document.
    Exemple:    "Passaport: C189172" retorna "Passaport".
    """
    if re.search('[a-zA-Z0-9]', id_document):
        return id_document.split(':')[0].strip()
    else:
        return "SENSE INFORMACIÓ"


def get_nationality(country):
    """def get_nationality(country)
    Descripció: Retorna el país de nacionalitat amb la primera lletra en
                majúscula i la resta en minúscula.
    Entrada:    String amb el país de nacionalitat (habitualment tot en
                majúscules).
    Sortida:    String amb el país de nacionalitat amb el format esmenat.
    Exemple:    "COLOMBIA" retorna "Colombia".
    """
    return country.title()


def remove_phone_prefixes(phones_string):
    """def remove_phone_prefixes(phones_string)
    Descripció: Retorna els llistats de telèfons sense el prefixe.
    Entrada:    String amb telèfon/s amb prefix en cas dels fixos
                i informació del/s titular.
    Sortida:    String amb un o múltiples telèfons i informació del titular.
    Exemple:    "933866109 (fix), +34-+34-+34-+34-933866109 (alumne),
                +34-631593343 (alumne)" retorna "933866109 (fix), 933866109
                (alumne), 631593343 (alumne)"
    """
    return re.sub(r'([+34-]*)''([0-9a-zAa-zA-ZÀ-ÿ ,()]*)',
                  r'\2',
                  phones_string)


def get_address(address):
    """def get_address(address)
    Descripció: Retorna l'adreça sense espais de sobra.
    Entrada:    String amb l'adreça.
    Sortida:    String amb l'adreça amb el format esmenat.
    Exemple:    "CR  Pirineus  6     " retorna "CR Pirineus 6".
    """
    return ' '.join(address.split())


def format_zip_code(zip_code):
    """def format_zip_code(zip_code)
    Descripció: Retorna el CP amb 5 dígits amb independència de què el primer
                sigui un "0".
    Entrada:    String amb el CP.
    Sortida:    String amb el CP en 5 dígits.
    Exemple:    "8012" retorna "08012".
    """
    return zip_code.zfill(5)


def get_person_in_charge(
                         person1,
                         relationship1,
                         phone1,
                         person2,
                         relationship2,
                         phone2):
    """def get_person_in_charge(person1, relationship1, phone1,
                                person2, relationship2, phone2)
    Descripció: Retorna el llistat de responsables, el parentiu i el telèfon.
    Entrada:    6 strings.
    Sortida:    String única amb format.
    Exemple:    "CR  Pirineus  6     " retorna "CR Pirineus 6".
    """
    person_in_charge1 = ""
    if person1 != "":
        person_in_charge1 += "Nom: " + person1.title().replace(" ,", ",")
    if relationship1 != "" and relationship1 != "":
        person_in_charge1 += "; parentiu: " + relationship1.lower()
    elif relationship1 != "":
        person_in_charge1 = relationship1.lower()
    if phone1 != "" and relationship1 != "":
        person_in_charge1 += "; " + phone1
    elif phone1 != "":
        person_in_charge1 += phone1

    if person_in_charge1 != "":
        person_in_charge1.partition(" ")[0].title() +\
         person_in_charge1.partition(" ")[2]

    person_in_charge2 = ""
    if person2 != "":
        person_in_charge2 += "Nom: " + person2.title().replace(" ,", ",")
    if relationship2 != "" and relationship2 != "":
        person_in_charge2 += "; parentiu: " + relationship2.lower()
    elif relationship2 != "":
        person_in_charge2 = relationship2.lower()
    if phone2 != "" and relationship2 != "":
        person_in_charge2 += "; " + phone2
    elif phone2 != "":
        person_in_charge2 += phone2

    if person_in_charge2 != "":
        person_in_charge2.partition(" ")[0].title() +\
         person_in_charge2.partition(" ")[2]

    in_charge = ""
    if person_in_charge1 != "":
        in_charge = ' '.join(person_in_charge1.strip().split()) + "."
    if person_in_charge2 != "" and in_charge != "":
        in_charge += " " + ' '.join(person_in_charge2.strip().split()) + "."
    elif person_in_charge2 != "":
        in_charge = ' '.join(person_in_charge2.strip().split())

    return in_charge


def get_ufs_enrolled(grup, enrolled_subjects):
    """def get_ufs_enrolled(enrolled_subjects)
    Descripció: Extreu les UF matriculades per l'alumne a partir del llistat de
                codis de SAGA.
    Entrada:    String amb els codis dels MP i UF matriculades.
    Sortida:    Llistat amb les UF matriculades a cada MP.
    """
    enrolled_dict = {
                     "MP01": "", "MP02": "", "MP03": "", "MP04": "",
                     "MP05": "", "MP06": "", "MP07": "", "MP08": "",
                     "MP09": "", "MP10": "", "MP11": "", "MP12": "",
                     "MP13": "", "MP14": "", "MP15": "", "MP16": ""}

    for elem in enrolled_subjects.split(','):
        if len(elem) < 5:
            pass
        else:
            mp = "MP" + elem[0:3].lstrip('0').zfill(2)
            uf = "UF" + elem[3:].lstrip('0')

            mp, uf = fix_saga_inconsistencies(grup, mp, uf)

            if enrolled_dict.get(mp) != "":
                enrolled_dict[mp] = enrolled_dict.get(mp) + ", " + uf
            else:
                enrolled_dict[mp] = uf

    enrolled_ufs = []
    for k, v in enrolled_dict.items():
        enrolled_ufs.append(enrolled_dict.get(k))

    return enrolled_ufs


def fix_saga_inconsistencies(grup, mp, uf):
    """fix_saga_inconsistencies(grup, mp, uf)
    Descripció: Esmena les incoherències detectades entre els codis assignats a
                SAGA i els MP i UF realment matriculats.
    Entrada:    3 strings amb grup, MP i UF.
    Sortida:    String "MP" i string "UF".
    Exemple:    "MP16" en el cas del cicle d'AF retorna "MP05".
                "UF4" en el cas del MP01 de GA retorna "UF3".
    """
    # Cicle de GA
    if "GEST" in grup:
        if mp == "MP07":
            if uf == "UF8":
                uf = "UF3"

    return mp, uf


def setup_whole_level_file():
    """def setup_whole_level_file()
    Descripció: Genera el fitxer 'fitxes_grau_complet.csv' i emplena la
                capçalera.
    Entrada:    Cap.
    Sortida:    Fitxer 'fitxes_grau_complet.csv'.
    """
    with open(WHOLE_LEVEL_FILE, 'w', encoding='utf-8') as result_file:
        result_file_writer = csv.writer(result_file, delimiter=',')
        result_file_writer.writerow(
                                   ["GRUP", "COGNOMS", "NOM", "DATA NAIXEMENT",
                                    "NOMBRE ID", "TIPUS ID", "NACIONALITAT",
                                    "EMAIL", "TELÈFON", "RESPONSABLE",
                                    "ADREÇA", "POBLACIÓ", "CP", "MODE D'ACCÉS",
                                    "TREBALLA", "CONVALIDACIONS", "EXEMPCIONS",
                                    "MP01", "MP02", "MP03", "MP04", "MP05",
                                    "MP06", "MP07", "MP08", "MP09", "MP10",
                                    "MP11", "MP12", "MP13", "MP14", "MP15",
                                    "MP16"])


def setup_group_file(group):
    """def setup_group_file()
    Descripció: Genera el fitxer fitxes_' + nom_de_grup + '.csv' i emplena la
                capçalera.
    Entrada:    Cap.
    Sortida:    Fitxer 'fitxes_' + nom_de_grup + '.csv'.
    """
    file_name = 'Fitxes-' + group.replace(' ', '_') + '.csv'

    with open(file_name, 'w', encoding='utf-8') as result_file:
        result_file_writer = csv.writer(result_file, delimiter=',')
        result_file_writer.writerow(
                                   ["COGNOMS", "NOM", "DATA NAIXEMENT",
                                    "NOMBRE ID", "TIPUS ID", "NACIONALITAT",
                                    "EMAIL", "TELÈFON", "RESPONSABLE",
                                    "ADREÇA", "POBLACIÓ", "CP", "MODE D'ACCÉS",
                                    "TREBALLA", "CONVALIDACIONS", "EXEMPCIONS",
                                    "MP01", "MP02", "MP03", "MP04", "MP05",
                                    "MP06", "MP07", "MP08", "MP09", "MP10",
                                    "MP11", "MP12", "MP13", "MP14", "MP15",
                                    "MP16"])

    return file_name


def get_groups_list():
    """def get_ufs_enrolled(enrolled_subjects)
    Descripció: Extreu el llistat de cursos/grups diferents que apareixen al
                fitxer d'entrada.
    Entrada:    Cap.
    Sortida:    Llistat amb els cursos/grups.
    """
    groups_list = []

    with open(WHOLE_LEVEL_FILE, 'r', encoding='utf-8') as all_groups_file:
        all_groups_file_reader = csv.DictReader(all_groups_file)
        for row in all_groups_file_reader:
            if row["GRUP"] not in groups_list:
                groups_list.append(row["GRUP"])

    return groups_list


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
    generate_whole_level_file()
    generate_groups_files()
