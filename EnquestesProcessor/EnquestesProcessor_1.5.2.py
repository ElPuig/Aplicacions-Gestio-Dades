#!/usr/bin/python3.6
# -*- coding: UTF-8 -*-

"""EnquestesProcessor_1.5.2:
Fitxers d'entrada:
    - alumnes-mp.csv: llista dels alumnes matriculats a cada CF,
                      amb el seu nom complet, l'adreça Xeill, el cicle i curs,
                      i una «x» per cada MP al qual estigui matriculat
    - respostes.csv: descarregat des del formulari d'avaluació de Google Drive,
                     conté les valoracions dels alumnes
Fitxers de sortida:
    - finals:
        * resultats_respostes.csv: conté les respostes per ser traspassades al
                                   full de càlcul final
        * resultats_errades.csv: conté les respostes filtrades
        * resultats_alumnes-respostes.csv: conté quins objectes han estat
                                           avaluats per cada alumne
    - registres (opcionalment eliminables):
        * errades_rec.csv: conté les errades filtrades amb l'avaluació completa
                          feta per l'estudiant
        * resultats_rec.csv: conté les respostes filtrades amb l'avaluació
                            completa feta per l'estudiant
    - temporals (opcionalment eliminables):
        * resultats_tmp.csv: conté les respostes vàlides amb la identificació
                            de l'estudiant

Principals canvis d'aquesta nova versió (respecte a v1.5.1):
    - corregeix un bug que permetia avaluacions d'alumnes no matricualts d'un
      MP
    - al fitxer FILE_ERRORS_RECORD s'afegeix el nom de l'MP en cas que l'alumne
      avaluï un MP del qual no està matriculat
"""

import csv
import os
from dateutil import parser

FILE_ANSWERS = 'resultats_respostes.csv'
FILE_ERRORS = 'resultats_errades.csv'
FILE_STUDENTS_WITH_AVALUATED_MP = 'resultats_alumnes-respostes.csv'
FILE_ERRORS_RECORD = 'errades_rec.csv'
FILE_ANSWERS_RECORD = 'resultats_rec.csv'
FILE_ANSWERS_TMP = 'resultats_tmp.csv'
# tmp -> 0 = elimina
#        1 = conserva
#        2 = consulta a usuari
OPTION_TMP_FILES = 0
OPTION_TMP_RECORDS = 0
# duplicates -> 0 = conserva antiga
#               1 = conserva nova
#               2 = consulta a usuari
OPTION_DUPLICATE_FILES = 1
# reports -> 0 = no
#            1 = sí
#            2 = consulta a usuari
OPTION_REPORTS = 1
REPORT_FILE_ADM = 'informe_Dept_Admin.csv'
REPORT_FILE_INF = 'informe_Dept_Inform.csv'
REPORT_FILE_CENTRE = 'informe_Centre.csv'
SOURCE_FILE_STUDENTS_WITH_MP = 'alumnes-mp.csv'
SOURCE_FILE_STUDENT_ANSWERS = 'respostes.csv'


def filter_responses():
    """def filter_responses()
    Descripció: Filtra les respostes d'alumnes que no estiguin matriculats al
                cicle o al MP avaluat, o que no pertanyin al curs de la tutoria
                avaluada.
    Entrada:    Cap.
    Sortida:    Fitxer resultats_tmp.csv
                Fitxer errades_rec.csv
    """
    resultats_tmp = open(FILE_ANSWERS_TMP, 'w', encoding='utf-8')
    resultats_tmp_writer = csv.writer(resultats_tmp)

    # Encapçalats
    resultats_tmp_writer.writerow(
                                ['ALUMNE', 'TIMESTAMP', 'EMAIL', 'CURS',
                                 'OBJECTE', 'MP-ÍTEM1', 'MP-ÍTEM2', 'MP-ÍTEM3',
                                 'MP-ÍTEM4', 'MP-COMENTARI', 'TUTORIA1-ÍTEM1',
                                 'TUTORIA1-ÍTEM2', 'TUTORIA1-ÍTEM3',
                                 'TUTORIA1-COMENTARI', 'TUTORIA2-ÍTEM1',
                                 'TUTORIA2-ÍTEM2', 'TUTORIA2-ÍTEM3',
                                 'TUTORIA2-ÍTEM4', 'TUTORIA2-COMENTARI',
                                 'CENTRE-ÍTEM1', 'CENTRE-ÍTEM2',
                                 'CENTRE-ÍTEM3', 'CENTRE-ÍTEM4',
                                 'CENTRE-ÍTEM5', 'CENTRE-ÍTEM6',
                                 'CENTRE-COMENTARI'])
    errades_rec = open(FILE_ERRORS_RECORD, 'w', encoding='utf-8')
    errades_rec_writer = csv.writer(errades_rec)

    # Encapçalats
    errades_rec_writer.writerow(
                              ['ALUMNE', 'CURS', 'MOTIU', 'TIMESTAMP', 'EMAIL',
                               'CURS AVALUAT', 'OBJECTE', 'MP-ÍTEM1',
                               'MP-ÍTEM2', 'MP-ÍTEM3', 'MP-ÍTEM4',
                               'MP-COMENTARI', 'TUTORIA1-ÍTEM1',
                               'TUTORIA1-ÍTEM2', 'TUTORIA1-ÍTEM3',
                               'TUTORIA1-COMENTARI', 'TUTORIA2-ÍTEM1',
                               'TUTORIA2-ÍTEM2', 'TUTORIA2-ÍTEM3',
                               'TUTORIA2-ÍTEM4', 'TUTORIA2-COMENTARI',
                               'CENTRE-ÍTEM1', 'CENTRE-ÍTEM2', 'CENTRE-ÍTEM3',
                               'CENTRE-ÍTEM4', 'CENTRE-ÍTEM5', 'CENTRE-ÍTEM6',
                               'CENTRE-COMENTARI'])

    with open(SOURCE_FILE_STUDENT_ANSWERS, 'r', encoding='utf-8') as respostes:
        respostes_reader = csv.reader(respostes)
        next(respostes, None)

        for respostes_row in respostes_reader:
            r_email = respostes_row[1]
            r_curs = respostes_row[2]
            mp_index = extract_resposta_mp_index(*respostes_row[3:8])
            r_objecte = extract_mp_number(respostes_row[3:8][mp_index])
            arranged_respostes_row = []
            arranged_respostes_row.extend(respostes_row[:3] +
                                          [respostes_row[3:8][mp_index]] +
                                          respostes_row[8:])
            email_found = False

            with open(SOURCE_FILE_STUDENTS_WITH_MP, 'r', encoding='utf-8')\
                    as alumnes:
                alumnes_reader = csv.DictReader(alumnes)
                for alumnes_row in alumnes_reader:
                    error_found = False
                    # Busca email de l'alumne que avalua
                    if r_email == alumnes_row['CORREU']:
                        arranged_respostes_row = retrieve_groupclass(
                                                       alumnes_row['GRUP'],
                                                       *arranged_respostes_row)
                        email_found = True
                        # Comprova que l'alumne pertany al cicle que avalua
                        # Comparació sense tenir en compte el grup del curs
                        # (ex. 'B' a 'DAM1B')
                        if r_curs not in alumnes_row['GRUP']:
                            errades_rec_writer.writerow(
                                                    [alumnes_row['ALUMNE']] +
                                                    [alumnes_row['GRUP']] +
                                                    ['CICLE INCORRECTE'] +
                                                    arranged_respostes_row)
                            error_found = True

                        else:
                            # Comprova que l'alumne cursa l'MP avaluat
                            if r_objecte in alumnes_row and\
                               alumnes_row[r_objecte].lower() != 'x':
                                errades_rec_writer.writerow(
                                                    [alumnes_row['ALUMNE']] +
                                                    [alumnes_row['GRUP']] +
                                                    ['MP INCORRECTE: ' +
                                                     r_objecte] +
                                                    arranged_respostes_row)
                                error_found = True

                            # Comprova que l'alumne pertany al curs
                            # de la tutoria avaluada
                            elif r_objecte == 'Tutoria 1r curs' and\
                                    '1' not in alumnes_row['GRUP']:
                                errades_rec_writer.writerow(
                                                    [alumnes_row['ALUMNE']] +
                                                    [alumnes_row['GRUP']] +
                                                    ['TUTORIA INCORRECTA'] +
                                                    arranged_respostes_row)
                                error_found = True

                            elif r_objecte == 'Tutoria 2n curs' and\
                                    '2' not in alumnes_row['GRUP']:
                                errades_rec_writer.writerow(
                                                    [alumnes_row['ALUMNE']] +
                                                    [alumnes_row['GRUP']] +
                                                    ['TUTORIA INCORRECTA'] +
                                                    arranged_respostes_row)
                                error_found = True

                        # Enregistra respostes que passin els filtres
                        if error_found is False:
                            resultats_tmp_writer.writerow(
                                                    [alumnes_row['ALUMNE']] +
                                                    arranged_respostes_row)

                # Enregistra com a errors els emails no trobats
                if email_found is False:
                    errades_rec_writer.writerow(
                                     ['desconegut'] +
                                     ['desconegut'] +
                                     ['EMAIL INEXISTENT'] +
                                     arranged_respostes_row)

    errades_rec.close()
    resultats_tmp.close()


def extract_resposta_mp_index(*mp_respostes_info):
    """extract_resposta_mp_index(*mp_respostes)
    Descripció: Troba l'índex amb informació sobre l'MP avaluat, el qual varia
                depenent del cicle de l'estudiant.
    Entrada:    [foo, foo, "MP10 - Gestió logística i comercial", foo, foo].
    Sortida:    "2".
    """
    return next(i for i, j in enumerate(mp_respostes_info) if j != "")


def extract_mp_number(full_mp_name):
    """extract_mp_number(full_mp_name)
    Descripció: Extreu el nombre de l'MP i descarta el seu nom; en cas que
                l'objecte avaluat sigui el centre o la tutoria retorna
                l'objecte sense canvis.
    Entrada:    "MP10 - Gestió logística i comercial".
    Sortida:    "MP10".
    """
    if full_mp_name[:2] == "MP":
        return full_mp_name[:4]
    else:
        return full_mp_name


def retrieve_groupclass(groupclass, *arranged_respostes_row):
    """retrieve_groupclass(group, *arranged_respostes_row)
    Descripció: Substitueix la informació del cicle pel curs i classe
                específic al llistat que conté la informació de cada resposta
                d'estudiant.
    Entrada:    "ASIX2C", [foo, foo, "ASIX", foo, ... ].
    Sortida:    [foo, foo, "ASIX2C", foo, ... ].
    """
    arranged_respostes_row_with_classgroup = []
    arranged_respostes_row_with_classgroup = (
                                             list(arranged_respostes_row[:2]) +
                                             [groupclass] +
                                             list(arranged_respostes_row[3:]))
    return arranged_respostes_row_with_classgroup


def filter_duplicates():
    """def filter_duplicates()
    Descripció: Filtra les respostes duplicades.
    Entrada:    Cap.
    Sortida:    Cap.
    """
    global OPTION_DUPLICATE_FILES

    respostes_dict = {}
    errades_dict = {}

    with open(FILE_ANSWERS_TMP, 'r', encoding='utf-8') as respostes:
        respostes_reader = csv.reader(respostes)
        next(respostes_reader, None)

        for respostes_row in respostes_reader:
            r_email_curs_objecte = respostes_row[2] +\
                                respostes_row[3] +\
                                respostes_row[4]
            r_time = parser.parse(respostes_row[1])

            resposta_anterior = respostes_dict.get(r_email_curs_objecte)

            if resposta_anterior is None:
                respostes_dict[r_email_curs_objecte] = {}
                respostes_dict[r_email_curs_objecte]['time'] = r_time
                respostes_dict[r_email_curs_objecte]['resposta'] =\
                    respostes_row

            else:
                if OPTION_DUPLICATE_FILES == 0:  # Conserva primera resposta
                    if (r_time > resposta_anterior['time']):
                        errades_dict[r_email_curs_objecte] = {}
                        errades_dict[r_email_curs_objecte]['time'] = r_time
                        errades_dict[r_email_curs_objecte][
                                                           'resposta'
                                                           ] = respostes_row

                    else:
                        key_errades = str(resposta_anterior) +\
                                     str(resposta_anterior['time'])
                        errades_dict[key_errades] = {}
                        errades_dict[key_errades][
                                                 'time'
                                                 ] = resposta_anterior['time']
                        errades_dict[key_errades][
                                                 'resposta'
                                                 ] = resposta_anterior[
                                                                 'resposta'
                                                                       ]

                        respostes_dict[r_email_curs_objecte] = {}
                        respostes_dict[r_email_curs_objecte][
                                                             'time'
                                                             ] = r_time
                        respostes_dict[r_email_curs_objecte][
                                                             'resposta'
                                                             ] = respostes_row

                else:  # Conserva nova resposta
                    if (r_time > resposta_anterior['time']):
                        key_errades = str(resposta_anterior) +\
                                     str(resposta_anterior['time'])
                        errades_dict[key_errades] = {}
                        errades_dict[key_errades]['time'
                                                  ] = resposta_anterior['time']
                        errades_dict[key_errades]['resposta'
                                                  ] = resposta_anterior[
                                                                  'resposta'
                                                                        ]

                        respostes_dict[r_email_curs_objecte] = {}
                        respostes_dict[r_email_curs_objecte]['time'] = r_time
                        respostes_dict[r_email_curs_objecte]['resposta'
                                                             ] = respostes_row
                    else:
                        errades_dict[r_email_curs_objecte] = {}
                        errades_dict[r_email_curs_objecte]['time'] = r_time
                        errades_dict[r_email_curs_objecte]['resposta'
                                                           ] = respostes_row

    resultats = open(FILE_ANSWERS_RECORD, 'w', encoding='utf-8')
    resultats_writer = csv.writer(resultats)
    # Encapçalats
    resultats_writer.writerow(
                             ['ALUMNE', 'TIMESTAMP', 'EMAIL', 'GRUP',
                              'OBJECTE', 'MP-ÍTEM1', 'MP-ÍTEM2', 'MP-ÍTEM3',
                              'MP-ÍTEM4', 'MP-COMENTARI', 'TUTORIA1-ÍTEM1',
                              'TUTORIA1-ÍTEM2', 'TUTORIA1-ÍTEM3',
                              'TUTORIA1-COMENTARI', 'TUTORIA2-ÍTEM1',
                              'TUTORIA2-ÍTEM2', 'TUTORIA2-ÍTEM3',
                              'TUTORIA2-ÍTEM4', 'TUTORIA2-COMENTARI',
                              'CENTRE-ÍTEM1', 'CENTRE-ÍTEM2', 'CENTRE-ÍTEM3',
                              'CENTRE-ÍTEM4', 'CENTRE-ÍTEM5', 'CENTRE-ÍTEM6',
                              'CENTRE-COMENTARI'])
    [resultats_writer.writerow(v['resposta'])
     for k, v in respostes_dict.items()]
    resultats.close()

    errades_rec = open(FILE_ERRORS_RECORD, 'a', encoding='utf-8')
    errades_rec_writer = csv.writer(errades_rec)
    for k, v in errades_dict.items():
        if OPTION_DUPLICATE_FILES == 0:
            errades_rec_writer.writerow(
                                [v['resposta'][0]] +
                                [v['resposta'][3]] +
                                ['AVALUACIÓ POSTERIOR REPETIDA'] +
                                v['resposta'][1:])
        else:
            errades_rec_writer.writerow(
                                [v['resposta'][0]] +
                                [v['resposta'][3]] +
                                ['AVALUACIÓ ANTERIOR DESCARTADA'] +
                                v['resposta'][1:])
    errades_rec.close()


def generate_list_of_answers():
    """def generate_list_of_answers()
    Descripció: Genera un fitxer amb els objectes avaluats per l'alumne.
    Entrada:    Cap
    Sortida:    Fitxer FILE_STUDENTS_WITH_AVALUATED_MP
    """
    alumnes_mp_dict = {}

    # Crea diccionari d'alumnes amb els MP matriculats
    with open(SOURCE_FILE_STUDENTS_WITH_MP, 'r', encoding='utf-8') as alumnes:
        alumnes_reader = csv.reader(alumnes)
        next(alumnes_reader, None)

        for alumnes_row in alumnes_reader:
            email = alumnes_row[1]
            nom_cognoms = alumnes_row[0]
            curs = alumnes_row[2]
            mpList = alumnes_row[3:]
            mpList = [mp.lower() for mp in mpList]

            # Afegeix altres 2 elements a la llista per la tutoria i el centre
            mpList.extend(('x', 'x'))

            if email != "":
                alumnes_mp_dict[email] = {}
                alumnes_mp_dict[email]['nom_cognoms'] = nom_cognoms
                alumnes_mp_dict[email]['curs'] = curs
                alumnes_mp_dict[email]['objecte'] = mpList

    with open(FILE_ANSWERS_RECORD, 'r', encoding='utf-8') as respostes:
        respostes_reader = csv.DictReader(respostes)

        for respostes_row in respostes_reader:
            nom_cognoms = respostes_row['ALUMNE']
            email = respostes_row['EMAIL']
            curs = respostes_row['GRUP']
            objecte = extract_mp_number(respostes_row['OBJECTE'])

            # Aconsegueix el llistat d'MP matriculats i respostes
            avaluatsList = alumnes_mp_dict.get(email)['objecte']

            # Esbrina la posició a mpList segons l'objecte avaluat
            index_mapping_list = [
                                ('MP01', '0'), ('MP02', '1'), ('MP03', '2'),
                                ('MP04', '3'), ('MP05', '4'), ('MP06', '5'),
                                ('MP07', '6'), ('MP08', '7'), ('MP09', '8'),
                                ('MP10', '9'), ('MP11', '10'), ('MP12', '11'),
                                ('MP13', '12'), ('MP14', '13'), ('MP15', '14'),
                                ('Tutoria 1r curs', '15'),
                                ('Tutoria 2n curs', '15'), ('El centre', '16')]
            for k, v in index_mapping_list:
                objecte = objecte.replace(k, v)

            # Escriu 'avaluat' a la posició de l'objecte avaluat
            for n, i in enumerate(avaluatsList):
                if n == int(objecte):
                    avaluatsList[n] = 'avaluat'

            # Actualitza el llistat al diccionari
            alumnes_mp_dict[email]['objecte'] = avaluatsList

    # Escriu els resultats al fitxer de sortida
    result = open(FILE_STUDENTS_WITH_AVALUATED_MP, 'w', encoding='utf-8')
    result_writer = csv.writer(result)
    # Encapçalats
    result_writer.writerow(
                          ['CORREU', 'COGNOM/S I NOM', 'GRUP', 'MP01', 'MP02',
                           'MP03', 'MP04', 'MP05', 'MP06', 'MP07', 'MP08',
                           'MP09', 'MP10', 'MP11', 'MP12', 'MP13', 'MP14',
                           'MP15', 'TUTORIA', 'CENTRE'])

    [result_writer.writerow(
                         [k] +
                         [alumnes_mp_dict[k]['nom_cognoms']] +
                         [alumnes_mp_dict[k]['curs']] +
                         alumnes_mp_dict[k]['objecte'])
     for k, v in alumnes_mp_dict.items()]

    result.close()


def final_result_files_arranger():
    """def final_result_files_arranger
    Descripció: Elimina la informació sensible dels registres d'errades i
                respostes, i prepara els resultats per
                copiar i enganxar les dades al full de càlcul d'estadístiques.
    Entrada:    Cap
    Sortida:    Fitxer FILE_ERRORS
                Fitxer FILE_ANSWERS
    """
    with open(FILE_ERRORS_RECORD, 'r', encoding='utf-8') as errades_rec:
        errades_rec_reader = csv.DictReader(errades_rec)

        with open(FILE_ERRORS, 'w', encoding='utf-8') as errades:
            errades_writer = csv.writer(errades)

            # Encapçalats
            errades_writer.writerow((['ALUMNE', 'CURS', 'MOTIU', 'TIMESTAMP',
                                     'EMAIL', 'CURS AVALUAT', 'OBJECTE']))

            for errades_recRow in errades_rec_reader:
                errades_writer.writerow(
                                [errades_recRow['ALUMNE']] +
                                [errades_recRow['CURS']] +
                                [errades_recRow['MOTIU']] +
                                [errades_recRow['TIMESTAMP']] +
                                [errades_recRow['EMAIL']] +
                                [errades_recRow['CURS AVALUAT']] +
                                [errades_recRow['OBJECTE']])

    with open(FILE_ANSWERS_RECORD, 'r', encoding='utf-8') as resultats_rec:
        resultats_rec_reader = csv.reader(resultats_rec)
        next(resultats_rec_reader, None)

        with open(FILE_ANSWERS, 'w', encoding='utf-8')\
                as resultats:
            resultats_writer = csv.writer(resultats)

            # Encapçalats
            resultats_writer.writerow(
                                     ['TIMESTAMP', 'GRUP', 'OBJECTE',
                                      'MP-ÍTEM1', 'MP-ÍTEM2', 'MP-ÍTEM3',
                                      'MP-ÍTEM4', 'MP-COMENTARI',
                                      'TUTORIA1-ÍTEM1', 'TUTORIA1-ÍTEM2',
                                      'TUTORIA1-ÍTEM3', 'TUTORIA1-COMENTARI',
                                      'TUTORIA2-ÍTEM1', 'TUTORIA2-ÍTEM2',
                                      'TUTORIA2-ÍTEM3', 'TUTORIA2-ÍTEM4',
                                      'TUTORIA2-COMENTARI', 'CENTRE-ÍTEM1',
                                      'CENTRE-ÍTEM2', 'CENTRE-ÍTEM3',
                                      'CENTRE-ÍTEM4', 'CENTRE-ÍTEM5',
                                      'CENTRE-ÍTEM6', 'CENTRE-COMENTARI'])

            for resultats_rec_row in resultats_rec_reader:
                timestamp = resultats_rec_row[1]
                curs = resultats_rec_row[3]
                objecte = resultats_rec_row[4]
                avaluacions = resultats_rec_row[5:]

                resultats_writer.writerow(
                                          [timestamp] +
                                          [curs] +
                                          [objecte] +
                                          avaluacions)


def generate_reports():
    """def generateCommentsReport()
    Descripció: Genera informes per cadascun dels departaments (Administració i
                Informàtica) i el Centre
                amb les avaluacions i comentaris rebuts
    Entrada:    Cap
    Sortida:    Fitxer REPORT_FILE_CENTRE
                Fitxer REPORT_FILE_ADM
                Fitxer REPORT_FILE_INF
    """
    report_adm = open(REPORT_FILE_ADM, 'w', encoding='utf-8')
    report_adm_writer = csv.writer(report_adm)
    # Encapçalats
    report_adm_writer.writerow(
                       ['GRUP', 'OBJECTE', 'ÍTEM1', 'ÍTEM2', 'ÍTEM3', 'ÍTEM4',
                        'COMENTARI'])

    report_centre = open(REPORT_FILE_CENTRE, 'w', encoding='utf-8')
    report_centre_writer = csv.writer(report_centre)
    # Encapçalats
    report_centre_writer.writerow(
                       ['GRUP', 'OBJECTE', 'ÍTEM1', 'ÍTEM2', 'ÍTEM3', 'ÍTEM4',
                        'ÍTEM5', 'ÍTEM6', 'COMENTARI'])

    report_inf = open(REPORT_FILE_INF, 'w', encoding='utf-8')
    report_inf_writer = csv.writer(report_inf)
    # Encapçalats
    report_inf_writer.writerow(
                       ['GRUP', 'OBJECTE', 'ÍTEM1', 'ÍTEM2', 'ÍTEM3', 'ÍTEM4',
                        'COMENTARI'])

    with open(FILE_ANSWERS_RECORD, 'r', encoding='utf-8') as resultats:
        resultats_reader = csv.reader(resultats)
        next(resultats_reader, None)

        for resultats_row in resultats_reader:
            curs = resultats_row[3]
            objecte = resultats_row[4]
            avalua_mp = resultats_row[5:10]
            avalua_tutoria1 = resultats_row[10:13] +\
                                           ["no s'avalua"] +\
                resultats_row[13:14]
            avalua_tutoria2 = resultats_row[14:19]
            avalua_centre = resultats_row[19:]

            grup_avaluat = find_avaluated_object(curs)

            if grup_avaluat == 'Informàtica' and 'MP' in objecte:
                report_inf_writer.writerow([curs] + [objecte] + avalua_mp)
            elif grup_avaluat == 'Informàtica' and 'Tutoria 1r curs'\
                                 in objecte:
                report_inf_writer.writerow([curs] +
                                           [objecte] +
                                           avalua_tutoria1)
            elif grup_avaluat == 'Informàtica' and 'Tutoria 2n curs'\
                                 in objecte:
                report_inf_writer.writerow([curs] +
                                           [objecte] +
                                           avalua_tutoria2)
            elif grup_avaluat == 'Administració' and 'MP' in objecte:
                report_adm_writer.writerow([curs] + [objecte] + avalua_mp)
            elif grup_avaluat == 'Administració' and\
                                 'Tutoria 1r curs' in objecte:
                report_adm_writer.writerow([curs] +
                                           [objecte] +
                                           avalua_tutoria1)
            elif grup_avaluat == 'Administració' and\
                                 'Tutoria 2n curs' in objecte:
                report_adm_writer.writerow([curs] +
                                           [objecte] +
                                           avalua_tutoria2)
            elif 'El centre' in objecte:
                report_centre_writer.writerow([curs] +
                                              [objecte] +
                                              avalua_centre)

    report_adm.close()
    report_centre.close()
    report_inf.close()


def find_avaluated_object(s):
    """def find_avaluated_object(s)
    Descripció: Classifica els grups per departaments (Adminsitració i
                Informàtica)
    Entrada:    String
    Sortida:    String
    """
    grups_mapping_list = [
                        ('AF', 'Administració'), ('ASIX', 'Informàtica'),
                        ('DAM', 'Informàtica'), ('GA', 'Administració'),
                        ('SMX', 'Informàtica')]

    for k, v in grups_mapping_list:
        if k in s:
            return v


def setup_files():
    """def setup_files()
    Descripció: Elimina fitxers de sortida anteriors que puguin existir al
                directori.
    Entrada:    Cap.
    Sortida:    Elimina fixters anteriors.
    """
    # Elimina arxius anteriors
    os.remove(FILE_ERRORS)\
        if os.path.exists(FILE_ERRORS) else None
    os.remove(FILE_ANSWERS)\
        if os.path.exists(FILE_ANSWERS) else None
    os.remove(FILE_STUDENTS_WITH_AVALUATED_MP)\
        if os.path.exists(FILE_STUDENTS_WITH_AVALUATED_MP) else None

    os.remove(os.path.join(os.getcwd(), 'TmpFiles', FILE_ANSWERS_TMP))\
        if os.path.exists(os.path.join(
                                       os.getcwd(),
                                       'TmpFiles',
                                       FILE_ANSWERS_TMP)) else None
    os.rmdir(os.path.join(os.getcwd(), 'TmpFiles'))\
        if os.path.exists(os.path.join(os.getcwd(), 'TmpFiles')) else None

    os.remove(os.path.join(os.getcwd(), 'RcdFiles', FILE_ERRORS_RECORD))\
        if os.path.exists(os.path.join(
                                       os.getcwd(),
                                       'RcdFiles',
                                       FILE_ERRORS_RECORD)) else None
    os.remove(os.path.join(os.getcwd(), 'RcdFiles', FILE_ANSWERS_RECORD))\
        if os.path.exists(os.path.join(
                                       os.getcwd(),
                                       'RcdFiles',
                                       FILE_ANSWERS_RECORD)) else None
    os.rmdir(os.path.join(os.getcwd(), 'RcdFiles')) \
        if os.path.exists(os.path.join(os.getcwd(), 'RcdFiles')) else None

    os.remove(os.path.join(os.getcwd(), 'Informes', REPORT_FILE_CENTRE))\
        if os.path.exists(os.path.join(
                                       os.getcwd(),
                                       'Informes',
                                       REPORT_FILE_CENTRE)) else None
    os.remove(os.path.join(os.getcwd(), 'Informes', REPORT_FILE_ADM))\
        if os.path.exists(os.path.join(
                                       os.getcwd(),
                                       'Informes',
                                       REPORT_FILE_INF)) else None
    os.remove(os.path.join(
                           os.getcwd(),
                           'Informes',
                           REPORT_FILE_INF))\
        if os.path.exists(os.path.join(
                                       os.getcwd(),
                                       'Informes',
                                       REPORT_FILE_INF)) else None
    os.rmdir(os.path.join(os.getcwd(), 'Informes'))\
        if os.path.exists(os.path.join(os.getcwd(), 'Informes')) else None


def setup_options():
    """def setup_options(
                         OPTION_TMP_FILES,
                         OPTION_TMP_RECORDS,
                         OPTION_DUPLICATE_FILES)
    Descripció: Demana a l'usuari que definieixi les opcions no establertes.
    Entrada:    Cap.
    Sortida:    Defineix les variables globals OPTION_TMP_FILES,
                OPTION_TMP_RECORDS, OPTION_DUPLICATE_FILES en el seu cas.
    """
    global OPTION_TMP_FILES
    global OPTION_TMP_RECORDS
    global OPTION_DUPLICATE_FILES
    global OPTION_REPORTS

    while OPTION_TMP_FILES != 0 and OPTION_TMP_FILES != 1:
        OPTION_TMP_FILES = answer_from_string_to_binary(input(
                    "Voleu conservar els arxius temporals? (s/n) ").lower())

    while OPTION_TMP_RECORDS != 0 and OPTION_TMP_RECORDS != 1:
        OPTION_TMP_RECORDS = answer_from_string_to_binary(input(
                    "Voleu conservar els registres? (s/n) ").lower())

    while OPTION_DUPLICATE_FILES != 0 and OPTION_DUPLICATE_FILES != 1:
        OPTION_DUPLICATE_FILES = answer_from_string_to_binary(input(
                    "En cas de respostes duplicades, quina voleu conservar? \
                     (1: la primera, 2: l'última) ").lower())

    while OPTION_REPORTS != 0 and OPTION_DUPLICATE_FILES != 1:
        OPTION_REPORTS = answer_from_string_to_binary(input(
                    "Desitja generar els informes? (s/n) ").lower())


def answer_from_string_to_binary(s):
    """def answer_from_string_to_binary(s)
    Descripció: Converteix una string amb una 's'/'y' o amb una 'n' en un int
                0 o 1 respectivament.
    Entrada:    string
    Sortida:    int
    Exemple:    'n' retorna 1
    """
    if s == 'y' or s == 's' or s == '2':
        return 1
    else:
        return 0


def del_tmp_and_reg_files():
    """def del_tmp_and_reg_files(OPTION_TMP_FILES, OPTION_TMP_RECORDS)
    Descripció: Ignora o elimina els fitxers i registres temporals.
    Entrada:    Cap.
    Sortida:    Cap.
    """
    global OPTION_TMP_FILES
    global OPTION_TMP_RECORDS

    if OPTION_TMP_FILES == 1:  # Conserva arxius temporals
        # Crea subdirectori i mou dins arxius temporals
        if not os.path.exists(os.path.join(os.getcwd(), 'TmpFiles')):
            os.makedirs(os.path.join(os.getcwd(), 'TmpFiles'))
        os.rename(
                  os.path.join(os.getcwd(), FILE_ANSWERS_TMP),
                  os.path.join(os.getcwd(), 'TmpFiles', FILE_ANSWERS_TMP))
    else:  # Elimina arxius temporals
        os.remove(FILE_ANSWERS_TMP)\
            if os.path.exists(FILE_ANSWERS_TMP) else None
        print('Arxius temporals eliminats.')

    if OPTION_TMP_RECORDS == 1:  # Conserva els registres
        # Crea subdirectori i mou dins registres
        if not os.path.exists(os.path.join(os.getcwd(), 'RcdFiles')):
            os.makedirs(os.path.join(os.getcwd(), 'RcdFiles'))
        os.rename(
                  os.path.join(os.getcwd(), FILE_ERRORS_RECORD),
                  os.path.join(os.getcwd(), 'RcdFiles', FILE_ERRORS_RECORD))
        os.rename(
                  os.path.join(os.getcwd(), FILE_ANSWERS_RECORD),
                  os.path.join(os.getcwd(), 'RcdFiles', FILE_ANSWERS_RECORD))
    else:  # Elimina registres
        os.remove(FILE_ERRORS_RECORD)\
            if os.path.exists(FILE_ERRORS_RECORD) else None
        os.remove(FILE_ANSWERS_RECORD)\
            if os.path.exists(FILE_ANSWERS_RECORD) else None
        print('Registres temporals eliminats.')

    if OPTION_REPORTS == 1:  # Genera informes
        if not os.path.exists(os.path.join(os.getcwd(), 'Informes')):
            os.makedirs(os.path.join(os.getcwd(), 'Informes'))
        os.rename(
                  os.path.join(os.getcwd(), REPORT_FILE_CENTRE),
                  os.path.join(os.getcwd(), 'Informes', REPORT_FILE_CENTRE))
        os.rename(
                  os.path.join(os.getcwd(), REPORT_FILE_ADM),
                  os.path.join(
                               os.getcwd(),
                               'Informes',
                               REPORT_FILE_ADM))
        os.rename(
                  os.path.join(os.getcwd(), REPORT_FILE_INF),
                  os.path.join(
                               os.getcwd(),
                               'Informes',
                               REPORT_FILE_INF))


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
    check_source_file(SOURCE_FILE_STUDENTS_WITH_MP)
    check_source_file(SOURCE_FILE_STUDENT_ANSWERS)

    setup_options()
    setup_files()

    filter_responses()

    filter_duplicates()

    generate_list_of_answers()
    final_result_files_arranger()
    if OPTION_REPORTS == 1:
        generate_reports()
    del_tmp_and_reg_files()
