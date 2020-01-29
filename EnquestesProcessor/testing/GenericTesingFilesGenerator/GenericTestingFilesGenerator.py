#!/usr/bin/python3.6
# -*- coding: UTF-8 -*-

"""GenericTestingFilesGenerator_1.0:
Fitxers d'entrada
    - alumnes-mp.csv: llista dels alumnes matriculats a cada CF,
                      amb el seu nom complet, l'adreça Xeill, el cicle i curs,
                      i una «x» per cada MP al qual estigui matriculat
    - respostes.csv: descarregat des del formulari d'avaluació de Google Drive,
                     conté les valoracions dels alumnes
Fitxers de sortida:
    Dins del directori 'GenericFiles'
    - alumnes-mp.csv: llistat original amb el nom i email real dels estudiants
                      substituïts per altres genèrics
    - respostes.csv: llistat original al qual l'email real dels estudiants ha
                     estat substituït pel genèric, les valoracions numèriques
                     han estat reemplaçades per una altra aleatòria i els comentaris
                     intercanviats per un altre genèric
"""

import csv
import errno
import os
import random

COMPROMISED_SOURCE_FILE_STUDENTS_WITH_MP = 'alumnes-mp.csv'
COMPROMISED_SOURCE_FILE_STUDENT_ANSWERS = 'respostes.csv'
GENERIC_SOURCE_FILE_STUDENTS_WITH_MP = 'generic_alumnes-mp.csv'
GENERIC_SOURCE_FILE_STUDENT_ANSWERS = 'generic_respostes.csv'
OUTPUT_DIR = 'GenericFiles'
EMAIL_DOMAIN = '@elpuig.xeill.net'

def replace_info_in_students_information_file():
    """replace_info_in_students_information_file()
    Descripció: Reemplaça el nom i email real de cada estudiant per uns altres genèrics.
    Entrada:    Cap.
    Sortida:    Diccionari old_email_to_new_email_dict amb l'email real a clau, i el
                genèric com a valor.
    """
    old_email_to_new_email_dict = {}

    with open(GENERIC_SOURCE_FILE_STUDENTS_WITH_MP, 'w', encoding='utf-8') as generic_alumnes:
        generic_alumnes_writer = csv.writer(generic_alumnes)

        with open(COMPROMISED_SOURCE_FILE_STUDENTS_WITH_MP, 'r', encoding='utf-8') as compromised_alumnes:
            compromised_alumnes_reader = csv.reader(compromised_alumnes)
            generic_alumnes_writer.writerow(next(compromised_alumnes_reader))

            alumne_num = 1
            for alumne_row in compromised_alumnes_reader:
                compromised_email = alumne_row[1]
                generic_student_name = generic_student_name_generator(alumne_num)
                generic_student_email = generic_student_email_generator(alumne_num)

                old_email_to_new_email_dict[compromised_email] = generic_student_email
              
                generic_alumnes_writer.writerow([generic_student_name] + [generic_student_email] +
                                                alumne_row[2:])
                alumne_num += 1
    
    return old_email_to_new_email_dict

def replace_info_in_students_responses_file(**old_email_to_new_email_dict):
    """replace_info_in_students_responses_file(**old_email_to_new_email_dict)
    Descripció: Reemplaça l'email real dels estudiants amb l'equivalent genèric, les valoracions
                numèriquesvper altres aleatòries i els comentaris per altres genèrics.
    Entrada:    Diccionari old_email_to_new_email_dict amb l'email real a clau, i el
                genèric com a valor.
    Sortida:    Cap.
    """
    with open(GENERIC_SOURCE_FILE_STUDENT_ANSWERS, 'w', encoding='utf-8') as generic_respostes:
        generic_respostes_writer = csv.writer(generic_respostes)

        with open(COMPROMISED_SOURCE_FILE_STUDENT_ANSWERS, 'r', encoding='utf-8') as compromised_respostes:
            respostes_reader = csv.reader(compromised_respostes)
            generic_respostes_writer.writerow(next(respostes_reader))
            
            for respostes_row in respostes_reader:
                r_compromised_email = respostes_row[1]
                r_generic_email = old_email_to_new_email_dict.get(r_compromised_email)

                evaluated_item = extract_evaluated_item(*respostes_row[3:8])

                random_evaluation = random_evaluation_generator(evaluated_item, *respostes_row[8:])

                generic_respostes_writer.writerow([respostes_row[0]] + [r_generic_email] + [respostes_row[2]] +
                                                  respostes_row[3:8] + random_evaluation)


def generic_student_name_generator(alumne_num):
    """generic_student_name_generator(alumne_num)
    Descripció: Retorna un nom genèric per substituir el nom real dels estudiants.
    Entrada:    Número d'alumne processat.
    Sortida:    Nom genèric.
    """
    generic_name = 'Alumne Núm. ' + str(alumne_num)

    return generic_name


def generic_student_email_generator(alumne_num):
    """generic_student_email_generator(alumne_num)
    Descripció: Retorna un email genèric per substituir l'email real dels estudiants.
    Entrada:    Número d'alumne processat.
    Sortida:    Email genèric.
    """
    generic_student_email = 'alumnenum' + str(alumne_num) + EMAIL_DOMAIN

    return generic_student_email


def extract_evaluated_item(*compromised_row_items):
    """extract_evaluated_item(*compromised_row_items)
    Descripció: Retorna quin ha estat l'ítem avaluat.
    Entrada:    Llistat amb aquelles columnes de la resposta que contenen la selecció de l'ítem
                a avaluar.
    Sortida:    Ítem avaluat.
    """
    compromised_row_items = list(compromised_row_items)
    
    compromised_row_items_index = 0
    for item in compromised_row_items:
        if (item != ''):
            return item
        else:
            pass
            compromised_row_items_index += 1


def generic_student_comment_generator(evaluated_item):
    """generic_student_comment_generator(evaluated_item)
    Descripció: Retorna un comentari genèric per substituir un comentari real d'un estudiant.
    Entrada:    Ítem al qual es refereix el comentari.
    Sortida:    Comentari genèric.
    """
    generic_student_comment = "Comentari genèric sobre: " + str(evaluated_item)

    return generic_student_comment


def random_evaluation_generator(evaluated_item, *compromised_row_evaluations):
    """random_evaluation_generator(evaluated_item, *compromised_row_evaluations)
    Descripció: Retorna unes valoracions i comentaris aleatoris per reemplaçar els reals.
    Entrada:    Llistat amb aquelles columnes de la resposta que contenen les valoracions
                i comentaris.
    Sortida:    Llistat amb puntuacions aleatòries i, en el seu cas, un nou comentari
                genèric.
    """
    compromised_row_evaluations = list(compromised_row_evaluations)

    generic_respostes_row = []
    for item in compromised_row_evaluations:
        if (item == ''):
            generic_respostes_row.append('')
        elif (item.isdigit()):
            new_mark = str(random.randrange(1, 10))
            generic_respostes_row.append(new_mark)
        else:
            new_comment = generic_student_comment_generator(evaluated_item)
            generic_respostes_row.append(new_comment)

    return generic_respostes_row


def deliver_final_files():
    """deliver_final_files()
    Descripció: Crea una carpeta pels fitxers de sortida del script i reanomena aquests
                igual que els originals perquè puguin ser processats correctament pel
                script EnquestesProcessor.py.
    Entrada:    Cap.
    Sortida:    Cap.
    """
    if not os.path.exists(os.path.join(os.getcwd(), OUTPUT_DIR)):
        os.makedirs(os.path.join(os.getcwd(), OUTPUT_DIR))
    os.rename(
            os.path.join(os.getcwd(), GENERIC_SOURCE_FILE_STUDENTS_WITH_MP),
            os.path.join(os.getcwd(), OUTPUT_DIR, COMPROMISED_SOURCE_FILE_STUDENTS_WITH_MP))
    os.rename(
            os.path.join(os.getcwd(), GENERIC_SOURCE_FILE_STUDENT_ANSWERS),
            os.path.join(os.getcwd(), OUTPUT_DIR, COMPROMISED_SOURCE_FILE_STUDENT_ANSWERS))


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
    file_and_dir_remover(
        os.path.join(os.getcwd(), OUTPUT_DIR, COMPROMISED_SOURCE_FILE_STUDENTS_WITH_MP))
    file_and_dir_remover(
        os.path.join(os.getcwd(), OUTPUT_DIR, COMPROMISED_SOURCE_FILE_STUDENT_ANSWERS))


if __name__ == '__main__':
    setup_files()

    old_email_to_new_email_dict = replace_info_in_students_information_file()

    replace_info_in_students_responses_file(**old_email_to_new_email_dict)

    deliver_final_files()
