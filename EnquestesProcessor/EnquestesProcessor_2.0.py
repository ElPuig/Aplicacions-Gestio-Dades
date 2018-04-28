#!/usr/bin/python3.6
# -*- coding: UTF-8 -*-

"""EnquestesProcessor_2.0:
Fitxers d'entrada:
    - alumnes-mp.csv: llista dels alumnes matriculats a cada CF,
                      amb el seu nom complet, l'adreça Xeill, el cicle i curs,
                      i una «x» per cada MP al qual estigui matriculat
    - respostes.csv: descarregat des del formulari d'avaluació de Google Drive,
                     conté les valoracions dels alumnes
Fitxers de sortida:
    - finals:
        * estadística_respostes.csv: conté la mitjana de les respostes per ítem
                                     objecte avaluat i grup
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

Novetats a la versió 2.0:
    - càlcul de l'estadística per grup, objecte i ítem
    - nou format dels informes per departament i centre
"""

import csv
import collections
from dateutil import parser
import errno
import os

RECORD_FILE_ERRORS = 'errades_rec.csv'
RECORD_FILE_ANSWERS = 'resultats_rec.csv'
REPORT_FILE_ADM = 'informe_Dept_Admin.csv'
REPORT_FILE_INF = 'informe_Dept_Inform.csv'
REPORT_FILE_CENTRE = 'informe_Centre.csv'
RESULT_FILE_ANSWERS = 'resultats_respostes.csv'
RESULT_FILE_ERRORS = 'resultats_errades.csv'
RESULT_FILE_STATISTICS = 'estadística_respostes.csv'
RESULT_FILE_STUDENTS_WITH_AVALUATED_MP = 'resultats_alumnes-respostes.csv'
SOURCE_FILE_STUDENTS_WITH_MP = 'alumnes-mp.csv'
SOURCE_FILE_STUDENT_ANSWERS = 'respostes.csv'
TMP_FILE_ANSWERS = 'resultats_tmp.csv'
# tmp -> 0 = elimina
#        1 = conserva
#        2 = consulta a usuari
OPTION_TMP_FILES = 0
OPTION_TMP_RECORDS = 0
# duplicates -> 0 = conserva primera
#               1 = conserva nova
#               2 = consulta a usuari
OPTION_DUPLICATED_ANSWERS = 1
# reports -> 0 = no
#            1 = sí
#            2 = consulta a usuari
OPTION_REPORTS = 1


def filter_invalid_responses():
    """def filter_invalid_responses()
    Descripció: Filtra les respostes d'alumnes que no estiguin matriculats al
                cicle o al MP avaluat, o que no pertanyin al curs de la tutoria
                avaluada.
    Entrada:    Cap.
    Sortida:    Fitxer resultats_tmp.csv
                Fitxer errades_rec.csv
    """
    resultats_tmp = open(TMP_FILE_ANSWERS, 'w', encoding='utf-8')
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
    errades_rec = open(RECORD_FILE_ERRORS, 'w', encoding='utf-8')
    errades_rec_writer = csv.writer(errades_rec)

    # Encapçalats
    errades_rec_writer.writerow(
                              ['ALUMNE', 'CURS', 'MOTIU', 'TIMESTAMP', 'EMAIL',
                               'CICLE AVALUAT', 'OBJECTE AVALUAT', 'MP-ÍTEM1',
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
                        arranged_respostes_row_with_groupclass =\
                                                  retrieve_groupclass(
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
                                                    ['MP INCORRECTE'] +
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
                                        arranged_respostes_row_with_groupclass)

                # Enregistra com a errors els emails no trobats
                if email_found is False:
                    errades_rec_writer.writerow(
                                     ['desconegut'] +
                                     ['desconegut'] +
                                     ['EMAIL DESCONEGUT'] +
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


def filter_duplicated_answers():
    """def filter_duplicated_answers()
    Descripció: Filtra les respostes duplicades.
    Entrada:    Cap.
    Sortida:    Cap.
    """
    global OPTION_DUPLICATED_ANSWERS

    respostes_dict = {}
    errades_dict = {}

    with open(TMP_FILE_ANSWERS, 'r', encoding='utf-8') as respostes:
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
                if OPTION_DUPLICATED_ANSWERS == 0:  # Conserva primera resposta
                    if (r_time > resposta_anterior['time']):
                        errades_dict[r_email_curs_objecte] = {}
                        errades_dict[r_email_curs_objecte]['time'] = r_time
                        errades_dict[r_email_curs_objecte][
                                                           'resposta'
                                                           ] = respostes_row
                        errades_dict[r_email_curs_objecte][
                                                 'referenced_timestamp'
                                                 ] = resposta_anterior['time']
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
                        errades_dict[key_errades][
                                                 'referenced_timestamp'
                                                 ] = r_time

                        respostes_dict[r_email_curs_objecte] = {}
                        respostes_dict[r_email_curs_objecte][
                                                             'time'
                                                             ] = r_time
                        respostes_dict[r_email_curs_objecte][
                                                             'resposta'
                                                             ] = respostes_row

                else:  # Conserva resposta més recent
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
                        errades_dict[key_errades][
                                                 'referenced_timestamp'
                                                 ] = r_time

                        respostes_dict[r_email_curs_objecte] = {}
                        respostes_dict[r_email_curs_objecte]['time'] = r_time
                        respostes_dict[r_email_curs_objecte]['resposta'
                                                             ] = respostes_row
                    else:
                        errades_dict[r_email_curs_objecte] = {}
                        errades_dict[r_email_curs_objecte]['time'] = r_time
                        errades_dict[r_email_curs_objecte]['resposta'
                                                           ] = respostes_row
                        errades_dict[r_email_curs_objecte][
                                                 'referenced_timestamp'
                                                 ] = resposta_anterior['time']

    resultats = open(RECORD_FILE_ANSWERS, 'w', encoding='utf-8')
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

    errades_rec = open(RECORD_FILE_ERRORS, 'a', encoding='utf-8')
    errades_rec_writer = csv.writer(errades_rec)
    for k, v in errades_dict.items():
        if OPTION_DUPLICATED_ANSWERS == 0:
            errades_rec_writer.writerow(
                                [v['resposta'][0]] +
                                [v['resposta'][3]] +
                                ['AVALUACIÓ POSTERIOR REPETIDA' +
                                 ' (resp. original: ' +
                                 str(v['referenced_timestamp']) + ')'] +
                                v['resposta'][1:])
        else:
            errades_rec_writer.writerow(
                                [v['resposta'][0]] +
                                [v['resposta'][3]] +
                                ['AVALUACIÓ ANTERIOR DESCARTADA' +
                                 ' (resp. nova: ' +
                                 str(v['referenced_timestamp']) + ')'] +
                                v['resposta'][1:])
    errades_rec.close()


def generate_list_of_answers():
    """def generate_list_of_answers()
    Descripció: Genera un fitxer amb els objectes avaluats per l'alumne.
    Entrada:    Cap
    Sortida:    Fitxer RESULT_FILE_STUDENTS_WITH_AVALUATED_MP
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

    with open(RECORD_FILE_ANSWERS, 'r', encoding='utf-8') as respostes:
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
    result = open(RESULT_FILE_STUDENTS_WITH_AVALUATED_MP,
                  'w', encoding='utf-8')
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
    Sortida:    Fitxer RESULT_FILE_ERRORS
                Fitxer RESULT_FILE_ANSWERS
    """
    with open(RECORD_FILE_ERRORS, 'r', encoding='utf-8') as errades_rec:
        errades_rec_reader = csv.DictReader(errades_rec)

        with open(RESULT_FILE_ERRORS, 'w', encoding='utf-8') as errades:
            errades_writer = csv.writer(errades)

            # Encapçalats
            errades_writer.writerow((['ALUMNE', 'CURS', 'MOTIU',
                                      'EMAIL', 'CICLE AVALUAT',
                                      'OBJECTE AVALUAT',
                                      'TIMESTAMP']))

            for errades_recRow in errades_rec_reader:
                errades_writer.writerow(
                                [errades_recRow['ALUMNE']] +
                                [errades_recRow['CURS']] +
                                [errades_recRow['MOTIU']] +
                                [errades_recRow['EMAIL']] +
                                [errades_recRow['CICLE AVALUAT']] +
                                [errades_recRow['OBJECTE AVALUAT']] +
                                [errades_recRow['TIMESTAMP']])

    with open(RECORD_FILE_ANSWERS, 'r', encoding='utf-8') as resultats_rec:
        resultats_rec_reader = csv.reader(resultats_rec)
        next(resultats_rec_reader, None)

        with open(RESULT_FILE_ANSWERS, 'w', encoding='utf-8')\
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


def generate_statistics():
    statistics = open(RESULT_FILE_STATISTICS, 'w', encoding='utf-8')
    statistics_writer = csv.writer(statistics)

    # Encapçalat
    statistics_writer.writerow(['DEPARTAMENT', 'GRUP', 'OBJECTE', 'ÍTEM 1',
                                'ÍTEM 2', 'ÍTEM 3', 'ÍTEM 4', 'ÍTEM 5',
                                'ÍTEM 6', 'NOMBRE RESPOSTES'])

    survey_avg_results_dict = collections.OrderedDict()
    survey_avg_results_dict = fill_survey_avg_results_dict(
                                  **survey_avg_results_dict)

    for cicle, objecte in sorted(survey_avg_results_dict.items()):
        departament = get_departament(cicle)
        objectes_dict = collections.OrderedDict(
                            survey_avg_results_dict[cicle].items())
        for objecte, item in sorted(objectes_dict.items()):
            items_dict = collections.OrderedDict(
                            objectes_dict[objecte].items())
            items_list = generate_items_points_and_responses_list(**items_dict)
            statistics_writer.writerow(
                [departament, cicle, objecte] + items_list)

    statistics.close()


def fill_survey_avg_results_dict(**survey_avg_results_dict):
    """fill_survey_avg_results_dict(**survey_avg_results_dict)
    Descripció: Emplena els cicles a survey_avg_results_dict.
    Entrada:    Diccionari buit.
    Sortida:    Diccionari complet amb el total de punts per ítem,
                nombre de respostes per ítem i mitjana per ítem de cada
                objecte de cada cicle.
    """
    survey_avg_results_dict = add_cicles_to_dict(
                                  **survey_avg_results_dict)
    survey_avg_results_dict = add_objects_to_cicle(
                                  **survey_avg_results_dict)
    survey_avg_results_dict = add_qualifications_to_objects(
                                  **survey_avg_results_dict)

    return survey_avg_results_dict


def add_cicles_to_dict(**survey_avg_results_dict):
    """add_cicles_to_dict(**survey_avg_results_dict)
    Descripció: Emplena els cicles a survey_avg_results_dict.
    Entrada:    Diccionari buit.
    Sortida:    Diccionari amb tots els cicles participants a l'enquesta.
    """
    with open(RESULT_FILE_ANSWERS, 'r', encoding='utf-8') as respostes:
        respostes_reader = csv.DictReader(respostes)

        for respostes_row in respostes_reader:
            if respostes_row['GRUP'] not in survey_avg_results_dict.keys():
                survey_avg_results_dict[respostes_row['GRUP']] = {}

    return survey_avg_results_dict


def add_objects_to_cicle(**survey_avg_results_dict):
    """add_objects_to_cicle(**survey_avg_results_dict)
    Descripció: Emplena els objectes a survey_avg_results_dict.
    Entrada:    Diccionari amb els cicles.
    Sortida:    Diccionari amb els apartats d'MP, tutoria i centre
                afegits per cada cicle.
    """
    with open(RESULT_FILE_ANSWERS, 'r', encoding='utf-8') as respostes:
        respostes_reader = csv.DictReader(respostes)

        for respostes_row in respostes_reader:
            if (respostes_row['OBJECTE'] not in survey_avg_results_dict[
                                    respostes_row['GRUP']].keys()):
                survey_avg_results_dict[
                    respostes_row['GRUP']
                    ][respostes_row['OBJECTE']] = {}

    return survey_avg_results_dict


def add_qualifications_to_objects(**survey_avg_results_dict):
    """add_qualifications_to_objects(**survey_avg_results_dict)
    Descripció: Emplena els resultats per ítem de cada objecte a
                survey_avg_results_dict.
    Entrada:    Diccionari amb els cicles i objectes.
    Sortida:    Diccionari actualitzat amb el total de punts per ítem,
                nombre de respostes per ítem i mitjana per ítem de cada
                objecte.
    """
    with open(RESULT_FILE_ANSWERS, 'r', encoding='utf-8') as respostes:
        respostes_reader = csv.DictReader(respostes)

        for respostes_row in respostes_reader:
            item_number = 1
            for column in respostes_row:
                if (respostes_row[column].isdigit() is True):
                    # Add to total points by item
                    if ('item' + str(item_number)
                        ) not in survey_avg_results_dict[
                        respostes_row['GRUP']
                            ][respostes_row['OBJECTE']].keys():
                        survey_avg_results_dict[
                            respostes_row['GRUP']
                                  ][respostes_row['OBJECTE']
                                    ]['item' + str(item_number)] = {}

                        survey_avg_results_dict[
                            respostes_row['GRUP']
                                        ][respostes_row['OBJECTE']
                                          ]['item' + str(item_number)
                                            ]['TOTAL POINTS'] = 0

                    survey_avg_results_dict[
                        respostes_row['GRUP']
                                    ][respostes_row['OBJECTE']
                                      ]['item' + str(item_number)
                                        ]['TOTAL POINTS'] += int(
                                                    respostes_row[column])

                    # Add to total responses by item
                    if 'TOTAL RESPONSES' not in survey_avg_results_dict[
                        respostes_row['GRUP']
                        ][respostes_row['OBJECTE']
                          ]['item' + str(item_number)].keys():
                        survey_avg_results_dict[
                            respostes_row['GRUP']
                            ][respostes_row['OBJECTE']
                              ]['item' + str(item_number)
                                ]['TOTAL RESPONSES'] = 1

                    else:
                        survey_avg_results_dict[
                          respostes_row['GRUP']
                          ][respostes_row['OBJECTE']
                            ]['item' + str(item_number)
                              ]['TOTAL RESPONSES'] += 1

                    # Recalculate average points per item
                    survey_avg_results_dict[
                        respostes_row['GRUP']
                        ][respostes_row['OBJECTE']
                          ]['item' + str(item_number)
                            ]['AVERAGE POINTS'] = (survey_avg_results_dict[
                                                respostes_row['GRUP']
                                                ][respostes_row['OBJECTE']
                                                  ]['item' + str(item_number)
                                                    ]['TOTAL POINTS'] /
                                               survey_avg_results_dict[
                                                respostes_row['GRUP']
                                                ][respostes_row['OBJECTE']
                                                  ]['item' + str(item_number)
                                                    ]['TOTAL RESPONSES'])
                    item_number += 1

    return survey_avg_results_dict


def generate_items_points_and_responses_list(**items_dict):
    """generate_items_points_and_responses_list(**items_dict)
    Descripció: Retorna el departament corresponent al cicle.
    Entrada:    Diccionari amb els ítems.
    Sortida:    String amb el nom del departament.
    """
    items_list = []
    for k, v in sorted(items_dict.items()):
        items_list.append(
            format(round(items_dict[k]['AVERAGE POINTS'], 2), '.2f'))

    while (len(items_list) < 6):
        items_list.append('')

    items_list.append(items_dict[k]['TOTAL RESPONSES'])

    return items_list


def get_departament(cicle):
    """get_departament(cicle)
    Descripció: Retorna el departament corresponent al cicle.
    Entrada:    String amb el nom del cicle.
    Sortida:    String amb el nom del departament.
    """
    if 'AF' in cicle or 'GA' in cicle:
        return 'ADMINISTRACIÓ'
    return 'INFORMÀTICA'


def generate_reports():
    """def generateCommentsReport()
    Descripció: Genera informes per cadascun dels departaments (Administració
                i Informàtica) i el centre amb les avaluacions i comentaris
                rebuts.
    Entrada:    Cap
    Sortida:    Fitxer REPORT_FILE_CENTRE
                Fitxer REPORT_FILE_ADM
                Fitxer REPORT_FILE_INF
    """
    depts_dict = {'ADMINISTRACIÓ': REPORT_FILE_ADM,
                  'INFORMÀTICA': REPORT_FILE_INF}

    for dept, file in depts_dict.items():
        report_dept = open(depts_dict[dept], 'w', encoding='utf-8')
        report_dept_writer = csv.writer(report_dept)
        # Encapçalats
        report_dept_writer.writerow(
                        ['GRUP', 'OBJECTE', 'ÍTEM 1', 'ÍTEM 2', 'ÍTEM 3',
                         'ÍTEM 4', 'COMENTARI'])

        with open(RESULT_FILE_STATISTICS, 'r', encoding='utf-8') as statistics:
            statistics_reader = csv.DictReader(statistics)

            for statistics_row in statistics_reader:
                comments = ''
                if (statistics_row['DEPARTAMENT'] == dept and
                   'mp' in statistics_row['OBJECTE'].lower()):
                    with open(RESULT_FILE_ANSWERS,
                              'r', encoding='utf-8') as resultats:
                        resultats_reader = csv.DictReader(resultats)
                        for resultats_row in resultats_reader:
                            if (statistics_row[
                                    'GRUP'] == resultats_row['GRUP'] and
                               statistics_row[
                                    'OBJECTE'] == resultats_row['OBJECTE'] and
                               resultats_row['MP-COMENTARI'] != ''):
                                if comments != '':
                                    comments += '\n'
                                comments += resultats_row['MP-COMENTARI'
                                                          ].replace('\n', ' ')
                    report_dept_writer.writerow([statistics_row['GRUP']] +
                                                [statistics_row['OBJECTE']] +
                                                [statistics_row['ÍTEM 1']] +
                                                [statistics_row['ÍTEM 2']] +
                                                [statistics_row['ÍTEM 3']] +
                                                [statistics_row['ÍTEM 4']] +
                                                [comments])

                elif (statistics_row['DEPARTAMENT'] == dept and
                      'tutoria' in statistics_row['OBJECTE'].lower()):
                    with open(RESULT_FILE_ANSWERS,
                              'r', encoding='utf-8') as resultats:
                        resultats_reader = csv.DictReader(resultats)
                        for resultats_row in resultats_reader:
                            if (statistics_row[
                                   'GRUP'] == resultats_row['GRUP'] and
                               statistics_row[
                                   'OBJECTE'] == resultats_row['OBJECTE']):
                                if resultats_row['TUTORIA1-COMENTARI'] != '':
                                    if comments != '':
                                        comments += '\n'
                                    comments += resultats_row[
                                                    'TUTORIA1-COMENTARI'
                                                    ].replace('\n', ' ')
                                if resultats_row['TUTORIA2-COMENTARI'] != '':
                                    if comments != '':
                                        comments += '\n'
                                    comments += resultats_row[
                                                    'TUTORIA2-COMENTARI'
                                                    ].replace('\n', ' ')
                    report_dept_writer.writerow([statistics_row['GRUP']] +
                                                [statistics_row['OBJECTE']] +
                                                [statistics_row['ÍTEM 1']] +
                                                [statistics_row['ÍTEM 2']] +
                                                [statistics_row['ÍTEM 3']] +
                                                [statistics_row['ÍTEM 4']] +
                                                [comments])
        report_dept.close()

    report_centre = open(REPORT_FILE_CENTRE, 'w', encoding='utf-8')
    report_centre_writer = csv.writer(report_centre)
    # Encapçalats
    report_centre_writer.writerow(
                    ['DEPARTAMENT', 'GRUP', 'ÍTEM 1', 'ÍTEM 2', 'ÍTEM 3',
                     'ÍTEM 4', 'ÍTEM 5', 'ÍTEM 6', 'COMENTARI'])

    with open(RESULT_FILE_STATISTICS, 'r', encoding='utf-8') as statistics:
            statistics_reader = csv.DictReader(statistics)

            for statistics_row in statistics_reader:
                comments = ''
                if 'centre' in statistics_row['OBJECTE'].lower():
                    with open(RESULT_FILE_ANSWERS,
                              'r', encoding='utf-8') as resultats:
                        resultats_reader = csv.DictReader(resultats)
                        for resultats_row in resultats_reader:
                            if (statistics_row[
                                    'GRUP'] == resultats_row['GRUP'] and
                               statistics_row[
                                    'OBJECTE'] == resultats_row['OBJECTE']):
                                    if resultats_row['CENTRE-COMENTARI'] != '':
                                        if comments != '':
                                            comments += '\n'
                                        comments += resultats_row[
                                                         'CENTRE-COMENTARI'
                                                         ].replace('\n', ' ')

                        report_centre_writer.writerow(
                                        [get_departament(
                                          statistics_row['GRUP'])
                                         ] +
                                        [statistics_row['GRUP']] +
                                        [statistics_row['ÍTEM 1']] +
                                        [statistics_row['ÍTEM 2']] +
                                        [statistics_row['ÍTEM 3']] +
                                        [statistics_row['ÍTEM 4']] +
                                        [statistics_row['ÍTEM 5']] +
                                        [statistics_row['ÍTEM 6']] +
                                        [comments])
    report_centre.close()


def file_and_dir_remover(file_or_dir):
    """def file_and_dir_remover(file_or_dir)
    Descripció: Elimina fitxers i directoris sempre que existeixin i estiguin
                buits.
    Entrada:    Nom del fitxer o directori.
    Sortida:    Eliminació de fixter o directori.
    """
    try:
        os.remove(file_or_dir)
    except OSError as e:
        """
        Descarta els errors per fitxer o directori no existent, o directori no
        buit.
        """
        if e.errno != errno.ENOENT and e.errno != errno.ENOTEMPTY:
            raise


def setup_files():
    """def setup_files()
    Descripció: Elimina fitxers de sortida anteriors que puguin existir al
                directori.
    Entrada:    Cap.
    Sortida:    Elimina fixters anteriors.
    """
    file_and_dir_remover(RESULT_FILE_ERRORS)

    file_and_dir_remover(RESULT_FILE_ANSWERS)

    file_and_dir_remover(RESULT_FILE_STATISTICS)

    file_and_dir_remover(RESULT_FILE_STUDENTS_WITH_AVALUATED_MP)

    file_and_dir_remover(
        os.path.join(os.getcwd(), 'TmpFiles', TMP_FILE_ANSWERS))

    file_and_dir_remover(
        os.path.join(os.getcwd(), 'TmpFiles', TMP_FILE_ANSWERS))

    file_and_dir_remover(
        os.path.join(os.getcwd(), 'RcdFiles', RECORD_FILE_ERRORS))

    file_and_dir_remover(
        os.path.join(os.getcwd(), 'RcdFiles', RECORD_FILE_ANSWERS))

    file_and_dir_remover(
        os.path.join(os.getcwd(), 'RcdFiles', RECORD_FILE_ANSWERS))

    file_and_dir_remover(
        os.path.join(os.getcwd(), 'Informes', REPORT_FILE_CENTRE))

    file_and_dir_remover(
        os.path.join(os.getcwd(), 'Informes', REPORT_FILE_ADM))

    file_and_dir_remover(
        os.path.join(os.getcwd(), 'Informes', REPORT_FILE_INF))

    file_and_dir_remover(
        os.path.join(os.getcwd(), 'Informes', REPORT_FILE_INF))


def setup_options():
    """def setup_options(
                         OPTION_TMP_FILES,
                         OPTION_TMP_RECORDS,
                         OPTION_DUPLICATED_ANSWERS)
    Descripció: Demana a l'usuari que definieixi les opcions no establertes.
    Entrada:    Cap.
    Sortida:    Defineix les variables globals OPTION_TMP_FILES,
                OPTION_TMP_RECORDS, OPTION_DUPLICATED_ANSWERS en el seu cas.
    """
    global OPTION_TMP_FILES
    global OPTION_TMP_RECORDS
    global OPTION_DUPLICATED_ANSWERS
    global OPTION_REPORTS

    while OPTION_TMP_FILES != 0 and OPTION_TMP_FILES != 1:
        OPTION_TMP_FILES = answer_from_string_to_binary(input(
                    "Voleu conservar els arxius temporals? (s/n) ").lower())

    while OPTION_TMP_RECORDS != 0 and OPTION_TMP_RECORDS != 1:
        OPTION_TMP_RECORDS = answer_from_string_to_binary(input(
                    "Voleu conservar els registres? (s/n) ").lower())

    while OPTION_DUPLICATED_ANSWERS != 0 and OPTION_DUPLICATED_ANSWERS != 1:
        OPTION_DUPLICATED_ANSWERS = answer_from_string_to_binary(input(
                    "En cas de respostes duplicades, quina voleu conservar? \
                     (1: la primera, 2: l'última) ").lower())

    while OPTION_REPORTS != 0 and OPTION_REPORTS != 1:
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
                  os.path.join(os.getcwd(), TMP_FILE_ANSWERS),
                  os.path.join(os.getcwd(), 'TmpFiles', TMP_FILE_ANSWERS))
    else:  # Elimina arxius temporals
        file_and_dir_remover(TMP_FILE_ANSWERS)
        print('Arxius temporals eliminats.')

    if OPTION_TMP_RECORDS == 1:  # Conserva els registres
        # Crea subdirectori i mou dins registres
        if not os.path.exists(os.path.join(os.getcwd(), 'RcdFiles')):
            os.makedirs(os.path.join(os.getcwd(), 'RcdFiles'))
        os.rename(
                  os.path.join(os.getcwd(), RECORD_FILE_ERRORS),
                  os.path.join(os.getcwd(), 'RcdFiles', RECORD_FILE_ERRORS))
        os.rename(
                  os.path.join(os.getcwd(), RECORD_FILE_ANSWERS),
                  os.path.join(os.getcwd(), 'RcdFiles', RECORD_FILE_ANSWERS))
    else:  # Elimina registres
        file_and_dir_remover(RECORD_FILE_ERRORS)
        file_and_dir_remover(RECORD_FILE_ANSWERS)
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

    filter_invalid_responses()

    filter_duplicated_answers()

    generate_list_of_answers()
    final_result_files_arranger()

    generate_statistics()

    if OPTION_REPORTS == 1:
        generate_reports()
    del_tmp_and_reg_files()
