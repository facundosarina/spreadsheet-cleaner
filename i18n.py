"""
i18n.py

Every string the app shows, in one place.

Three languages ship: Spanish, English and Italian -- the ones the author can
actually proofread. Adding a fourth is adding one dict below; nothing else in
the app hardcodes a sentence.

Note what is NOT translated: the cleaning rules themselves. They are built for
Argentine records (DNI, CUIT, +54 phone numbers, dd/mm dates, ARS amounts), and
translating the buttons would not change that. The app says so on screen in
every language rather than implying it works anywhere.
"""

from __future__ import annotations

LANGUAGES = {"es": "Español", "en": "English", "it": "Italiano"}

DEFAULT_LANGUAGE = "es"

STRINGS: dict[str, dict[str, str]] = {
    "es": {
        "app_name": "Fila Limpia",
        "tagline": "Corregimos lo seguro. Vos decidís lo dudoso.",
        "intro": "Subí una base de clientes, pagos o contactos y te la devolvemos "
                 "ordenada, con el detalle de cada cambio y la lista de lo que no "
                 "nos animamos a adivinar.",
        "scope_note": "Las reglas son argentinas: DNI, CUIT, teléfonos +54, fechas "
                      "día/mes e importes en pesos.",
        "privacy": "Tu archivo se procesa acá y no se guarda. Son reglas escritas a "
                   "mano: no se envía nada a ninguna IA.",
        "language": "Idioma",

        "drop_here": "Arrastrá tu archivo o elegilo",
        "formats": "CSV, XLSX o XLS · hasta 20 MB",
        "or": "o",
        "try_demo": "Ver una demostración",
        "demo_badge": "Archivo de demostración",
        "demo_clients": "Base de clientes (45 filas)",
        "demo_payments": "Base de pagos (40 filas)",
        "start_over": "Empezar de nuevo",

        "step_upload": "Subir",
        "step_confirm": "Confirmar",
        "step_review": "Revisar",
        "step_download": "Descargar",

        "confirm_title": "Confirmá cómo leímos el archivo",
        "detected_rows": "Detectamos {rows} filas y {cols} columnas",
        "column": "Columna",
        "detected_type": "Tipo detectado",
        "example": "Ejemplo",
        "sheet": "Hoja",
        "which_sheet": "Este archivo tiene varias hojas. ¿Cuál querés limpiar?",
        "separator": "Separador",
        "encoding": "Codificación",
        "read_as": "Leído como",
        "clean_button": "Limpiar {rows} filas",

        "result_title": "Archivo procesado",
        "fixed": "correcciones seguras",
        "pending": "valores necesitan revisión",
        "dupes": "posibles duplicados",
        "all_clear": "No quedó nada pendiente. El archivo está listo.",
        "review_cta": "Revisar {n} pendientes",
        "download_anyway": "Descargar igual",
        "download_clean": "Descargar archivo limpio",
        "download_pack": "Descargar todo (limpio + cambios + pendientes)",
        "changes_tab": "Cambios aplicados",
        "dupes_tab": "Posibles duplicados",
        "table_tab": "Tabla completa",

        "review_title": "Pendientes de revisión",
        "case_of": "Caso {i} de {n}",
        "row": "Fila",
        "problem": "Problema",
        "original_value": "Valor original",
        "your_value": "Corrección",
        "keep_original": "Mantener original",
        "apply_fix": "Aplicar corrección",
        "skip": "Saltear",
        "reviewed": "{done} de {total} revisados",
        "review_done": "Terminaste de revisar. Podés descargar el archivo.",
        "dupe_question": "Estas filas parecen ser la misma persona",
        "keep_both": "Mantener ambas",
        "delete_dupe": "Eliminar la repetida",
        "first_seen": "primera aparición en la fila {row}",

        "changed_from": "antes",
        "changed_to": "después",
        "what_changed": "qué cambió",
        "no_changes": "No hubo nada que corregir en este archivo.",
        "highlight_note": "Las celdas corregidas están resaltadas.",

        "err_read": "No pudimos abrir «{name}». Probá guardándolo como XLSX o CSV y "
                    "volvé a subirlo.",
        "err_encoding": "No pudimos entender la codificación de «{name}». Guardalo "
                        "como CSV UTF-8 y volvé a intentar.",
        "err_empty": "Ese archivo no tiene filas.",
        "err_xls": "Los archivos .xls viejos necesitan una librería extra que no está "
                   "instalada. Guardalo como .xlsx y volvé a subirlo.",
    },

    "en": {
        "app_name": "Fila Limpia",
        "tagline": "We fix what is certain. You decide what isn't.",
        "intro": "Upload a client, payment or contact list and get it back tidy, with "
                 "a log of every change and a list of the values we would not guess at.",
        "scope_note": "The rules are Argentine: DNI, CUIT, +54 phone numbers, "
                      "day/month dates and peso amounts.",
        "privacy": "Your file is processed here and not stored. These are hand-written "
                   "rules — nothing is sent to any AI.",
        "language": "Language",

        "drop_here": "Drop your file here, or pick one",
        "formats": "CSV, XLSX or XLS · up to 20 MB",
        "or": "or",
        "try_demo": "See a demonstration",
        "demo_badge": "Demonstration file",
        "demo_clients": "Client list (45 rows)",
        "demo_payments": "Payments list (40 rows)",
        "start_over": "Start over",

        "step_upload": "Upload",
        "step_confirm": "Confirm",
        "step_review": "Review",
        "step_download": "Download",

        "confirm_title": "Confirm how we read the file",
        "detected_rows": "We found {rows} rows and {cols} columns",
        "column": "Column",
        "detected_type": "Detected type",
        "example": "Example",
        "sheet": "Sheet",
        "which_sheet": "This file has several sheets. Which one should we clean?",
        "separator": "Separator",
        "encoding": "Encoding",
        "read_as": "Read as",
        "clean_button": "Clean {rows} rows",

        "result_title": "File processed",
        "fixed": "safe corrections",
        "pending": "values need review",
        "dupes": "possible duplicates",
        "all_clear": "Nothing left pending. The file is ready.",
        "review_cta": "Review {n} pending",
        "download_anyway": "Download anyway",
        "download_clean": "Download the clean file",
        "download_pack": "Download everything (clean + changes + pending)",
        "changes_tab": "Corrections applied",
        "dupes_tab": "Possible duplicates",
        "table_tab": "Full table",

        "review_title": "Pending review",
        "case_of": "Case {i} of {n}",
        "row": "Row",
        "problem": "Problem",
        "original_value": "Original value",
        "your_value": "Correction",
        "keep_original": "Keep original",
        "apply_fix": "Apply correction",
        "skip": "Skip",
        "reviewed": "{done} of {total} reviewed",
        "review_done": "Review finished. You can download the file.",
        "dupe_question": "These rows look like the same person",
        "keep_both": "Keep both",
        "delete_dupe": "Delete the repeat",
        "first_seen": "first seen in row {row}",

        "changed_from": "before",
        "changed_to": "after",
        "what_changed": "what changed",
        "no_changes": "Nothing needed fixing in this file.",
        "highlight_note": "Corrected cells are highlighted.",

        "err_read": "We couldn't open “{name}”. Try saving it as XLSX or CSV and "
                    "upload it again.",
        "err_encoding": "We couldn't work out the encoding of “{name}”. Save it as "
                        "UTF-8 CSV and try again.",
        "err_empty": "That file has no rows.",
        "err_xls": "Old .xls files need an extra library that isn't installed. Save it "
                   "as .xlsx and upload it again.",
    },

    "it": {
        "app_name": "Fila Limpia",
        "tagline": "Correggiamo ciò che è certo. Il dubbio lo decidi tu.",
        "intro": "Carica un elenco di clienti, pagamenti o contatti e te lo "
                 "restituiamo in ordine, con il dettaglio di ogni modifica e "
                 "l'elenco dei valori che non abbiamo voluto indovinare.",
        "scope_note": "Le regole sono argentine: DNI, CUIT, numeri +54, date "
                      "giorno/mese e importi in pesos.",
        "privacy": "Il file viene elaborato qui e non viene conservato. Sono regole "
                   "scritte a mano: nulla viene inviato a un'IA.",
        "language": "Lingua",

        "drop_here": "Trascina il file o scegline uno",
        "formats": "CSV, XLSX o XLS · fino a 20 MB",
        "or": "oppure",
        "try_demo": "Vedi una dimostrazione",
        "demo_badge": "File dimostrativo",
        "demo_clients": "Elenco clienti (45 righe)",
        "demo_payments": "Elenco pagamenti (40 righe)",
        "start_over": "Ricomincia",

        "step_upload": "Carica",
        "step_confirm": "Conferma",
        "step_review": "Rivedi",
        "step_download": "Scarica",

        "confirm_title": "Conferma come abbiamo letto il file",
        "detected_rows": "Abbiamo trovato {rows} righe e {cols} colonne",
        "column": "Colonna",
        "detected_type": "Tipo rilevato",
        "example": "Esempio",
        "sheet": "Foglio",
        "which_sheet": "Questo file ha più fogli. Quale vuoi pulire?",
        "separator": "Separatore",
        "encoding": "Codifica",
        "read_as": "Letto come",
        "clean_button": "Pulisci {rows} righe",

        "result_title": "File elaborato",
        "fixed": "correzioni sicure",
        "pending": "valori da rivedere",
        "dupes": "possibili duplicati",
        "all_clear": "Non è rimasto nulla in sospeso. Il file è pronto.",
        "review_cta": "Rivedi {n} in sospeso",
        "download_anyway": "Scarica comunque",
        "download_clean": "Scarica il file pulito",
        "download_pack": "Scarica tutto (pulito + modifiche + in sospeso)",
        "changes_tab": "Correzioni applicate",
        "dupes_tab": "Possibili duplicati",
        "table_tab": "Tabella completa",

        "review_title": "In attesa di revisione",
        "case_of": "Caso {i} di {n}",
        "row": "Riga",
        "problem": "Problema",
        "original_value": "Valore originale",
        "your_value": "Correzione",
        "keep_original": "Mantieni l'originale",
        "apply_fix": "Applica la correzione",
        "skip": "Salta",
        "reviewed": "{done} di {total} riviste",
        "review_done": "Revisione completata. Puoi scaricare il file.",
        "dupe_question": "Queste righe sembrano la stessa persona",
        "keep_both": "Tieni entrambe",
        "delete_dupe": "Elimina la ripetizione",
        "first_seen": "prima comparsa alla riga {row}",

        "changed_from": "prima",
        "changed_to": "dopo",
        "what_changed": "cosa è cambiato",
        "no_changes": "Non c'era nulla da correggere in questo file.",
        "highlight_note": "Le celle corrette sono evidenziate.",

        "err_read": "Non siamo riusciti ad aprire «{name}». Prova a salvarlo come "
                    "XLSX o CSV e caricalo di nuovo.",
        "err_encoding": "Non siamo riusciti a capire la codifica di «{name}». "
                        "Salvalo come CSV UTF-8 e riprova.",
        "err_empty": "Questo file non ha righe.",
        "err_xls": "I vecchi file .xls richiedono una libreria non installata. "
                   "Salvalo come .xlsx e caricalo di nuovo.",
    },
}

# Column-kind labels, kept beside the rest of the copy.
KIND_LABELS: dict[str, dict[str, str]] = {
    "es": {"name": "Nombre", "dni": "DNI", "cuit": "CUIT", "phone": "Teléfono",
           "email": "Email", "date": "Fecha", "amount": "Importe",
           "category": "Categoría", "text": "Texto libre"},
    "en": {"name": "Name", "dni": "ID number (DNI)", "cuit": "Tax ID (CUIT)",
           "phone": "Phone", "email": "Email", "date": "Date", "amount": "Amount",
           "category": "Category", "text": "Free text"},
    "it": {"name": "Nome", "dni": "DNI", "cuit": "CUIT", "phone": "Telefono",
           "email": "Email", "date": "Data", "amount": "Importo",
           "category": "Categoria", "text": "Testo libero"},
}

# What was corrected, in the person's language.
CHANGES: dict[str, dict[str, str]] = {
    "es": {
        "spaces": "espacios de más",
        "caps": "mayúsculas y minúsculas",
        "format": "formato unificado",
        "iso": "fecha a AAAA-MM-DD",
        "number": "convertido a número",
        "domain": "dominio corregido",
        "unified": "misma etiqueta escrita distinto",
    },
    "en": {
        "spaces": "extra spaces",
        "caps": "capitalisation",
        "format": "standardised format",
        "iso": "date to YYYY-MM-DD",
        "number": "converted to a number",
        "domain": "domain typo corrected",
        "unified": "same label written differently",
    },
    "it": {
        "spaces": "spazi in eccesso",
        "caps": "maiuscole e minuscole",
        "format": "formato uniformato",
        "iso": "data in AAAA-MM-GG",
        "number": "convertito in numero",
        "domain": "dominio corretto",
        "unified": "stessa etichetta scritta diversamente",
    },
}

# Why a value was held back, in the person's language.
REASONS: dict[str, dict[str, str]] = {
    "es": {
        "digits": "tiene {n} dígitos y esperábamos {expected}",
        "check_digit": "el dígito verificador no coincide",
        "bad_email": "no parece una dirección válida",
        "bad_date": "no reconocimos el formato de fecha",
        "no_digits": "no encontramos números",
        "bad_number": "no pudimos leer el número",
    },
    "en": {
        "digits": "has {n} digits, expected {expected}",
        "check_digit": "the check digit does not match",
        "bad_email": "does not look like a valid address",
        "bad_date": "we did not recognise the date format",
        "no_digits": "no digits found",
        "bad_number": "we could not read the number",
    },
    "it": {
        "digits": "ha {n} cifre, ne attendevamo {expected}",
        "check_digit": "la cifra di controllo non corrisponde",
        "bad_email": "non sembra un indirizzo valido",
        "bad_date": "non abbiamo riconosciuto il formato della data",
        "no_digits": "nessuna cifra trovata",
        "bad_number": "non siamo riusciti a leggere il numero",
    },
}


def t(language: str, key: str, **kwargs) -> str:
    """Look up a string, falling back to Spanish and then to the key itself."""
    table = STRINGS.get(language) or STRINGS[DEFAULT_LANGUAGE]
    text = table.get(key) or STRINGS[DEFAULT_LANGUAGE].get(key, key)
    return text.format(**kwargs) if kwargs else text


def kind_label(language: str, kind: str) -> str:
    table = KIND_LABELS.get(language) or KIND_LABELS[DEFAULT_LANGUAGE]
    return table.get(kind, kind)


def reason_text(language: str, code: str, **kwargs) -> str:
    """The sentence for a note code, whether it was a fix or a held-back value."""
    for table_set in (REASONS, CHANGES):
        table = table_set.get(language) or table_set[DEFAULT_LANGUAGE]
        if code in table:
            text = table[code]
            return text.format(**kwargs) if kwargs else text
    return code
