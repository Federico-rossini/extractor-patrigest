# -*- coding: utf-8 -*-
"""
EXTRACTOR LOGIC v10.0 FINALE - UNIVERSALE COMPLETO
Supporta visure moderne + legacy con:
- Multi-estrazione (multipli part/sub nella stessa riga)
- Pattern indirizzo flessibile
- Categoria pulita (senza lettere finali)
- Statistiche dettagliate
"""

import re
import pandas as pd
import tempfile
import os

try:
    import tabula
except ImportError:
    raise ImportError("tabula-py non installato")

DEBUG_MODE = False

def debug_print(msg):
    if DEBUG_MODE:
        print(f"[DEBUG] {msg}")

def safe_str(value):
    """Converte valore in stringa sicura"""
    if pd.isna(value):
        return ""
    if value is None:
        return ""
    s = str(value).strip()
    
    if '.' in s:
        try:
            parts = s.split('.')
            if len(parts) == 2 and parts[1] in ['0', '00']:
                return parts[0]
        except:
            pass
    
    return s


# ============ ESTRAZIONE CAMPI ============

def estrai_categoria(testo):
    """
    Estrae categoria - PULITA senza lettere finali
    D/1a) → D1
    A/2 → A2
    C/3b) → C3
    """
    testo = safe_str(testo).upper().strip()
    
    # Pattern 1: "D/1a)" o "A/2b)" - RIMUOVE lettere finali
    m = re.search(r'([A-Z])/(\d{1,2})[a-z]?\)', testo)
    if m:
        return m.group(1) + m.group(2)
    
    # Pattern 2: "A/2"
    m = re.search(r'([A-Z])/(\d{1,2})', testo)
    if m:
        return m.group(1) + m.group(2)
    
    # Pattern 3: "A2"
    m = re.search(r'\b([A-Z])(\d{1,2})\b', testo)
    if m:
        return m.group(1) + m.group(2)
    
    return ""


def estrai_consistenza(testo):
    testo = safe_str(testo)
    
    m = re.search(r'([\d,\.]+)\s*vani', testo, re.IGNORECASE)
    if m:
        return m.group(1) + " vani"
    
    m = re.search(r'(\d+)\s*m\b', testo, re.IGNORECASE)
    if m:
        try:
            val = int(m.group(1))
            if val < 30:
                return m.group(1) + "m"
        except:
            pass
    
    return ""


def estrai_superficie(testo):
    testo = safe_str(testo)
    
    m = re.search(r'Totale:?\s+(\d+)\s*m', testo, re.IGNORECASE)
    if m:
        return m.group(1)
    
    matches = re.findall(r'(\d+)\s*m', testo, re.IGNORECASE)
    if matches:
        for match in matches:
            try:
                val = int(match)
                if val >= 30:
                    return match
            except:
                pass
    
    return ""


def estrai_rendita(testo):
    testo = safe_str(testo)
    
    # "Rendita Euro 85,22"
    m = re.search(r'Rendita\s+Euro\s+([\d,\.]+)', testo, re.IGNORECASE)
    if m:
        return m.group(1).replace(',', '.')
    
    # "Euro 85,22"
    m = re.search(r'Euro\s+([\d,\.]+)', testo, re.IGNORECASE)
    if m:
        return m.group(1).replace(',', '.')
    
    return ""


def estrai_indirizzo(testo):
    """
    Estrae indirizzo - PATTERN AGGRESSIVO E FLESSIBILE
    """
    testo = safe_str(testo)
    
    if not testo:
        return ""
    
    # Pattern 1: Con civico "n. 38" o "n.38"
    m = re.search(
        r'(VIA|PIAZZA|CORSO|VIALE|STRADA|VICOLO|LARGO|CONTRADA|VLE|PIAZZALE|P\.ZA|VIALE)\s+([A-ZÀ-Ù][A-ZÀ-Ù\s\.]+?)\s+n\.?\s*(\d+[A-Z]?)',
        testo,
        re.IGNORECASE
    )
    
    if m:
        tipo_via = m.group(1).strip().upper()
        nome_via = re.sub(r'\s+', ' ', m.group(2).strip()).upper()
        civico = m.group(3).strip()
        
        indirizzo = f"{tipo_via} {nome_via} n. {civico}"
        debug_print(f"    Indirizzo con civico: {indirizzo}")
        return indirizzo
    
    # Pattern 2: Senza civico - cattura fino a maiuscole ripetute o keyword
    m = re.search(
        r'(VIA|PIAZZA|CORSO|VIALE|STRADA|VICOLO|LARGO|CONTRADA|VLE|PIAZZALE|P\.ZA|VIALE)\s+([A-ZÀ-Ù][A-ZÀ-Ù\s\.]{2,50}?)(?=\s+(?:Piano|Pian|Scala|Interno|Cat|Rendita|Foglio|Part|\d{4}|$))',
        testo,
        re.IGNORECASE
    )
    
    if m:
        tipo_via = m.group(1).strip().upper()
        nome_via = re.sub(r'\s+', ' ', m.group(2).strip()).upper()
        
        # Rimuovi trailing noise
        nome_via = re.sub(r'\s+(T|S|N|P|A)$', '', nome_via)
        
        indirizzo = f"{tipo_via} {nome_via}"
        debug_print(f"    Indirizzo senza civico: {indirizzo}")
        return indirizzo
    
    # Pattern 3: Ancora più aggressivo - cattura quasi tutto
    m = re.search(
        r'(VIA|PIAZZA|CORSO|VIALE|STRADA|VICOLO|LARGO|CONTRADA)\s+([A-Z][A-ZÀ-Ù\s]{2,})',
        testo,
        re.IGNORECASE
    )
    
    if m:
        tipo_via = m.group(1).strip().upper()
        nome_via_raw = m.group(2).strip()
        
        # Tronca a prima keyword o troppi spazi
        nome_via = re.split(r'\s+(?:Piano|Pian|Scala|Cat|Rend|Foglio|Part\.|Sub\.)', nome_via_raw, maxsplit=1)[0]
        nome_via = re.sub(r'\s+', ' ', nome_via).strip().upper()
        nome_via = nome_via[:60]  # Max 60 caratteri
        
        if len(nome_via) > 2:
            indirizzo = f"{tipo_via} {nome_via}"
            debug_print(f"    Indirizzo fallback: {indirizzo}")
            return indirizzo
    
    debug_print(f"    ❌ Indirizzo NON trovato in: {testo[:100]}")
    return ""



# ============ METODO MODERNO ============

def elabora_pdf_moderno(df):
    """Elabora PDF moderno (tabelle con header)"""
    risultati = []
    
    try:
        debug_print(f"MODERNO: {len(df)} righe")
        
        riga_int = None
        for idx in range(min(30, len(df))):
            testo = ' '.join([safe_str(v).upper() for v in df.iloc[idx].values])
            if 'FOGLIO' in testo and 'NUMERO' in testo:
                riga_int = idx
                break
        
        if riga_int is None:
            debug_print("MODERNO: Header non trovato")
            return []
        
        mappa = {}
        for idx_col, val in enumerate(df.iloc[riga_int]):
            val_str = safe_str(val).upper()
            
            if 'FOGLIO' in val_str and 'foglio' not in mappa:
                mappa['foglio'] = idx_col
            elif 'NUMERO' in val_str and 'numero' not in mappa:
                mappa['numero'] = idx_col
            elif 'SUB' in val_str:
                mappa['sub'] = idx_col
            elif 'CATEGORIA' in val_str:
                mappa['categoria'] = idx_col
            elif 'CONSISTENZA' in val_str:
                mappa['consistenza'] = idx_col
            elif 'SUPERFICIE' in val_str:
                mappa['superficie'] = idx_col
            elif 'RENDITA' in val_str:
                mappa['rendita'] = idx_col
            elif 'INDIRIZZO' in val_str:
                mappa['indirizzo'] = idx_col
        
        foglio_curr = ""
        numero_curr = ""
        
        for idx in range(riga_int + 1, len(df)):
            riga = df.iloc[idx]
            
            try:
                testo = ' '.join([safe_str(v) for v in riga.values if safe_str(v)])
                
                if len(testo) < 5:
                    continue
                
                if any(x in testo.upper() for x in ['DATI IDENTIFICATIVI', 'SEGUE', 'PAG:']):
                    continue
                
                foglio = safe_str(riga[mappa.get('foglio', 0)]) if 'foglio' in mappa else ""
                numero = safe_str(riga[mappa.get('numero', 1)]) if 'numero' in mappa else ""
                sub = safe_str(riga[mappa.get('sub', 2)]) if 'sub' in mappa else ""
                
                if foglio and foglio.isdigit():
                    foglio_curr = foglio
                if numero and numero.isdigit():
                    numero_curr = numero
                
                if not sub or not sub.isdigit():
                    for num in re.findall(r'\b(\d{1,3})\b', testo):
                        if num != foglio_curr and num != numero_curr:
                            sub = num
                            break
                
                if not sub or not sub.isdigit():
                    continue
                
                categoria = ""
                if 'categoria' in mappa:
                    categoria = estrai_categoria(safe_str(riga[mappa['categoria']]))
                if not categoria:
                    categoria = estrai_categoria(testo)
                
                if not categoria:
                    continue
                
                consistenza = ""
                if 'consistenza' in mappa:
                    consistenza = estrai_consistenza(safe_str(riga[mappa['consistenza']]))
                if not consistenza:
                    consistenza = estrai_consistenza(testo)
                
                superficie = ""
                if 'superficie' in mappa:
                    superficie = estrai_superficie(safe_str(riga[mappa['superficie']]))
                if not superficie:
                    superficie = estrai_superficie(testo)
                
                rendita = ""
                if 'rendita' in mappa:
                    rendita = estrai_rendita(safe_str(riga[mappa['rendita']]))
                if not rendita:
                    rendita = estrai_rendita(testo)
                
                indirizzo = ""
                if 'indirizzo' in mappa:
                    indirizzo = estrai_indirizzo(safe_str(riga[mappa['indirizzo']]))
                if not indirizzo:
                    indirizzo = estrai_indirizzo(testo)
                
                risultati.append({
                    'Foglio': foglio_curr,
                    'Numero': numero_curr,
                    'Sub': sub,
                    'Categoria': categoria,
                    'Consistenza': consistenza,
                    'Superficie Catastale': superficie,
                    'Rendita': rendita,
                    'Indirizzo': indirizzo
                })
                
            except:
                continue
        
        # Statistiche moderno
        if risultati:
            indirizzi_presenti = sum(1 for r in risultati if r['Indirizzo'])
            debug_print(f"MODERNO: {len(risultati)} unità - Indirizzi: {indirizzi_presenti}/{len(risultati)} ({100*indirizzi_presenti/len(risultati):.1f}%)")
    
    except:
        pass
    
    return risultati


# ============ METODO LEGACY - CON MULTI-ESTRAZIONE ============

def trova_colonne_legacy(df):
    """
    Identifica le 3 colonne del formato legacy:
    - Colonna identificativi (Foglio, Part., Sub.)
    - Colonna classamento (Categoria, Rendita)
    - Colonna indirizzo (VIA, PIAZZA, etc.)
    """
    colonne = {
        'identificativi': None,
        'classamento': None,
        'indirizzo': None
    }
    
    try:
        for col_idx in range(len(df.columns)):
            sample = ' '.join([safe_str(v) for v in df[col_idx].head(20)])
            sample_upper = sample.upper()
            
            if 'FOGLIO' in sample_upper and 'PART' in sample_upper:
                colonne['identificativi'] = col_idx
                debug_print(f"Colonna identificativi: {col_idx}")
            
            elif 'CATEGORIA' in sample_upper or 'RENDITA' in sample_upper:
                colonne['classamento'] = col_idx
                debug_print(f"Colonna classamento: {col_idx}")
            
            elif re.search(r'\b(VIA|PIAZZA|CORSO|VIALE)\b', sample_upper):
                colonne['indirizzo'] = col_idx
                debug_print(f"Colonna indirizzo: {col_idx}")
        
        if colonne['identificativi'] is None:
            for col_idx in range(len(df.columns)):
                for row_idx in range(min(10, len(df))):
                    cell = safe_str(df.iloc[row_idx, col_idx])
                    if re.search(r'Foglio\s+\d+', cell, re.IGNORECASE):
                        colonne['identificativi'] = col_idx
                        debug_print(f"Colonna identificativi (fallback): {col_idx}")
                        break
                if colonne['identificativi'] is not None:
                    break
    
    except Exception as e:
        debug_print(f"Errore trova_colonne_legacy: {e}")
    
    return colonne


def estrai_tutte_particelle_da_testo(testo):
    """
    Estrae TUTTE le particelle da un testo - MULTIPLI nella stessa riga
    
    Supporta:
    - "Foglio 29 Part. 71 Categoria D/1a)"
    - "Foglio 29 Part. 134 Sub. 37 Categoria D/1a)"
    - "Foglio 29 Part. 71 Sub. 1 Foglio 29 Part. 72 Sub. 2" (MULTIPLI!)
    
    Usa re.finditer() per trovare TUTTE le occorrenze
    """
    testo = safe_str(testo)
    if not testo:
        return []
    
    particelle = []
    
    # Pattern: "Foglio 29 Part. 71" o "Foglio 29 Part. 134 Sub. 37"
    # FINDITER trova TUTTE le occorrenze!
    pattern = r'Foglio\s+(\d+)\s+Part\.\s+(\d+)(?:\s+Sub\.\s+(\d+))?'
    
    for m in re.finditer(pattern, testo, re.IGNORECASE):
        particelle.append({
            'foglio': m.group(1),
            'numero': m.group(2),
            'sub': m.group(3) if m.group(3) else ''
        })
        debug_print(f"  Match: F{m.group(1)} N{m.group(2)} S{m.group(3) if m.group(3) else '-'}")
    
    # Fallback: formato esteso "Foglio 13 Particella 102 Subalterno 1"
    if not particelle:
        pattern2 = r'Foglio\s+(\d+)\s+Particella\s+(\d+)(?:\s+Subalterno\s+(\d+))?'
        for m in re.finditer(pattern2, testo, re.IGNORECASE):
            particelle.append({
                'foglio': m.group(1),
                'numero': m.group(2),
                'sub': m.group(3) if m.group(3) else ''
            })
            debug_print(f"  Match esteso: F{m.group(1)} N{m.group(2)} S{m.group(3) if m.group(3) else '-'}")
    
    return particelle


def elabora_pdf_legacy(df):
    """Elabora PDF legacy - LETTURA A COLONNE + MULTI-ESTRAZIONE"""
    risultati = []
    
    try:
        debug_print(f"LEGACY: {len(df)} righe totali")
        
        colonne = trova_colonne_legacy(df)
        
        if colonne['identificativi'] is None:
            debug_print("LEGACY: Colonna identificativi non trovata")
            return []
        
        col_id = colonne['identificativi']
        col_class = colonne['classamento']
        col_ind = colonne['indirizzo']
        
        righe_processate = 0
        righe_valide = 0
        
        for row_idx, row in df.iterrows():
            try:
                # Leggi colonna identificativi
                testo_id = safe_str(row[col_id])
                
                if len(testo_id) < 10:
                    continue
                
                # Skip header
                if re.search(r'Dati\s+identificativi|Dati\s+della\s+richiesta|Situazione\s+degli\s+atti', testo_id, re.IGNORECASE):
                    continue
                
                righe_processate += 1
                
                # Estrai TUTTE le particelle dalla riga (possono essere multiple!)
                particelle_riga = estrai_tutte_particelle_da_testo(testo_id)
                
                if not particelle_riga:
                    debug_print(f"Riga {row_idx}: Nessuna particella - {testo_id[:60]}")
                    continue
                
                righe_valide += 1
                
                # Leggi colonna classamento (se esiste)
                categoria = ""
                rendita = ""
                consistenza = ""
                superficie = ""
                
                if col_class is not None:
                    testo_class = safe_str(row[col_class])
                    categoria = estrai_categoria(testo_class)
                    rendita = estrai_rendita(testo_class)
                    consistenza = estrai_consistenza(testo_class)
                    superficie = estrai_superficie(testo_class)
                
                # Leggi colonna indirizzo (se esiste)
                indirizzo = ""
                if col_ind is not None:
                    testo_ind = safe_str(row[col_ind])
                    indirizzo = estrai_indirizzo(testo_ind)
                
                # CREA UNA RIGA PER OGNI PARTICELLA TROVATA
                for particella in particelle_riga:
                    risultati.append({
                        'Foglio': particella['foglio'],
                        'Numero': particella['numero'],
                        'Sub': particella['sub'],
                        'Categoria': categoria,
                        'Consistenza': consistenza,
                        'Superficie Catastale': superficie,
                        'Rendita': rendita,
                        'Indirizzo': indirizzo
                    })
                    
                    debug_print(f"✓ Estratto: F{particella['foglio']} N{particella['numero']} S{particella['sub']} Cat{categoria}")
            
            except Exception as e:
                debug_print(f"Errore riga {row_idx}: {e}")
                continue
        
        # Statistiche legacy
        if risultati:
            indirizzi_presenti = sum(1 for r in risultati if r['Indirizzo'])
            debug_print(f"LEGACY: processate {righe_processate} righe, valide {righe_valide}, estratte {len(risultati)} unità")
            debug_print(f"Statistiche indirizzi: {indirizzi_presenti}/{len(risultati)} ({100*indirizzi_presenti/len(risultati):.1f}%)")
    
    except Exception as e:
        debug_print(f"Errore LEGACY: {e}")
    
    return risultati


# ============ FUNZIONE PRINCIPALE ============

def elabora_pdf_bytes(pdf_bytes, filename="documento.pdf"):
    """
    Elabora PDF - UNIVERSALE
    1. Prova lattice + moderno
    2. Prova lattice + legacy
    3. Prova stream + legacy
    """
    risultati = []
    
    try:
        debug_print(f"\n{'='*80}")
        debug_print(f"File: {filename}")
        debug_print(f"{'='*80}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = tmp_file.name
        
        # TENTATIVO 1: LATTICE
        try:
            debug_print("\n=== TENTATIVO 1: LATTICE ===")
            dfs_lattice = tabula.read_pdf(
                tmp_path,
                pages='all',
                multiple_tables=True,
                lattice=True,
                silent=True,
                pandas_options={'header': None}
            )
            
            if dfs_lattice:
                df_lattice = pd.concat(dfs_lattice, ignore_index=True)
                debug_print(f"Lattice: {len(df_lattice)} righe")
                
                # Prova moderno
                risultati = elabora_pdf_moderno(df_lattice)
                
                # Se fallisce, prova legacy
                if len(risultati) == 0:
                    risultati = elabora_pdf_legacy(df_lattice)
        except Exception as e:
            debug_print(f"Lattice fallito: {e}")
        
        # TENTATIVO 2: STREAM
        if len(risultati) == 0:
            try:
                debug_print("\n=== TENTATIVO 2: STREAM ===")
                dfs_stream = tabula.read_pdf(
                    tmp_path,
                    pages='all',
                    multiple_tables=True,
                    stream=True,
                    guess=False,
                    silent=True,
                    pandas_options={'header': None}
                )
                
                if dfs_stream:
                    df_stream = pd.concat(dfs_stream, ignore_index=True)
                    debug_print(f"Stream: {len(df_stream)} righe")
                    
                    risultati = elabora_pdf_legacy(df_stream)
            except Exception as e:
                debug_print(f"Stream fallito: {e}")
        
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        debug_print(f"\n{'='*80}")
        debug_print(f"FINALE: {len(risultati)} unità estratte")
        debug_print(f"{'='*80}\n")
    
    except Exception as e:
        debug_print(f"ERRORE CRITICO: {e}")
    
    return risultati

