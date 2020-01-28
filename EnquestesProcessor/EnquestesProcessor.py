#!/usr/bin/python3.6
from core.terminal import *
from core.worker import *
import sys
import os

LOG_LEVEL = 2
    #   0 = no log
    #   1 = simple
    #   2 = detailed  

"""
    FPS 20200121: ideas      
        [X] Cambio de nombre: EnquestesProcessor_3.0.py o quizas eliminando el _3.0.py (quizas tenia sentido cuando era un solo fichero).
        [X] Mostrar info de bienvenida, con versión y copyright.        
        [X] Montar una opción verbose básica, para que muestre por consola lo que va haciendo.     
        [X] Carpetas input y output, donde dejar y recoger los ficheros.        
        [ ] Montar pruebas unitarias para comprobar que todo funciona (en carpeta test).
        [X] De ser posible, separar el core de la aplicación de consola (en carpeta core) para que se pueda usar como aplicación o como libreria        
        [ ] Para evitar las preguntas interactivas, se podrá especificar un fichero "yaml" como parámetro al invocar la app.
        [ ] Existe una manera de auto-instalar dependencias con pip?

    Info:   https://docs.python.org/3/tutorial/modules.html
            https://www.python.org/dev/peps/pep-0008/
            https://docs.python.org/3/library/unittest.html
"""

"""EnquestesProcessor_2.2:
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

Novetats respecte a la versió 2.1:
    - modificacions per afegir als informes de departament els comentaris dels
    estudiants de 2n curs que repeteixen alguna UF d'un MP de 1r curs i han
    estat fusionats amb el grup de 1r

Novetats respecte a la versió 2.2:
    - modificacions per incorporar MP impartits a un mateix grup per més d'un
      professor, i que a la nova versió del formulari són avaluats separadament
      per l'alumnat

Novetats respecte a la versió 2.3:
    - al llarg del procés les dades dels estudiants són reemplaçades per un
      identificador únic diferent en cada execució per garantitzar l'anonimat
      de les respostes al llarg de tot el procés
"""

def setup_options():
    """
    Descripció: Demana a l'usuari que definieixi les opcions no establertes.
    Entrada:    Cap.
    Sortida:    Defineix les variables globals OPTION_TMP_FILES,
                OPTION_TMP_RECORDS, OPTION_DUPLICATED_ANSWERS en el seu cas.
    """
    
    while worker.OPTION_TMP_FILES != 0 and worker.OPTION_TMP_FILES != 1:        
        terminal.writeln("Voleu conservar els arxius temporals? (s/n) ")
        worker.OPTION_TMP_FILES = answer_from_string_to_binary(input().lower())

    while worker.OPTION_TMP_RECORDS != 0 and worker.OPTION_TMP_RECORDS != 1:
        terminal.writeln("Voleu conservar els registres? (s/n) ")
        worker.OPTION_TMP_RECORDS = answer_from_string_to_binary(input().lower())

    while worker.OPTION_DUPLICATED_ANSWERS != 0 and worker.OPTION_DUPLICATED_ANSWERS != 1:
        terminal.writeln("En cas de respostes duplicades, quina voleu conservar? (1: la primera, 2: l'última) ")
        worker.OPTION_DUPLICATED_ANSWERS = answer_from_string_to_binary(input().lower())

    while worker.OPTION_REPORTS != 0 and worker.OPTION_REPORTS != 1:
        terminal.writeln("Desitja generar els informes? (s/n) ")
        worker.OPTION_REPORTS = answer_from_string_to_binary(input().lower())

def answer_from_string_to_binary(text):
    """
    Descripció: Converteix una string amb una 's'/'y' o amb una 'n' en un int 0 o 1 respectivament.
    Entrada:    string
    Sortida:    int
    Exemple:    'n' retorna 1
    """
    return 1 if text == 'y' or text == 's' or text == '2' else 0    

def offer_navigation_menu_for_troublesome_source_files(source_file):
    """
    Descripció: Ofereix a l'usuari l'opció de solucionar un problema amb els
                fitxers d'entrada i continuar amb l'execució del programa, o bé
                interrompre'l.
    Entrada:    String amb el nom del fitxer d'entrada.
    Sortida:    Executa una determinada funció segons l'opció triada.
    """    
    terminal.tab()
    terminal.breakline()
    terminal.writeln("Què voleu fer? Trieu una opció:", TerminalColors.UNDERLINE)

    terminal.tab()
    terminal.write("1. ", TerminalColors.CYAN)
    terminal.writeln("Solucionar el problema i seguir.")
    terminal.write("2. ", TerminalColors.CYAN)
    terminal.writeln("Voleu sortir del programa")
    terminal.untab()

    option = input()
    if option == "1":
        terminal.writeln("Si us plau, assegureu-vos de què heu solucionat el problema i premeu «Enter».")
        terminal.untab()

        input()
        if LOG_LEVEL > 0: terminal.write("Reintentant... ")
        check_source_file(source_file)

    elif option == "2":
        terminal.untab()
        exit()

    else:
        terminal.writeln("Si us plau, assegureu-vos de què heu solucionat una opció vàlida.")
        terminal.untab()
        offer_navigation_menu_for_troublesome_source_files(source_file)

def check_source_file(source_file):
    """
    Descripció: Comprova que el fitxer d'entrada existeix i no està buit.
    Entrada:    String amb el nom del fitxer d'entrada.
    Sortida:    Cap o crida a la funció
    """
    if not os.path.exists(source_file):
        error("No s'ha trobat a la carpeta el fitxer «%s»." % source_file)        
        offer_navigation_menu_for_troublesome_source_files(source_file)

    if os.path.getsize(source_file) == 0:
        print("\nEl fitxer «%s» està buit." % source_file)
        offer_navigation_menu_for_troublesome_source_files(source_file)

def catch_exception(ex):    
    error(str(ex))    
    sys.exit()

def succeed():
    if LOG_LEVEL > 0: 
        terminal.writeln("OK", TerminalColors.DARKGREEN)

def error(details):
    msg = ""
    if LOG_LEVEL > 0: msg += "ERROR"
    if LOG_LEVEL > 1: msg += ": " + details
    
    terminal.writeln(msg, TerminalColors.RED)

if __name__ == '__main__':
    global terminal
    global worker

    terminal = Terminal()  
    terminal.breakline()    
    terminal.write("Processador automàtic d'enquestes: ", TerminalColors.YELLOW)
    terminal.writeln("v3.0")
    terminal.write("Copyright © 2019: ", TerminalColors.YELLOW)
    terminal.writeln("INS Puig Castellar")
    terminal.write("Under the GPL v3.0 license: ", TerminalColors.YELLOW)
    terminal.writeln("https://github.com/ElPuig/Aplicacions-Gestio-Dades")
    
    terminal.breakline()        
    terminal.writeln("Iniciant el procés:")
    terminal.tab()    

    worker = Worker()
    if LOG_LEVEL > 0: terminal.write("Carregant configuració... ")
    try:
        #TODO: si no es diu el contrari, el programa pregunta, en cas contrari, es pot passar un fitxer yaml i llegeix d'aqui en comptes de preguntar
        #setup_options()
        succeed()
    except Exception as ex:
        catch_exception(ex)

    if LOG_LEVEL > 0: terminal.write("Netejant fitxers antics... ")
    try:
        worker.clean_files()
        succeed()
    except Exception as ex:
        catch_exception(ex)       
        
    if LOG_LEVEL > 0: terminal.write("Comprovant fitxers d'origen... ")
    try:
        check_source_file(worker.SOURCE_FILE_STUDENTS_WITH_MP)
        check_source_file(worker.SOURCE_FILE_STUDENT_ANSWERS)    
        succeed()
    except Exception as ex:
        catch_exception(ex)

    if LOG_LEVEL > 0: terminal.write("Filtrant respostes invàlides... ")
    try:        
        id_to_email_and_name_dict = worker.anonymize_answers()
        worker.filter_invalid_responses(id_to_email_and_name_dict)
        succeed()
    except Exception as ex:
       catch_exception(ex)

    if LOG_LEVEL > 0: terminal.write("Filtrant respostes duplicades... ")
    try:
        worker.filter_duplicated_answers()
        succeed()
    except Exception as ex:
        catch_exception(ex)

    if LOG_LEVEL > 0: terminal.write("Generant llistat de respostes... ")
    try:
        worker.generate_list_of_answers(id_to_email_and_name_dict)
        worker.final_result_files_arranger(id_to_email_and_name_dict)
        succeed()
    except Exception as ex:
        catch_exception(ex)

    if LOG_LEVEL > 0: terminal.write("Eliminant les dades sensibles... ")
    try:
        worker.final_result_files_arranger(id_to_email_and_name_dict)
        succeed()
    except Exception as ex:
        catch_exception(ex)

    if LOG_LEVEL > 0: terminal.write("Generant estadísitiques... ")
    try:
        merged_grup_mp_dict = worker.generate_statistics()
        succeed()
    except Exception as ex:
        catch_exception(ex)

    if worker.OPTION_REPORTS == 1:
        if LOG_LEVEL > 0: terminal.write("Generant informes... ")
        try:
            worker.generate_reports(**merged_grup_mp_dict)
            succeed()
        except Exception as ex:
            catch_exception(ex)

    if LOG_LEVEL > 0: terminal.write("Eliminant fitxers temporals... ")
    try:
        worker.clean_temp_files()
        succeed()
    except Exception as ex:
        catch_exception(ex)

    terminal.untab()
    terminal.breakline()