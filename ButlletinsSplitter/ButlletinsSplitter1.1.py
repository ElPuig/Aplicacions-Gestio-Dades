#!/usr/bin/python
# -*- coding: utf-8 -*-

"""ButlletinsSplitter1.1.py
Fitxer d'entrada:     Fitxer PDF amb els butlletins de notes d'un grup sencer
                      amb el nom «informe.pdf».
Fitxers de sortida:   Un fitxer PDF per cada alumne amb el seu butlletí i
                      reanomenat amb el seu nom.
"""

import os
import PyPDF2

SOURCE_FILE_SAGA = "informe.pdf"


def main():
    butlletins = open(SOURCE_FILE_SAGA, 'rb')
    butlletins_reader = PyPDF2.PdfFileReader(butlletins)

    total_pages = butlletins_reader.getNumPages()
    page_num = 0
    current_student = None

    while page_num < total_pages:
        if current_student is None:
            page_text = butlletins_reader.getPage(page_num)
            page_text_string = page_text.extractText()
            current_student = get_student_name(page_text_string)

        student = current_student
        output_file = student + '.pdf'
        output_writer = PyPDF2.PdfFileWriter()

        while current_student == student and current_student is not None:
            output_writer.addPage(page_text)

            page_num += 1

            if page_num < total_pages:
                page_text = butlletins_reader.getPage(page_num)
                page_text_string = page_text.extractText()
                current_student = get_student_name(page_text_string)

                # Blank page
                if current_student is None:
                    page_num += 1

            with open(output_file, 'wb') as output_stream:
                output_writer.write(output_stream)

    butlletins.close()


def get_student_name(s):
    """def get_student_name(s)
    Descripció: Troba el nom de l'alumne al text d'una pàgina del butlletí de
                notes passat com a string.
    Entrada:    String.
    Sortida:    String amb el nom de l'alumne si la pàgina no està buida;
            None en cas contrari.
    """

    try:
        # Get student's name
        """ start: 'Grup' (al text sempre davant del nom de l'alumne
                           i el seu DNI)
            end:   'CFP' (al text sempre darrere del nom de l'alumne
                          i el seu DNI)
        """
        start_index = s.index('Grup') + len('Grup')
        end_index = s.index('CFP')
        # Ignore ID's last char
        student_with_id = s[start_index:end_index][:-1]

        # Remove ID from substring (every number and/or
        #                           letter followed by a number)
        student = ''.join(l for i, l in enumerate(student_with_id)
                          if not l.isdigit() and not
                          (l.isupper() and student_with_id[i+1].isdigit()))

        return student
    except:  # Blank page
        return None


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
    main()
