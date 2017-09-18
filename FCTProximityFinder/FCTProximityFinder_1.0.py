#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""FCTProximityFinder1.0.py
Fitxers d'entrada:
    - alumnes.csv:
        * CSV amb la fitxa de l'alumne amb els camps:
            - NOM
            - COGNOMS
            - ADREÇA
            - POBLACIÓ
        * el fitxer ha de portar capçalera
    - empreses.csv:
        * CSV amb la informació de les empreses d'FCT amb els camps:
            - Empresa
            - Adreça Empresa
            - Codi Postal Empresa
            - Municipi/Localitat Empresa
"""

import csv
import geopy.distance
from googlemaps import Client as GoogleMaps
import os
import re

ADDRESS_NOT_FOUND_CODE = '999999'
# API_KEY vinculada al compte fctproximityfinder@elpuig.xeill.net
# API_KEY = 'AIzaSyB36Mt-0-bO9MPVfPiUQqBrDoeiE8JHweE'
API_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
SOURCE_FILE_COMPANIES = 'empreses.csv'
SOURCE_FILE_STUDENTS = 'alumnes.csv'


def prompt_mode():
    """def prompt_mode()
    Descripció: Demana a l'usuari en quin dels 3 modes possibles vol executar
                el programa.
    Entrada:    Cap.
    Sortida:    Executa un dels modes del programa en funció de l'opció triada.
    """
    global mode
    mode = ""

    mode = input(
                 "\nQuè voleu fer?\n" +
                 "\n\t1. Trobar els estudiants amb domicili més a prop d'una "
                 "empresa" +
                 "\n\t2. Trobar les empreses més a prop al domicili d'un "
                 "estudiant" +
                 "\n\t3. Trobar les empreses i estudiants amb problemes de "
                 "geolocalització" +
                 "\nTrieu una opció (1/2/3): ")

    if mode == "1":
        print(
              "Heu triat trobar els estudiants amb domicili més a prop "
              "d'una empresa.")
        sort_students_near_company()
    elif mode == "2":
        print(
              "Heu triat trobar les empreses més a prop al domicili d'un "
              "estudiant.")
        sort_companies_near_student()
    elif mode == "3":
        print("Heu triat Trobar les empreses i estudiants amb problemes de "
              "geolocalització.")
        prompt_non_locatable_addresses_search()
    else:
        print("\nATENCIÓ: Si us plau, trieu «1», «2» o «3».")
        prompt_mode()


def sort_students_near_company():
    """def sort_students_near_company()
    Descripció: Retorna el llistat d'estudiants amb domicili més a prop de
                l'empresa triada.
    Entrada:    Cap.
    Sortida:    Imprimeix llistat.
    """
    company = choose_company()

    company_address = get_company_address(company)

    company_lat_lng = get_location(simplify_address(company_address))

    if company_lat_lng == ADDRESS_NOT_FOUND_CODE:
        print("No s'ha pogut trobar al mapa l'adreça de l'empresa")
        offer_navigation_menu()

    else:
        print(
              "\nSi us plau, espereu uns segons: "
              "s'està realitzant la cerca...")
        students_dict = {}
        with open(SOURCE_FILE_STUDENTS, 'r', encoding='utf-8') as students:
            students_reader = csv.DictReader(students)

            for row in students_reader:
                student_name = row["COGNOMS"] + ", " + row["NOM"]
                student_address = simplify_address(
                                                   row["ADREÇA"] +
                                                   " " +
                                                   row["CP"].zfill(5) +
                                                   " " +
                                                   row["POBLACIÓ"])

                student_lat_lng = get_location(student_address)
                if student_lat_lng == ADDRESS_NOT_FOUND_CODE:
                    students_dict[student_name] = student_lat_lng
                else:
                    distance = geopy.distance.vincenty(
                                                       company_lat_lng,
                                                       student_lat_lng
                                                       ).km

                    students_dict[student_name] = distance

        result_list = sorted(students_dict.items(), key=lambda x: float(x[1]))

        print(
              "\nAQUESTS SÓN ELS ESTUDIANTS AMB DOMICILI MÉS PROPER "
              "A L'EMPRESA:")
        i = 1
        for elem in result_list:
            if elem[1] == ADDRESS_NOT_FOUND_CODE:
                print("--. " + elem[0] + ": ADREÇA NO TROBADA AL MAPA")
            else:
                print(
                      str(i).zfill(2) + ". " +
                      elem[0] + ": " +
                      str(elem[1]) + " km.")
                i += 1

        offer_navigation_menu()


def choose_company():
    """def choose_company()
    Descripció: Ofereix a l'usuari l'opció d'escollir l'empresa.
    Entrada:    Cap.
    Sortida:    String amb el nom de l'empresa.
    """
    search_criteria = prompt_search_criteria()

    companies_list = []
    with open(SOURCE_FILE_COMPANIES, 'r', encoding='utf-8') as companies:
        file_dialect = csv.Sniffer().sniff(companies.read(), delimiters=";,\t")
        companies.seek(0)
        companies_reader = csv.DictReader(companies, dialect=file_dialect)

        for row in companies_reader:
            company_name = remove_id_from_company_name(row["Empresa"])
            if re.search('[a-zA-Z0-9]', search_criteria):
                if normalize_char(search_criteria) in\
                                      normalize_char(company_name):
                    companies_list.append(company_name)
            else:
                companies_list.append(company_name)

    if not companies_list:
        print("\nLa teva cerca no ha generat resultats.")
        sort_students_near_company()
    else:
        companies_list = sorted(companies_list)

        i = 1
        for company in companies_list:
            print(str(i) + ". " + company)
            i += 1

        selected_company = prompt_object_selection(*companies_list)
        print("Heu triat " + selected_company)

    return selected_company


def get_company_address(company):
    """def get_company_address(company)
    Descripció: Retorna l'adreça de l'empresa indicada.
    Entrada:    String amb el nom de l'empresa.
    Sortida:    String amb l'adreça de l'empresa.
    """
    with open(SOURCE_FILE_COMPANIES, 'r', encoding='utf-8') as companies:
        file_dialect = csv.Sniffer().sniff(companies.read(), delimiters=";,\t")
        companies.seek(0)
        companies_reader = csv.DictReader(companies, dialect=file_dialect)

        for row in companies_reader:
            company_name = remove_id_from_company_name(row["Empresa"])
            company_address = (simplify_address(
                                          row["Adreça Empresa"] +
                                          " " +
                                          row["Codi Postal Empresa"].zfill(5) +
                                          " " +
                                          row["Municipi/Localitat Empresa"]))
            if company_name == company:
                return company_address


def sort_companies_near_student():
    """def sort_companies_near_student()
    Descripció: Retorna el llistat d'empreses més a prop del domicili
                de l'estudiant triat.
    Entrada:    Cap.
    Sortida:    Imprimeix llistat.
    """
    student = choose_student()

    student_address = get_student_address(student)

    student_lat_lng = get_location(simplify_address(student_address))

    if student_lat_lng == ADDRESS_NOT_FOUND_CODE:
        print("No s'ha pogut trobar al mapa el domicili de l'estudiant")
        offer_navigation_menu()
    else:
        print(
              "\nSi us plau, espereu uns segons: "
              "s'està realitzant la cerca...")
        companies_dict = {}
        with open(SOURCE_FILE_COMPANIES, 'r', encoding='utf-8') as companies:
            file_dialect = csv.Sniffer().sniff(
                                               companies.read(),
                                               delimiters=";,\t")
            companies.seek(0)
            companies_reader = csv.DictReader(companies, dialect=file_dialect)

            for row in companies_reader:
                company_name = remove_id_from_company_name(row["Empresa"])
                company_address = (simplify_address(
                                          row["Adreça Empresa"] +
                                          " " +
                                          row["Codi Postal Empresa"].zfill(5) +
                                          " " +
                                          row["Municipi/Localitat Empresa"]))

                company_lat_lng = get_location(company_address)
                if company_lat_lng == ADDRESS_NOT_FOUND_CODE:
                    companies_dict[company_name] = company_lat_lng
                else:
                    distance = geopy.distance.vincenty(
                                                       student_lat_lng,
                                                       company_lat_lng
                                                       ).km

                    companies_dict[company_name] = distance

        result_list = sorted(companies_dict.items(), key=lambda x: float(x[1]))

        print(
              "\nAQUESTES SÓN LES EMPRESES MÉS PROPERES AL DOMICILI "
              "DE L'ESTUDIANT:")
        i = 1
        for elem in result_list:
            if elem[1] == ADDRESS_NOT_FOUND_CODE:
                print("--. " + elem[0] + ": ADREÇA NO TROBADA AL MAPA")
            else:
                print(
                      str(i).zfill(2) + ". " +
                      elem[0] + ": " +
                      str(elem[1]) + " km.")
                i += 1

        offer_navigation_menu()


def choose_student():
    """def choose_student()
    Descripció: Ofereix a l'usuari l'opció d'escollir l'estudiant.
    Entrada:    Cap.
    Sortida:    String amb el nom complet de l'estudiant.
    """
    search_criteria = prompt_search_criteria()

    students_list = []
    with open(SOURCE_FILE_STUDENTS, 'r', encoding='utf-8') as students:
        students_reader = csv.DictReader(students)

        for row in students_reader:
            student_name = row["COGNOMS"] + ", " + row["NOM"]
            if re.search('[a-zA-Z0-9]', search_criteria):
                if normalize_char(search_criteria) in\
                                      normalize_char(student_name):
                    students_list.append(student_name)
            else:
                students_list.append(student_name)

    if not students_list:
        print("\nLa teva cerca no ha generat resultats.")
        sort_companies_near_student()
    else:
        students_list = sorted(students_list)

        i = 1
        for student in students_list:
            print(str(i) + ". " + student)
            i += 1

        selected_student = prompt_object_selection(*students_list)
        print("Heu triat " + selected_student)

    return selected_student


def get_student_address(student):
    """def get_student_address(company)
    Descripció: Retorna l'adreça de l'etudiant indicat.
    Entrada:    String amb el nom de l'estudiant.
    Sortida:    String amb el domicili de l'estudiant.
    """
    with open(SOURCE_FILE_STUDENTS, 'r', encoding='utf-8') as students:
        students_reader = csv.DictReader(students)

        for row in students_reader:
            student_name = row["COGNOMS"] + ", " + row["NOM"]
            student_address = simplify_address(
                                               row["ADREÇA"] +
                                               " " +
                                               row["CP"].zfill(5) +
                                               " " +
                                               row["POBLACIÓ"])
            if student_name == student:
                return student_address


def prompt_non_locatable_addresses_search():
    """def prompt_non_locatable_addresses_search()
    Descripció: Demana a l'usuari quin tipus de cerca d'adreces no
                localitzables vol portar a cap.
    Entrada:    Cap.
    Sortida:    Executa un dels modes de cerca en funció de l'opció triada.
    """
    option = input(
                 "\nQuè voleu fer?\n" +
                 "\t1. Imprimir el llistat d'empreses i estudiants amb "
                 "problemes de geolocalització\n" +
                 "\t2. Buscar per nom empreses i estudiants amb "
                 "problemes de geolocalització\n" +
                 "Trieu una opció (1/2): ")

    if option == "1":
        print(
              "\nSi us plau, espereu uns segons: "
              "s'està realitzant la cerca...")
        get_every_non_locatable_company()
        get_every_non_locatable_student()
    elif option == "2":
        search_criteria = prompt_search_criteria()
        print(
              "\nSi us plau, espereu uns segons: "
              "s'està realitzant la cerca...")
        if search_criteria == "":
            get_every_non_locatable_company()
            get_every_non_locatable_student()
        else:
            get_non_locatable_companies_on_demand(search_criteria)
            get_non_locatable_students_on_demand(search_criteria)

    else:
        print("\nATENCIÓ: Si us plau, trieu «1» o «2».")
        prompt_non_locatable_addresses_search()

    offer_navigation_menu()


def get_every_non_locatable_company():
    """def get_every_non_locatable_company()
    Descripció: Retorna el nom i adreça de totes les empreses amb domicili
                no geolocalitzable.
    Entrada:    Cap.
    Sortida:    Imprimeix llistat.
    """
    non_locatable_companies = {}
    with open(SOURCE_FILE_COMPANIES, 'r', encoding='utf-8') as companies:
        file_dialect = csv.Sniffer().sniff(companies.read(), delimiters=";,\t")
        companies.seek(0)
        companies_reader = csv.DictReader(companies, dialect=file_dialect)

        for row in companies_reader:
            company_name = remove_id_from_company_name(row["Empresa"])
            company_address = (simplify_address(
                                          row["Adreça Empresa"] +
                                          " " +
                                          row["Codi Postal Empresa"].zfill(5) +
                                          " " +
                                          row["Municipi/Localitat Empresa"]))
            if get_location(company_address) == ADDRESS_NOT_FOUND_CODE:
                non_locatable_companies[company_name] = company_address

    if non_locatable_companies:
        print("\nEMPRESES:")
        i = 1
        for company in sorted(list(non_locatable_companies.keys())):
            print (str(i).zfill(2) + ". " +
                   company + ": " +
                   non_locatable_companies.get(company))
            i += 1
    else:
        print("\nNo hi han empreses amb problemes de geolocalització.")


def get_every_non_locatable_student():
    """def get_every_non_locatable_student()
    Descripció: Retorna el nom i domicili de tots els estudiants amb domicili
                no geolocalitzable.
    Entrada:    Cap.
    Sortida:    Imprimeix llistat.
    """
    non_locatable_students = {}
    with open(SOURCE_FILE_STUDENTS, 'r', encoding='utf-8') as students:
        students_reader = csv.DictReader(students)

        for row in students_reader:
            student_name = row["COGNOMS"] + ", " + row["NOM"]
            student_address = simplify_address(
                                   row["ADREÇA"] +
                                   " " +
                                   row["CP"].zfill(5) +
                                   " " +
                                   row["POBLACIÓ"])
            if get_location(student_address) == ADDRESS_NOT_FOUND_CODE:
                non_locatable_students[student_name] = student_address

    if non_locatable_students:
        print("\nESTUDIANTS:")
        i = 1
        for student in sorted(list(non_locatable_students.keys())):
            print (str(i).zfill(2) + ". " +
                   student + ": " +
                   non_locatable_students.get(student))
            i += 1
    else:
        print("\nNo hi han domicilis d'estudiant amb problemes de"
              "geolocalització.")


def get_non_locatable_companies_on_demand(search_criteria):
    """def get_non_locatable_companies_on_demand(search_criteria)
    Descripció: Retorna el nom i adreça de les empreses amb domicili
                no geolocalitzable que compleixin el criteri de cerca indicat
                per l'usuari, així com el nom de les empreses sense problemes
                de geolocalització que compleixein el criteri de cerca indicat.
    Entrada:    String amb el criteri de cerca.
    Sortida:    Imprimeix llistats.
    """
    locatable_companies = []
    non_locatable_companies = {}
    with open(SOURCE_FILE_COMPANIES, 'r', encoding='utf-8') as companies:
        file_dialect = csv.Sniffer().sniff(companies.read(), delimiters=";,\t")
        companies.seek(0)
        companies_reader = csv.DictReader(companies, dialect=file_dialect)

        for row in companies_reader:
            company_name = remove_id_from_company_name(row["Empresa"])
            company_address = (simplify_address(
                                          row["Adreça Empresa"] +
                                          " " +
                                          row["Codi Postal Empresa"].zfill(5) +
                                          " " +
                                          row["Municipi/Localitat Empresa"]))
            if normalize_char(search_criteria) in normalize_char(company_name):
                if get_location(company_address) == ADDRESS_NOT_FOUND_CODE:
                    non_locatable_companies[company_name] = company_address
                else:
                    locatable_companies.append(company_name)

    print("\nEMPRESES:")
    if locatable_companies:
        print("\nLes següents empreses són geolocalitzables:")
        i = 1
        for company in sorted(locatable_companies):
            print (str(i).zfill(2) + ". " + company)
            i += 1

    if non_locatable_companies:
        print("\nLES SEGÜENTS EMPRESES NO SÓN GEOLOCALITZABLES:")
        i = 1
        for company in sorted(list(non_locatable_companies.keys())):
            print (str(i).zfill(2) + ". " +
                   company + ": " +
                   non_locatable_companies.get(company))
            i += 1
    else:
        print("\nTotes les empreses que compleixen els criteris "
              "de cerca són geolocalitzables.")


def get_non_locatable_students_on_demand(search_criteria):
    """def get_non_locatable_students_on_demand(search_criteria)
    Descripció: Retorna el nom i adreça dels estudiants amb domicili
                no geolocalitzable que compleixin el criteri de cerca indicat
                per l'usuari, així con el nom dels estudiants amb domicili
                sense problemes de geolocalització que compleixein el criteri
                de cerca indicat.
    Entrada:    String amb el criteri de cerca.
    Sortida:    Imprimeix llistats.
    """
    locatable_students = []
    non_locatable_students = {}
    with open(SOURCE_FILE_STUDENTS, 'r', encoding='utf-8') as students:
        students_reader = csv.DictReader(students)

        for row in students_reader:
            student_name = row["COGNOMS"] + ", " + row["NOM"]
            student_address = simplify_address(
                                   row["ADREÇA"] +
                                   " " +
                                   row["CP"].zfill(5) +
                                   " " +
                                   row["POBLACIÓ"])
            if normalize_char(search_criteria) in normalize_char(student_name):
                if get_location(student_address) == ADDRESS_NOT_FOUND_CODE:
                    non_locatable_students[student_name] = student_address
                else:
                    locatable_students.append(student_name)

    print("\nESTUDIANTS:")
    if locatable_students:
        print("\nEls domicilis dels següents estudiants són geolocalitzables:")
        i = 1
        for student in sorted(locatable_students):
            print (str(i).zfill(2) + ". " + student)
            i += 1

    if non_locatable_students:
        print("\nELS DOMICILIS DELS SEGÜENTS ESTUDIANTS NO SÓN "
              "GEOLOCALITZABLES:")
        i = 1
        for student in sorted(list(non_locatable_students.keys())):
            print (str(i).zfill(2) + ". " +
                   student + ": " +
                   non_locatable_students.get(student))
            i += 1
    else:
        print("\nTots els domicilis dels estudiants que compleixen els "
              "criteris de cerca són geolocalitzables.")


def prompt_search_criteria():
    """def prompt_search_criteria()
    Descripció: Demana a l'usuari que introdueixi el nom parcial d'una empesa
                o estudiant.
    Entrada:    Cap.
    Sortida:    String introduït per l'usuari.
    """
    global mode

    if mode == "1":
        search_object = "l'empresa"
    if mode == "2":
        search_object = "l'estudiant"
    if mode == "3":
        search_object = "l'empresa i/o l'estudiant"

    search_criteria = input(
                       ("\nIntroduïu part del nom de " +
                        search_object +
                        " o deixeu-lo en blanc per mostrar el llistat "
                        "sencer: "))

    return search_criteria


def prompt_object_selection(*results_list):
    """def prompt_object_selection(*results_list)
    Descripció: Demana a l'usuari que triï una opció del llistat de resultats
                imprès inserint el seu nombre d'ordre.
    Entrada:    Llista de resultats.
    Sortida:    String amb el resultat de l'opció triada.
    """
    global mode

    option = input(
                   ("\nInseriu el nombre corresponent a la vostra opció "
                    "o premeu «Enter» per tornar enrere: "))

    if option == "":
        offer_navigation_menu()
    elif int(option) > len(results_list) or\
            int(option) <= 0 or\
            option.isdigit() is False:
        print("\nATENCIÓ: El nombre triat no és a la llista.")
        offer_navigation_menu()
    else:
        return results_list[int(option)-1]


def normalize_char(s):
    """def normalize_char(s)
    Descripció: Reemplaça els caràcters que no pertanyen al codi ASCII.
    Entrada:    String amb caràctes no pertanyents al codi ASCII.
    Sortida:    String amb tots els caràctes pertanyents al codi ASCII.
    Exemple:    "àñ-çü,í" retorna "ancui"
    """
    letter_equivalences = [("à", "a"), ("á", "a"), ("ä", "a"), ("â", "a"),
                           ("ã", "a"), ("å", "a"),
                           ("ç", "c"),
                           ("è", "e"), ("é", "e"), ("ë", "e"), ("ê", "e"),
                           ("ì", "i"), ("í", "i"), ("ï", "i"), ("î", "i"),
                           ("¡", "i"),
                           ("l·l", "ll"), ("ñ", "n"),
                           ("ò", "o"), ("ó", "o"), ("ö", "o"), ("ô", "o"),
                           ("ù", "u"), ("ú", "u"), ("ü", "u"), ("û", "u"),
                           (",", ""), (".", ""), ("-", ""),
                           ("º", ""), ("ª", ""),
                           ("€", ""),
                           ("·", ""), ("”", ""), ("  ", " ")]

    for k, v in letter_equivalences:
        s = s.lower().replace(k, v)

    return s


def get_location(address):
    """def get_location(address)
    Descripció: Cerca la latitud i longitud d'un adreça.
    Entrada:    String amb l'adreça.
    Sortida:    String amb la latitud i longitud o codi d'error
                segons el resultat de la cerca.
    """
    try:
        gmaps = GoogleMaps(API_KEY)
        geocode_result = gmaps.geocode(address)[0]
        lat = geocode_result["geometry"]["location"]['lat']
        lng = geocode_result["geometry"]["location"]['lng']
        address_lat_lng = (str(lat) + ", " + str(lng))
        return address_lat_lng
    except IndexError:
        return ADDRESS_NOT_FOUND_CODE


def remove_id_from_company_name(company_with_nif):
    """def remove_id_from_company_name(company_with_nif)
    Descripció: Elimina el NIF de l'empresa del nom.
    Entrada:    String amb el nom de l'empresa i el DNI.
    Sortida:    String amb el nom de l'empresa sense espais addicionals.
    Exemple:    "GESDOCUMENT Y GESTION SA (A59053355)" retorna
                "GESDOCUMENT Y GESTION SA"
    """
    return company_with_nif.split("(")[0].strip()


def simplify_address(address):
    """def simplify_address(address)
    Descripció: Redueix les adreces al nom de la via, el nombre, CP i localitat
                per evitar problemes a les cerques.
    Entrada:    String amb l'adreça completa.
    Sortida:    String sense els nombres seguits de lletra.
    Exemple:    "CR Milà i Fontanals 85 1er 1era 8922 Santa Coloma de Gramenet"
                retorna "CR Milà i Fontanals 85 8922 Santa Coloma de Gramenet"
    """
    address = re.sub(r'(^[a-zA-ZÀ-ÿ ,]+ [0-9-/sn ]* )'
                     '([a-zA-ZÀ-ÿ0-9 -_,]*)'
                     '(\d\d\d\d\d[a-zA-ZÀ-ÿ ]+$)',
                     r'\1\3',
                     address)
    return address


def offer_navigation_menu():
    """def offer_navigation_menu()
    Descripció: Ofereix a l'usuari diferents l'opció de realitzar una nova
                cerca, tornar al menú principal o sortir del programa.
    Entrada:    Cap.
    Sortida:    Executa una determinada funció segons l'opció triada.
    """
    global mode

    option = input(
                   "\n" +
                   ("Inseriu «0» per a fer una nova cerca, "
                    "«*» per a tornar al menú principal "
                    "o «@» per a sortir del programa: "))

    if option == "0":
        if mode == "1":
            sort_students_near_company()
        if mode == "2":
            sort_companies_near_student()
        if mode == "3":
            prompt_non_locatable_addresses_search()
    elif option == "*":
        prompt_mode()
    elif option == "@":
        exit()
    else:
        print("\nATENCIÓ: Si us plau, trieu «0», «*» o «@».")
        offer_navigation_menu()


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
    check_source_file(SOURCE_FILE_COMPANIES)
    check_source_file(SOURCE_FILE_STUDENTS)
    prompt_mode()
