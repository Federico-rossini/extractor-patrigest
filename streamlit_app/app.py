# -*- coding: utf-8 -*-
"""
EXTRACTOR WEB APP v1.0
Estrattore Dati Catastali - Interfaccia Web
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os
from extractor_logic import elabora_pdf_bytes

# ============ CONFIGURAZIONE PAGINA ============
st.set_page_config(
    page_title="EXTRACTOR - Patrigest",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ STILI CUSTOM PATRIGEST ============
st.markdown("""
<style>
    /* Colori Patrigest */
    :root {
        --patrigest-red: #B20933;
        --patrigest-dark: #8A0726;
        --patrigest-light: #FFE6ED;
    }
    
    /* Header principale */
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #B20933;
        text-align: center;
        padding: 1rem 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Box colorati */
    .success-box {
        padding: 1.5rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .info-box {
        padding: 1.5rem;
        background-color: #FFE6ED;
        border-left: 5px solid #B20933;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Bottoni */
    .stButton button {
        background-color: #B20933 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        background-color: #8A0726 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(178, 9, 51, 0.3);
    }
    
    /* Download button specifico */
    .stDownloadButton button {
        background-color: #28a745 !important;
        width: 100%;
    }
    
    .stDownloadButton button:hover {
        background-color: #218838 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #B20933;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #B20933;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #B20933;
        font-size: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ============ SIDEBAR ============
with st.sidebar:
    # Loghi Patrigest + RICS
    logo_path_base = os.path.join(os.path.dirname(__file__), "IMG")
    
    # Logo principale Patrigest
    logo_patrigest = os.path.join(logo_path_base, "logo.jpg")
    if os.path.exists(logo_patrigest):
        try:
            st.image(logo_patrigest, use_container_width=True)
        except:
            pass
    
    # Logo RICS (sotto)
    logo_rics = os.path.join(logo_path_base, "logoRICS.jpg")
    if os.path.exists(logo_rics):
        try:
            st.image(logo_rics, use_container_width=True)
        except:
            pass
    
    # Fallback se nessun logo caricato
    if not os.path.exists(logo_patrigest) and not os.path.exists(logo_rics):
        st.markdown("""
        <div style='background: linear-gradient(135deg, #B20933 0%, #8A0726 100%); 
                    padding: 30px; 
                    text-align: center; 
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h1 style='color: white; 
                       margin: 0; 
                       font-size: 2.5rem;
                       font-weight: bold;
                       letter-spacing: 3px;'>PATRIGEST</h1>
            <p style='color: rgba(255,255,255,0.9); 
                      margin: 10px 0 0 0;
                      font-size: 0.9rem;'>Servizi Immobiliari</p>
        </div>
        """, unsafe_allow_html=True)


    
    st.markdown("---")
    
    st.markdown("### 📖 Come Funziona")
    st.markdown("""
    **Passo 1:** Carica uno o più PDF di visure catastali
    
    **Passo 2:** Clicca "Elabora"
    
    **Passo 3:** Scarica il CSV
    
    ✅ Supporta formati moderni e legacy  
    ✅ Elaborazione batch (anche 50+ PDF)  
    ✅ Export pronto per Excel
    """)
    
    st.markdown("---")
    
    st.markdown("### 🔍 Dati Estratti")
    st.markdown("""
    - **Foglio, Numero, Sub**
    - **Categoria catastale**
    - **Consistenza** (vani/mq)
    - **Superficie catastale**
    - **Rendita catastale**
    - **Indirizzo**
    """)
    
    st.markdown("---")
    
    st.markdown("### ℹ️ Info")
    st.markdown("""
    **Versione:** 1.0  
    **Sviluppato da:** Patrigest  
    **Data:** Febbraio 2026  
    """)
    
    st.markdown("---")
    
    # Statistiche sessione
    if 'total_processed' not in st.session_state:
        st.session_state.total_processed = 0
    if 'total_units' not in st.session_state:
        st.session_state.total_units = 0
    
    st.markdown("### 📊 Questa Sessione")
    col1, col2 = st.columns(2)
    col1.metric("PDF", st.session_state.total_processed)
    col2.metric("Unità", st.session_state.total_units)
    
    st.markdown("---")
    st.caption("© 2026 Patrigest | EXTRACTOR v1.0")

# ============ HEADER ============
st.markdown('<div class="main-header">📊 EXTRACTOR</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Estrattore Automatico Dati Catastali</div>', unsafe_allow_html=True)
st.markdown("---")


# ============ UPLOAD SECTION ============
st.subheader("📁 Carica Visure Catastali")

uploaded_files = st.file_uploader(
    "Trascina qui i PDF oppure clicca per sfogliare",
    type=['pdf'],
    accept_multiple_files=True,
    help="Puoi caricare uno o più file PDF contemporaneamente (anche 50+)"
)

# Mostra file caricati
if uploaded_files:
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown(f"**✓ {len(uploaded_files)} PDF caricati**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander(f"📋 Visualizza lista ({len(uploaded_files)} file)"):
        for idx, f in enumerate(uploaded_files, 1):
            size_kb = f.size / 1024
            st.write(f"{idx}. **{f.name}** ({size_kb:.1f} KB)")

# ============ ELABORAZIONE ============
if uploaded_files:
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        elabora_btn = st.button(
            "🚀 ELABORA PDF",
            type="primary",
            use_container_width=True,
            help="Avvia l'estrazione dati da tutti i PDF caricati"
        )
    
    if elabora_btn:
        
        st.markdown("---")
        st.subheader("⚙️ Elaborazione in Corso")
        
        # Container per progress
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            tutti_dati = []
            pdf_ok = 0
            pdf_errori = 0
            
            # Elabora ogni PDF
            for idx, pdf_file in enumerate(uploaded_files):
                
                current_progress = (idx / len(uploaded_files))
                progress_bar.progress(current_progress)
                status_text.info(f"📄 Elaborazione: **{pdf_file.name}** ({idx+1}/{len(uploaded_files)})")
                
                try:
                    # Leggi bytes del PDF
                    pdf_bytes = pdf_file.read()
                    
                    # Elabora PDF
                    dati = elabora_pdf_bytes(pdf_bytes, pdf_file.name)
                    
                    if dati:
                        tutti_dati.extend(dati)
                        pdf_ok += 1
                        status_text.success(f"✓ {pdf_file.name}: {len(dati)} unità estratte")
                    else:
                        pdf_errori += 1
                        status_text.warning(f"⚠️ {pdf_file.name}: Nessun dato estratto")
                
                except Exception as e:
                    pdf_errori += 1
                    status_text.error(f"❌ {pdf_file.name}: Errore - {str(e)[:100]}")
            
            # Completa progress
            progress_bar.progress(1.0)
            status_text.success(f"✅ Elaborazione completata! ({pdf_ok}/{len(uploaded_files)} PDF elaborati con successo)")
        
        st.markdown("---")
        
        # ============ RISULTATI ============
        if tutti_dati:
            
            # Crea DataFrame
            df_finale = pd.DataFrame(tutti_dati)
            
            # Rimuovi duplicati
            before_dedup = len(df_finale)
            df_finale.drop_duplicates(subset=['Foglio', 'Numero', 'Sub'], keep='first', inplace=True)
            after_dedup = len(df_finale)
            
            # Aggiorna statistiche sessione
            st.session_state.total_processed += len(uploaded_files)
            st.session_state.total_units += len(df_finale)
            
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown("### ✅ ESTRAZIONE COMPLETATA")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Metriche
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="📊 Unità Totali",
                    value=len(df_finale),
                    delta=f"-{before_dedup - after_dedup} duplicati" if before_dedup > after_dedup else "Nessun duplicato"
                )
            
            with col2:
                fogli_unici = df_finale['Foglio'].nunique()
                st.metric(
                    label="🗂️ Fogli",
                    value=fogli_unici
                )
            
            with col3:
                particelle_uniche = df_finale['Numero'].nunique()
                st.metric(
                    label="📍 Particelle",
                    value=particelle_uniche
                )
            
            with col4:
                categorie_uniche = df_finale['Categoria'].nunique()
                st.metric(
                    label="🏠 Categorie",
                    value=categorie_uniche
                )
            
            # Statistiche categorie
            st.markdown("---")
            st.subheader("📈 Distribuzione Categorie")
            
            cat_counts = df_finale['Categoria'].value_counts()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.bar_chart(cat_counts)
            
            with col2:
                st.dataframe(
                    cat_counts.reset_index().rename(columns={'index': 'Categoria', 'Categoria': 'Conteggio'}),
                    hide_index=True,
                    use_container_width=True
                )
            
            # Anteprima dati
            st.markdown("---")
            st.subheader("🔍 Anteprima Dati")
            
            # Filtri
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fogli_disponibili = ['Tutti'] + sorted(df_finale['Foglio'].unique().tolist())
                foglio_filter = st.selectbox("Filtra per Foglio", fogli_disponibili)
            
            with col2:
                categorie_disponibili = ['Tutte'] + sorted(df_finale['Categoria'].unique().tolist())
                categoria_filter = st.selectbox("Filtra per Categoria", categorie_disponibili)
            
            with col3:
                n_righe = st.slider("Righe da visualizzare", 10, 100, 20)
            
            # Applica filtri
            df_filtered = df_finale.copy()
            
            if foglio_filter != 'Tutti':
                df_filtered = df_filtered[df_filtered['Foglio'] == foglio_filter]
            
            if categoria_filter != 'Tutte':
                df_filtered = df_filtered[df_filtered['Categoria'] == categoria_filter]
            
            st.dataframe(
                df_filtered.head(n_righe),
                use_container_width=True,
                hide_index=True
            )
            
            st.caption(f"Visualizzate {min(n_righe, len(df_filtered))} di {len(df_filtered)} unità (dopo filtri)")
            
            # ============ DOWNLOAD ============
            st.markdown("---")
            st.subheader("📥 Scarica Risultati")
            
            # Genera CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f"Dati_Catastali_{timestamp}.csv"
            
            # Converte DataFrame in CSV
            csv_buffer = io.StringIO()
            df_finale.to_csv(csv_buffer, index=False, encoding='utf-8-sig', sep=';')
            csv_bytes = csv_buffer.getvalue().encode('utf-8-sig')
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.download_button(
                    label=f"📥 SCARICA CSV ({len(df_finale)} unità)",
                    data=csv_bytes,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True,
                    help="Scarica il file CSV con tutti i dati estratti"
                )
            
            # Info file
            st.info(f"""
            **File:** {csv_filename}  
            **Formato:** CSV (separatore: punto e virgola)  
            **Encoding:** UTF-8 con BOM  
            **Dimensione:** {len(csv_bytes) / 1024:.1f} KB
            """)
            
            # Tabella riepilogo
            with st.expander("📊 Riepilogo Completo"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📁 Elaborazione**")
                    st.write(f"- PDF caricati: {len(uploaded_files)}")
                    st.write(f"- PDF elaborati con successo: {pdf_ok}")
                    st.write(f"- PDF con errori: {pdf_errori}")
                    st.write(f"- Unità totali estratte: {len(df_finale)}")
                
                with col2:
                    st.markdown("**🗂️ Dati Estratti**")
                    fogli = sorted([str(f) for f in df_finale['Foglio'].unique() if str(f)])
                    st.write(f"- Fogli: {', '.join(fogli[:5])}" + (" ..." if len(fogli) > 5 else ""))
                    
                    categorie = sorted([str(c) for c in df_finale['Categoria'].unique() if str(c)])
                    st.write(f"- Categorie: {', '.join(categorie)}")
                    
                    sup_ok = len(df_finale[df_finale['Superficie Catastale'] != ''])
                    cons_ok = len(df_finale[df_finale['Consistenza'] != ''])
                    st.write(f"- Con superficie: {sup_ok}/{len(df_finale)} ({sup_ok*100//len(df_finale)}%)")
                    st.write(f"- Con consistenza: {cons_ok}/{len(df_finale)} ({cons_ok*100//len(df_finale)}%)")
        
        else:
            st.error("❌ Nessun dato estratto da nessuno dei PDF caricati.")
            st.markdown("""
            **Possibili cause:**
            - I PDF non sono visure catastali dell'Agenzia delle Entrate
            - I PDF sono protetti da password
            - Formato PDF non riconosciuto
            - PDF corrotti o danneggiati
            
            **Prova a:**
            - Verificare che siano visure catastali standard
            - Aprire i PDF manualmente per controllare il contenuto
            - Usare PDF diversi
            """)

else:
    # Messaggio iniziale
    st.info("👆 **Carica uno o più PDF per iniziare l'estrazione**")
    
    # Esempio
    with st.expander("💡 Esempio di utilizzo"):
        st.markdown("""
        **Scenario tipico:**
        
        1. Ricevi 15 visure catastali via email
        2. Salvi tutti i PDF in una cartella
        3. Trascini tutti i 15 PDF qui
        4. Clicchi "Elabora"
        5. Dopo 30-60 secondi scarichi 1 CSV con tutte le 300+ unità
        
        **Tempo risparmiato:** Da 4 ore di lavoro manuale a 2 minuti! ⚡
        """)

# ============ FOOTER ============
st.markdown("---")
st.caption("EXTRACTOR v1.0 | Estrattore Automatico Dati Catastali | © 2026")
