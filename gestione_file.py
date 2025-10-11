import os
import shutil

def cancella_cartella(nome_cartella):
    """
    Cancella una cartella e tutto il suo contenuto ricorsivamente.
    """
    import shutil
    import os
    try:
        if os.path.exists(nome_cartella) and os.path.isdir(nome_cartella):
            shutil.rmtree(nome_cartella)
            return f"Cartella '{nome_cartella}' cancellata con successo."
        else:
            return f"La cartella '{nome_cartella}' non esiste."
    except Exception as e:
        return f"Errore durante la cancellazione della cartella '{nome_cartella}': {e}"

def sposta_cartella(percorso_origine, percorso_destinazione):
    """
    Sposta una cartella (o file) da percorso_origine a percorso_destinazione.
    Crea le cartelle di destinazione se non esistono.
    """
    import os
    import shutil
    try:
        if not os.path.exists(percorso_origine):
            return f"Il percorso '{percorso_origine}' non esiste."
        
        dir_dest = os.path.dirname(percorso_destinazione)
        if dir_dest and not os.path.exists(dir_dest):
            os.makedirs(dir_dest)
        
        shutil.move(percorso_origine, percorso_destinazione)
        return f"Cartella o file spostato da '{percorso_origine}' a '{percorso_destinazione}'."
    except Exception as e:
        return f"Errore nello spostamento: {e}"

def scrivi_registro_chat(nome_file, registro_chat):
    """
    Scrive tutto il registro della chat nel file 'registro.txt'.
    registro_chat deve essere una stringa (es. concatenazione di tutti i messaggi).
    """
    try:
        with open(nome_file, "w", encoding="utf-8") as f:
            f.write(registro_chat)
        return f"Registro chat salvato in '{nome_file}'."
    except Exception as e:
        return f"Errore durante la scrittura del registro chat: {e}"

def crea_cartella(nome_cartella):
    print(f"DEBUG: Creo cartella in: {nome_cartella}")  # Vedi quale percorso arriva
    if not os.path.exists(nome_cartella):
        os.makedirs(nome_cartella)
        return f"Cartella '{nome_cartella}' creata con successo."
    else:
        return f"La cartella '{nome_cartella}' esiste già."



def crea_file(nome_file):
    """
    Crea un nuovo file di testo vuoto con il nome fornito, creando anche le cartelle mancanti.
    Se il file esiste, non fa nulla.
    """
    try:
        cartella = os.path.dirname(nome_file)
        if cartella and not os.path.exists(cartella):
            os.makedirs(cartella)  # crea tutte le cartelle necessarie
        if not os.path.exists(nome_file):
            with open(nome_file, "w", encoding="utf-8") as f:
                pass
            return f"File '{nome_file}' creato con successo."
        else:
            return f"Il file '{nome_file}' esiste già."
    except Exception as e:
        return f"Errore durante la creazione del file '{nome_file}': {e}"

def sposta_file(percorso_origine, percorso_destinazione):
    """
    Sposta un file da percorso_origine a percorso_destinazione.
    Crea le cartelle di destinazione se non esistono.
    """
    try:
        if not os.path.exists(percorso_origine):
            return f"Il file '{percorso_origine}' non esiste."
        
        dir_dest = os.path.dirname(percorso_destinazione)
        if dir_dest and not os.path.exists(dir_dest):
            os.makedirs(dir_dest)
        
        shutil.move(percorso_origine, percorso_destinazione)
        return f"File spostato da '{percorso_origine}' a '{percorso_destinazione}'."
    except Exception as e:
        return f"Errore nello spostamento del file: {e}"

def scrivi_file(nome_file, contenuto):
    """
    Scrive/modifica il contenuto del file specificato.
    Sovrascrive tutto il contenuto del file con la stringa fornita.
    """
    try:
        with open(nome_file, "w", encoding="utf-8") as f:
            f.write(contenuto)
        return f"Contenuto scritto nel file '{nome_file}'."
    except Exception as e:
        return f"Errore durante la scrittura nel file '{nome_file}': {e}"

def aggiungi_al_file(nome_file, contenuto):
    """
    Aggiunge contenuto al file specificato senza cancellare quello esistente.
    """
    try:
        with open(nome_file, "a", encoding="utf-8") as f:
            f.write(contenuto)
        return f"Contenuto aggiunto al file '{nome_file}'."
    except Exception as e:
        return f"Errore durante l'aggiunta nel file '{nome_file}': {e}"

def cancella_contenuto_file(nome_file):
    """
    Svuota il contenuto del file senza cancellarlo.
    """
    try:
        with open(nome_file, "w", encoding="utf-8") as f:
            pass
        return f"Contenuto del file '{nome_file}' cancellato."
    except Exception as e:
        return f"Errore durante lo svuotamento del file '{nome_file}': {e}"

def cancella_file(nome_file):
    """
    Cancella il file dal disco.
    """
    try:
        if os.path.exists(nome_file):
            os.remove(nome_file)
            return f"File '{nome_file}' cancellato con successo."
        else:
            return f"Il file '{nome_file}' non esiste."
    except Exception as e:
        return f"Errore durante la cancellazione del file '{nome_file}': {e}"
