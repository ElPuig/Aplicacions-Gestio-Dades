#!/usr/bin/python3.6
# -*- coding: UTF-8 -*-

"""AlumnesMPSagaExtractor_1.0.py
Fitxers d'entrada:
    - resultatConsulta.csv:
        * CSV extret de SAGA amb els camps:
            - NOM
            - MATRICULADES
            - GRUPSCLASSE
        * separador de camps: tabulador
        * el fitxer ha de portar capçalera;
Fitxers de sortida:
    - alumne-mp.csv:
        * CSV amb els camps:
              "ESTUDIANT", "CORREU", "GRUP","MP01", "MP02", "MP03", "MP04",
              "MP05", "MP06", "MP07", "MP08", "MP09", "MP10", "MP11", "MP12",
              "MP13", "MP14", "MP15"
        * Consta una «x» a cada camp d'MP dels quals l'estudiant tingui alguna
          UF matriculada
        * El camp "CORREU" està buit.

"""

import csv
import os
import re

SOURCE_FILE_SAGA = 'resultatConsulta.csv'
MP_LIST = ["MP01", "MP02", "MP03", "MP04", "MP05", "MP06", "MP07", "MP08",
           "MP09", "MP10", "MP11", "MP12", "MP13", "MP14", "MP15"]
RESULT_FILE = 'alumnes-mp.csv'


def generate_result_file():
    """def generate_whole_level_file()
    Descripció: Emplena el fitxer RESULT_FILE.
    Entrada:    Cap.
    Sortida:    Fitxer RESULT_FILE.
    """
    setup_result_file()

    with open(SOURCE_FILE_SAGA, 'r', encoding='latin-1') as saga_file:
        file_dialect = csv.Sniffer().sniff(saga_file.read(), delimiters=";,\t")
        saga_file.seek(0)
        saga_file_reader = csv.DictReader(saga_file, dialect=file_dialect)
        for saga_row in saga_file_reader:
            saga_row = suppress_number_in_dict_keys(**saga_row)
            student_info = get_student_data(**saga_row)

            with open(RESULT_FILE, 'a', encoding='utf-8') as result_file:
                result_file_writer = csv.writer(result_file)
                result_file_writer.writerow(student_info)


def get_student_data(**saga_dict):
    """def get_student_data(**saga_dict)
    Descripció: Genera un fitxer 'fitxes_' + nom_de_grup + '.csv' per cada grup
                del fitxer d'entrada.
    Entrada:    Diccionari generat per DictReader amb la informació continguda
                a una filera del fitxer d'entrada
    Sortida:    Llista amb la informació extraïda i processada.
    """
    nom = saga_dict["NOM"]
    correu = ""
    curs = get_group(saga_dict["GRUPSCLASSE"])
    enrolled_mps = get_mps_enrolled(curs, saga_dict["MATRICULADES"])

    student_info = []
    student_info.extend((nom, correu, curs))
    student_info.extend(enrolled_mps)

    return student_info


def get_group(group_info):
    """def get_group
    Descripció: Retorna el curs i lletra del grup ignorant la resta
                d'informació administrativa.
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


def get_mps_enrolled(grup, enrolled_subjects):
    """def get_ufs_enrolled(enrolled_subjects)
    Descripció: Extreu les UF matriculades per l'alumne a partir del llistat de
                codis de SAGA.
    Entrada:    String amb els codis dels MP i UF matriculades.
    Sortida:    Llistat amb una 'x' a la columna de cada MP del qual
                l'estudiant tingui alguna UF matriculada.
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
            mp = fix_saga_inconsistencies(grup, mp)
            if enrolled_dict.get(mp) == "":
                enrolled_dict[mp] = "x"

    enrolled_ufs = []
    for k, v in enrolled_dict.items():
        enrolled_ufs.append(enrolled_dict.get(k))

    return enrolled_ufs


def setup_result_file():
    """def setup_whole_level_file()
    Descripció: Genera el fitxer 'RESULT_FILE i emplena la
                capçalera.
    Entrada:    Cap.
    Sortida:    Fitxer 'fitxes_grau_complet.csv'.
    """
    with open(RESULT_FILE, 'w', encoding='utf-8') as result_file:
        result_file_writer = csv.writer(result_file, delimiter=',')
        result_file_writer.writerow(
                                   ["ALUMNE", "CORREU", "GRUP", "MP01",
                                    "MP02", "MP03", "MP04", "MP05", "MP06",
                                    "MP07", "MP08", "MP09", "MP10", "MP11",
                                    "MP12", "MP13", "MP14", "MP15"])


def fix_saga_inconsistencies(grup, mp):
    """fix_saga_inconsistencies(grup, mp)
    Descripció: Esmena les incoherències detectades entre els codis assignats a
                SAGA i els MP matriculats.
    Entrada:    3 strings amb grup, MP i UF.
    Sortida:    String "MP"-
    Exemple:    "MP16" en el cas del cicle d'AF retorna "MP05".
    """
    # Cicle d'AF
    if "AD I FIN" in grup:
        if mp == "MP16":
            mp = "MP05"

        elif mp == "MP15":
            mp = "MP02"

    if "SMX" in grup:
        if mp == "MP11":
            mp = "MP12"

        elif mp == "MP12":
            mp = "MP11"

    return mp


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
    Descripció: Comprova que si un string comença amb 2 nombres i un guió
                baix.
    Entrada:    String.
    Sortida:    True/False.
    Exemple:    "02_GRUPSCLASSE" retorna True.
                "GRUPSCLASSE" retorna False.
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
    generate_result_file()
