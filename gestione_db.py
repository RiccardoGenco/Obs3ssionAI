import sqlite3
import json
import csv
import os
from pathlib import Path

DB_PATH = "database.sqlite"

def inizializza_db():
    """Crea il database se non esiste"""
    conn = sqlite3.connect(DB_PATH)
    conn.close()
    return f"Database inizializzato in {DB_PATH}"

def esegui_query(query, parametri=None):
    """Esegue una query SQL e restituisce i risultati"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if parametri:
            cursor.execute(query, parametri)
        else:
            cursor.execute(query)
            
        if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
            # Per query di selezione, restituisce i risultati
            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()
            # Converte i risultati in lista di dizionari
            results_list = [dict(zip(columns, row)) for row in results]
            conn.close()
            return {"success": True, "data": results_list}
        else:
            # Per query di modifica, fa il commit e restituisce il numero di righe modificate
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            return {"success": True, "affected_rows": affected_rows}
            
    except sqlite3.Error as e:
        return {"success": False, "error": str(e)}

def crea_tabella(nome_tabella, definizione_colonne):
    """
    Crea una nuova tabella nel database
    :param nome_tabella: Nome della tabella da creare
    :param definizione_colonne: Lista di definizioni delle colonne (es. ["id INTEGER PRIMARY KEY", "nome TEXT"])
    """
    try:
        query = f"CREATE TABLE IF NOT EXISTS {nome_tabella} ({', '.join(definizione_colonne)})"
        return esegui_query(query)
    except Exception as e:
        return {"success": False, "error": str(e)}

def inserisci_dati(nome_tabella, dati):
    """
    Inserisce dati in una tabella
    :param nome_tabella: Nome della tabella
    :param dati: Dizionario con i dati da inserire {colonna: valore}
    """
    try:
        colonne = list(dati.keys())
        valori = list(dati.values())
        placeholders = ','.join(['?' for _ in valori])
        
        query = f"INSERT INTO {nome_tabella} ({','.join(colonne)}) VALUES ({placeholders})"
        return esegui_query(query, valori)
    except Exception as e:
        return {"success": False, "error": str(e)}

def aggiorna_dati(nome_tabella, dati, condizione):
    """
    Aggiorna dati in una tabella
    :param nome_tabella: Nome della tabella
    :param dati: Dizionario con i dati da aggiornare {colonna: nuovo_valore}
    :param condizione: Stringa con la condizione WHERE
    """
    try:
        set_clause = ','.join([f"{k}=?" for k in dati.keys()])
        query = f"UPDATE {nome_tabella} SET {set_clause} WHERE {condizione}"
        return esegui_query(query, list(dati.values()))
    except Exception as e:
        return {"success": False, "error": str(e)}

def elimina_dati(nome_tabella, condizione):
    """
    Elimina dati da una tabella
    :param nome_tabella: Nome della tabella
    :param condizione: Stringa con la condizione WHERE
    """
    try:
        query = f"DELETE FROM {nome_tabella} WHERE {condizione}"
        return esegui_query(query)
    except Exception as e:
        return {"success": False, "error": str(e)}

def consulta_tabella(nome_tabella, colonne="*", condizione=None):
    """
    Consulta dati in una tabella
    :param nome_tabella: Nome della tabella
    :param colonne: Stringhe delle colonne da selezionare, default "*"
    :param condizione: Stringa con la condizione WHERE opzionale
    """
    try:
        query = f"SELECT {colonne} FROM {nome_tabella}"
        if condizione:
            query += f" WHERE {condizione}"
        return esegui_query(query)
    except Exception as e:
        return {"success": False, "error": str(e)}

def elenca_tabelle():
    """Restituisce la lista delle tabelle nel database"""
    try:
        return esegui_query("SELECT name FROM sqlite_master WHERE type='table'")
    except Exception as e:
        return {"success": False, "error": str(e)}

def descrivi_tabella(nome_tabella):
    """Restituisce la struttura di una tabella"""
    try:
        return esegui_query(f"PRAGMA table_info({nome_tabella})")
    except Exception as e:
        return {"success": False, "error": str(e)}

def modifica_tabella(nome_tabella, operazione, **kwargs):
    """
    Modifica la struttura di una tabella esistente
    :param nome_tabella: Nome della tabella da modificare
    :param operazione: Tipo di modifica ('aggiungi_colonna' o 'rimuovi_colonna')
    :param kwargs: Parametri aggiuntivi (definizione_colonna per aggiungi, nome_colonna per rimuovi)
    """
    try:
        if operazione == "aggiungi_colonna":
            definizione_colonna = kwargs.get("definizione_colonna")
            if not definizione_colonna:
                return {"success": False, "error": "Definizione colonna mancante"}
            
            query = f"ALTER TABLE {nome_tabella} ADD COLUMN {definizione_colonna}"
            return esegui_query(query)
            
        elif operazione == "rimuovi_colonna":
            nome_colonna = kwargs.get("nome_colonna")
            if not nome_colonna:
                return {"success": False, "error": "Nome colonna mancante"}
                
            # Creiamo una nuova tabella senza la colonna
            info_tabella = descrivi_tabella(nome_tabella)
            if not info_tabella["success"]:
                return info_tabella
                
            # Filtra le colonne escludendo quella da rimuovere
            colonne = [col for col in info_tabella["data"] if col["name"] != nome_colonna]
            if len(colonne) == len(info_tabella["data"]):
                return {"success": False, "error": f"Colonna {nome_colonna} non trovata"}
                
            # Crea la nuova definizione della tabella
            definizioni = []
            nomi_colonne = []
            for col in colonne:
                tipo = col["type"]
                nome = col["name"]
                nomi_colonne.append(nome)
                definizione = f"{nome} {tipo}"
                if col["pk"]:
                    definizione += " PRIMARY KEY"
                if not col["notnull"]:
                    definizione += " NULL"
                definizioni.append(definizione)
                
            # Crea una tabella temporanea con la nuova struttura
            temp_tabella = f"temp_{nome_tabella}"
            crea_temp = esegui_query(f"CREATE TABLE {temp_tabella} ({', '.join(definizioni)})")
            if not crea_temp["success"]:
                return crea_temp
                
            # Copia i dati
            colonne_str = ', '.join(nomi_colonne)
            copia_dati = esegui_query(f"INSERT INTO {temp_tabella} ({colonne_str}) SELECT {colonne_str} FROM {nome_tabella}")
            if not copia_dati["success"]:
                esegui_query(f"DROP TABLE {temp_tabella}")
                return copia_dati
                
            # Sostituisci la vecchia tabella
            esegui_query(f"DROP TABLE {nome_tabella}")
            esegui_query(f"ALTER TABLE {temp_tabella} RENAME TO {nome_tabella}")
            
            return {"success": True, "message": f"Colonna {nome_colonna} rimossa con successo"}
        else:
            return {"success": False, "error": f"Operazione non supportata: {operazione}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def esporta_tabella(nome_tabella, file_destinazione, formato="csv"):
    """
    Esporta i dati di una tabella in un file di testo
    :param nome_tabella: Nome della tabella da esportare
    :param file_destinazione: Percorso completo del file di destinazione
    :param formato: Formato di esportazione ('csv' o 'txt')
    :return: Dizionario con il risultato dell'operazione
    """
    try:
        # Ottieni i dati dalla tabella
        risultato = consulta_tabella(nome_tabella)
        if not risultato["success"]:
            return risultato

        # Ottieni la struttura della tabella per i nomi delle colonne
        struttura = descrivi_tabella(nome_tabella)
        if not struttura["success"]:
            return struttura

        # Estrai i nomi delle colonne
        nomi_colonne = [col["name"] for col in struttura["data"]]
        
        # Assicurati che la directory di destinazione esista
        os.makedirs(os.path.dirname(file_destinazione), exist_ok=True)
        
        if formato.lower() == "csv":
            # Usa il modulo csv per gestire l'output CSV con punto e virgola come separatore
            with open(file_destinazione, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(nomi_colonne)  # Scrivi intestazione
                
                # Scrivi i dati
                for riga in risultato["data"]:
                    writer.writerow([riga.get(col, "") for col in nomi_colonne])
                    
        else:
            # Formato testo tabulare
            larghezze = {col: len(col) for col in nomi_colonne}
            for riga in risultato["data"]:
                for col in nomi_colonne:
                    larghezze[col] = max(larghezze[col], len(str(riga.get(col, ""))))

            # Prepara le linee di output
            linee = []
            sep = "+" + "+".join("-" * (larghezze[col] + 2) for col in nomi_colonne) + "+"
            
            # Intestazione
            linee.append(sep)
            header = "|"
            for col in nomi_colonne:
                header += f" {col:<{larghezze[col]}} |"
            linee.append(header)
            linee.append(sep)
            
            # Dati
            for riga in risultato["data"]:
                line = "|"
                for col in nomi_colonne:
                    val = str(riga.get(col, ""))
                    line += f" {val:<{larghezze[col]}} |"
                linee.append(line)
            linee.append(sep)
            
            # Scrivi il file
            with open(file_destinazione, 'w', encoding='utf-8') as f:
                f.write('\n'.join(linee))

        return {
            "success": True,
            "message": f"Tabella esportata con successo in {file_destinazione}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }