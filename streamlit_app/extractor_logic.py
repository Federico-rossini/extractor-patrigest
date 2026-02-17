# -*- coding: utf-8 -*-
"""
EXTRACTOR LOGIC v4.0 - COPIA ESATTA SCRIPT FUNZIONANTE
Adattato per Streamlit (accetta bytes)
"""

import re
import pandas as pd
import tempfile
import os

try:
    import tabula
except ImportError:
    raise ImportError("tabula-py non installato")


def safe_str(value):
    """Converte valore in stringa sicura"""
    if pd.isna(value):
        return ""
    if value is None:
        return ""
    s = str(value).strip()
    
    # Rimuovi decimali ".0"
    if '.' in s:
        try:
            parts = s.split('.')
            if len(parts) == 2 and parts[1] in ['0', '00']:
                return parts[0]
        except:
            pass
    
    return s


def estrai_categoria(testo):
    """Estrae categoria: A/2 → A2"""
    testo = safe_str(testo).upper().strip()
    
    # Pattern 1: "A/2"
    m = re.search(r'([A-Z])/(\d{1,2})', testo)
    if m:
        return m.group(1) + m.group(2)
    
    # Pattern 2: "A2"
    m = re.search(r'\b([A-Z])(\d{1,2})\b', testo)
    if m:
        return m.group(1) + m.group(2)
    
    return ""


def estrai_consistenza(testo):
    """Estrae consistenza"""
    testo = safe_str(testo)
    
    # "4,5 vani"
    m = re.search(r'([\d,\.]+)\s*vani', testo, re.IGNORECASE)
    if m:
        return m.group(1) + " vani"
    
    # "19m" (solo < 30)
    m = re.search(r'(\d+)\s*m\b', testo, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        if val < 30:
            return m.group(1) + "m"
    
    return ""


def estrai_superficie(testo):
    """Estrae superficie (primo Totale)"""
    testo = safe_str(testo)
    
    # "Totale: 97 m"
    m = re.search(r'Totale:?\s+(\d+)\s*m', testo, re.IGNORECASE)
    if m:
        return m.group(1)
    
    # Fallback: "XXX m²" con val >= 30
    matches = re.findall(r'(\d+)\s*m', testo, re.IGNORECASE)
    if matches:
        for match in matches:
            val = int(match)
            if val >= 30:
                return match
    
    return ""


def estrai_rendita(testo):
    """Estrae rendita"""
    testo = safe_str(testo)
    
    m = re.search(r'Euro\s+([\d,\.]+)', testo, re.IGNORECASE)
    if m:
        return m.group(1).replace(',', '.')
    
    return ""


def estrai_indirizzo(testo):
    """Estrae indirizzo"""
    testo = safe_str(testo)
    
    m = re.search(
        r'(VIA|PIAZZA|CORSO|VIALE|STRADA|VICOLO|LARGO|CONTRADA)\s+([A-ZÀ-Ù\s]+?)(?:\s+n\.\s*(\S+?))?(?:\s+(?:Scala|Piano|VARIAZIONE|Interno|$))', 
        testo, 
        re.IGNORECASE
    )
    
    if m:
        tipo_via = m.group(1).strip()
        nome_via = m.group(2).strip()
        civico = m.group(3).strip() if m.group(3) else ""
        
        indirizzo = f"{tipo_via} {nome_via}"
        if civico:
            indirizzo += f" n. {civico}"
        
        return re.sub(r'\s+', ' ', indirizzo).strip()
    
    return ""


def elabora_pdf_bytes(pdf_bytes, filename="documento.pdf"):
    """
    Elabora PDF da bytes - LOGICA IDENTICA ALLO SCRIPT FUNZIONANTE
    """
    risultati = []
    
    try:
        # Salva temporaneamente (tabula richiede path)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = tmp_file.name
        
        # Leggi PDF con tabula
        dfs = tabula.read_pdf(
            tmp_path,
            pages='all',
            multiple_tables=True,
            lattice=True,
            silent=True,
            pandas_options={'header': None}
        )
        
        # Rimuovi file temporaneo
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        if not dfs:
            return risultati
        
        # Concatena tutte le tabelle
        df = pd.concat(dfs, ignore_index=True)
        
        # Cerca riga intestazioni
        riga_intestazioni = None
        for idx in range(min(25, len(df))):
            testo_riga = ' '.join([safe_str(v).upper() for v in df.iloc[idx].values])
            if 'FOGLIO' in testo_riga and 'NUMERO' in testo_riga:
                riga_intestazioni = idx
                break
        
        if riga_intestazioni is None:
            return risultati
        
        # Mappa colonne
        riga_int = df.iloc[riga_intestazioni]
        mappa_col = {}
        
        for idx_col, valore in enumerate(riga_int):
            val_str = safe_str(valore).upper()
            
            if 'FOGLIO' in val_str:
                mappa_col['foglio'] = idx_col
            elif 'NUMERO' in val_str and 'foglio' not in val_str.lower():
                mappa_col['numero'] = idx_col
            elif 'SUB' in val_str:
                mappa_col['sub'] = idx_col
            elif 'CATEGORIA' in val_str:
                mappa_col['categoria'] = idx_col
            elif 'CONSISTENZA' in val_str:
                mappa_col['consistenza'] = idx_col
            elif 'SUPERFICIE' in val_str:
                mappa_col['superficie'] = idx_col
            elif 'RENDITA' in val_str:
                mappa_col['rendita'] = idx_col
            elif 'INDIRIZZO' in val_str:
                mappa_col['indirizzo'] = idx_col
        
        # Mantieni foglio/numero correnti
        foglio_corrente = ""
        numero_corrente = ""
        
        righe_processate = 0
        
        # Elabora righe dati
        for idx in range(riga_intestazioni + 1, len(df)):
            riga = df.iloc[idx]
            
            try:
                # Testo completo
                testo_completo = ' '.join([safe_str(v) for v in riga.values if safe_str(v)])
                
                # Skip righe vuote
                if len(testo_completo) < 10:
                    continue
                
                # Skip intestazioni ripetute - SOLO QUESTI 3 PATTERN (come nello script funzionante)
                if any(x in testo_completo.upper() for x in ['DATI IDENTIFICATIVI', 'SEGUE', 'PAG:']):
                    continue
                
                righe_processate += 1
                
                # Estrai foglio/numero/sub dalle celle
                foglio_cella = safe_str(riga[mappa_col.get('foglio', 1)]) if 'foglio' in mappa_col else ""
                numero_cella = safe_str(riga[mappa_col.get('numero', 2)]) if 'numero' in mappa_col else ""
                sub_cella = safe_str(riga[mappa_col.get('sub', 3)]) if 'sub' in mappa_col else ""
                
                # Pulisci sub
                sub_cella = sub_cella.strip()
                
                # Aggiorna foglio/numero se presenti
                if foglio_cella and re.match(r'^\d+$', foglio_cella):
                    foglio_corrente = foglio_cella
                
                if numero_cella and re.match(r'^\d+$', numero_cella):
                    numero_corrente = numero_cella
                
                # Sub OBBLIGATORIO - cerca anche nel testo se manca
                if not sub_cella or not re.match(r'^\d+$', sub_cella):
                    # Cerca sub nel testo completo
                    m = re.search(r'\b(\d{1,3})\b', testo_completo)
                    if m:
                        # Prendi primo numero plausibile (non foglio/numero)
                        for num in re.findall(r'\b(\d{1,3})\b', testo_completo):
                            if num != foglio_corrente and num != numero_corrente:
                                sub_cella = num
                                break
                
                if not sub_cella or not re.match(r'^\d+$', sub_cella):
                    continue
                
                # Estrai categoria (OBBLIGATORIA)
                categoria = ""
                if 'categoria' in mappa_col:
                    cat_cella = safe_str(riga[mappa_col['categoria']])
                    categoria = estrai_categoria(cat_cella)
                
                if not categoria:
                    categoria = estrai_categoria(testo_completo)
                
                if not categoria:
                    continue  # Skip senza categoria
                
                # Estrai altri campi (opzionali)
                consistenza = ""
                if 'consistenza' in mappa_col:
                    cons_cella = safe_str(riga[mappa_col['consistenza']])
                    consistenza = estrai_consistenza(cons_cella)
                if not consistenza:
                    consistenza = estrai_consistenza(testo_completo)
                
                superficie = ""
                if 'superficie' in mappa_col:
                    sup_cella = safe_str(riga[mappa_col['superficie']])
                    superficie = estrai_superficie(sup_cella)
                if not superficie:
                    superficie = estrai_superficie(testo_completo)
                
                rendita = ""
                if 'rendita' in mappa_col:
                    rend_cella = safe_str(riga[mappa_col['rendita']])
                    rendita = estrai_rendita(rend_cella)
                if not rendita:
                    rendita = estrai_rendita(testo_completo)
                
                indirizzo = ""
                if 'indirizzo' in mappa_col:
                    ind_cella = safe_str(riga[mappa_col['indirizzo']])
                    indirizzo = estrai_indirizzo(ind_cella)
                if not indirizzo:
                    indirizzo = estrai_indirizzo(testo_completo)
                
                # Usa foglio/numero correnti
                foglio_finale = foglio_corrente if foglio_corrente else ""
                numero_finale = numero_corrente if numero_corrente else ""
                
                # Aggiungi risultato
                risultati.append({
                    'Foglio': foglio_finale,
                    'Numero': numero_finale,
                    'Sub': sub_cella,
                    'Categoria': categoria,
                    'Consistenza': consistenza,
                    'Superficie Catastale': superficie,
                    'Rendita': rendita,
                    'Indirizzo': indirizzo
                })
                
            except Exception as e:
                # Non bloccare per errori su singola riga
                continue
    
    except Exception as e:
        # Errore generale sul PDF
        pass
    
    return risultati
