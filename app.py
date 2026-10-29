import io
import os
import urllib.parse
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Comparatore Futuro Semplice", page_icon="⚡", layout="wide")

# =========================================================================
# STILE CSS AVANZATO
# =========================================================================
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .hero-banner {
        background: linear-gradient(135deg, #0091DA 0%, #004d7a 100%);
        padding: 24px;
        border-radius: 20px;
        color: white;
        box-shadow: 0 10px 15px -3px rgba(0, 145, 218, 0.2);
        margin-bottom: 24px;
    }
    .stButton>button {
        width: 100%;
        background-color: #8ED704;
        color: #111827;
        font-weight: 700;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #7cc203;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# INIZIALIZZAZIONE SESSION STATE
# =========================================================================
if "segmento" not in st.session_state:
    st.session_state.segmento = "Casa (Residenziale)"
if "client_name" not in st.session_state:
    st.session_state.client_name = ""
if "client_piva" not in st.session_state:
    st.session_state.client_piva = ""
if "client_name_res" not in st.session_state:
    st.session_state.client_name_res = ""
if "modo_luce" not in st.session_state:
    st.session_state.modo_luce = "Consumo Annuo (Ultimi 12 mesi)"
if "per_luce" not in st.session_state:
    st.session_state.per_luce = "1 Mese"
if "l_cons_in" not in st.session_state:
    st.session_state.l_cons_in = 0.0
if "l_cf_in" not in st.session_state:
    st.session_state.l_cf_in = 0.0
if "l_cv_curr" not in st.session_state:
    st.session_state.l_cv_curr = 0.000
if "modo_gas" not in st.session_state:
    st.session_state.modo_gas = "Consumo Annuo (Ultimi 12 mesi)"
if "per_gas" not in st.session_state:
    st.session_state.per_gas = "1 Mese"
if "g_cons_in" not in st.session_state:
    st.session_state.g_cons_in = 0.0
if "g_cf_in" not in st.session_state:
    st.session_state.g_cf_in = 0.0
if "g_cv_curr" not in st.session_state:
    st.session_state.g_cv_curr = 0.000

# =========================================================================
# CATALOGO OFFERTE UFFICIALI
# =========================================================================
OFFERTE_CATALOGO = {
    "Residenziale": {
        "Luce - SEV SUPER LUCE FIX (Prezzo Fisso 24 Mesi)": {
            "quota_fissa": 155.88,
            "materia_prima": 0.178,
            "ha_oneri_recesso": False,
            "durata": "Prezzo fisso garantito per 24 mesi"
        },
        "Luce - SORGENIA NEXT ENERGY VENTIQUATTRO (Prezzo Fisso 24 Mesi)": {
            "quota_fissa": 156.0,
            "materia_prima": 0.1768,
            "ha_oneri_recesso": False,
            "durata": "Prezzo fisso garantito per i primi 24 mesi"
        },
        "Luce - IREN LOCK&FIX (Fino al 31/12/2029 + Oneri Recesso)": {
            "quota_fissa": 147.0,
            "materia_prima": 0.155,
            "ha_oneri_recesso": True,
            "durata": "Prezzo fisso valido fino al 31/12/2029"
        },
        "Luce - IREN SOTTOCASA LUCE NEW (Fino al 31/12/2028)": {
            "quota_fissa": 159.0,
            "materia_prima": 0.1793,
            "ha_oneri_recesso": False,
            "durata": "Prezzo fisso valido fino al 31/12/2028"
        },
        "Gas - SEV SUPER GAS FIX (Prezzo Fisso 24 Mesi)": {
            "quota_fissa": 144.0,
            "materia_prima": 0.82,
            "ha_oneri_recesso": False,
            "durata": "Prezzo fisso garantito per 24 mesi"
        },
        "Gas - IREN SOTTOCASA GAS NEW (Fino al 31/12/2028)": {
            "quota_fissa": 156.0,
            "materia_prima": 0.845,
            "ha_oneri_recesso": False,
            "durata": "Prezzo fisso valido fino al 31/12/2028"
        }
    },
    "Business": {
        "Luce - IREN TUA AZIENDA LUCE FISSO (Fino al 31/12/2027)": {
            "quota_fissa": 180.0,
            "materia_prima": 0.21747,
            "ha_oneri_recesso": False,
            "durata": "Prezzo fisso valido fino al 31/12/2027"
        },
        "Luce - SORGENIA FISSO PER TE (Fino al 31/12/2029)": {
            "quota_fissa": 216.0,
            "materia_prima": 0.1826,
            "ha_oneri_recesso": True,
            "durata": "Prezzo fisso valido fino al 31/12/2029"
        },
        "Gas - IREN TUA AZIENDA GAS FISSO (Fino al 31/12/2027)": {
            "quota_fissa": 180.0,
            "materia_prima": 0.942,
            "ha_oneri_recesso": False,
            "durata": "Prezzo fisso valido fino al 31/12/2027"
        }
    }
}

# --- FUNZIONE PER GENERARE IL PDF CON IL LOGO ---
def genera_pdf_preventivo(nome_cliente, dati_riepilogo, testo_contatti, titolo_doc, tipo_cliente):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#003366'), spaceAfter=2)
    style_subtitle = ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontSize=10, leading=13, textColor=colors.HexColor('#555555'), spaceAfter=10)
    style_section_heading = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=11, leading=15, textColor=colors.HexColor('#003366'), spaceAfter=4, spaceBefore=8)
    style_body = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=9.5, leading=13, textColor=colors.HexColor('#222222'), spaceAfter=6)
    style_footer = ParagraphStyle('DocFooter', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#444444'), alignment=1)
    
    elements = []
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        img_pdf = RLImage(logo_path, width=55, height=55)
        header_text = [
            Paragraph("<b>Futuro Semplice CAF</b>", style_title),
            Paragraph(f"Preventivo e Analisi di Comparazione ({titolo_doc}) - Segmento: <b>{tipo_cliente}</b>", style_subtitle)
        ]
        header_table = Table([[img_pdf, header_text]], colWidths=[65, 475])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 0)]))
        elements.append(header_table)
    else:
        elements.append(Paragraph("<b>Futuro Semplice CAF</b>", style_title))
        elements.append(Paragraph(f"Preventivo e Analisi di Comparazione ({titolo_doc}) - Segmento: <b>{tipo_cliente}</b>", style_subtitle))
        
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#003366'), spaceAfter=12, spaceBefore=5))
    elements.append(Paragraph(f"Spett.le / Gentile <b>{nome_cliente}</b>,", style_body))
    elements.append(Paragraph("Abbiamo analizzato le Sue utenze confrontandole con le nostre soluzioni. Di seguito trova il dettaglio:", style_body))
    elements.append(Spacer(1, 4))
    
    for item in dati_riepilogo:
        elements.append(Paragraph(item['titolo_sezione'], style_section_heading))
        table_rows = [
            [Paragraph(f"<b>Offerta Selezionata:</b> {item['offerta']}", style_body), Paragraph(f"<b>Differenza / Vantaggio:</b> <font color='{'#008000' if item['risparmio'] >= 0 else '#b45309'}'><b>{item['risparmio']:+.2f} €/anno</b></font>", style_body)],
            [Paragraph(f"• Quota Fissa: {item['q_fissa']}<br/>• Materia Prima: {item['materia']}<br/>• <b>Durata Prezzo:</b> {item['durata']}", style_body), Paragraph(f"• Spesa Attuale: {item['spesa_corr']:.2f} €<br/>• Nuova Spesa: {item['spesa_off']:.2f} €", style_body)]
        ]
        if item.get('nota'):
            table_rows.append([Paragraph(f"<b>Nota importante:</b> {item['nota']}", style_body), ""])
            
        t = Table(table_rows, colWidths=[270, 270])
        style_cmds = [
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#DCDCDC')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#EFEFEF')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]
        if item.get('nota'):
            style_cmds.append(('SPAN', (0, 2), (1, 2)))
        t.setStyle(TableStyle(style_cmds))
        elements.append(t)
        elements.append(Spacer(1, 6))
        
    totale_valore = dati_riepilogo[0]['totale_risparmio'] if dati_riepilogo else 0.0
    totale_str = f"BILANCIO ECONOMICO ANNUO STIMATO: {totale_valore:+.2f} €"
    t_totale = Table([[Paragraph(f"<b><font size=10 color='#003366'>{totale_str}</font></b>", ParagraphStyle('Center', alignment=1))]], colWidths=[540])
    t_totale.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EAEFF5')), ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#003366')), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
    elements.append(t_totale)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Siamo a Sua completa disposizione per supportarLa in modo semplice e veloce.", style_body))
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CCCCCC'), spaceAfter=8))
    contatti_formatted = testo_contatti.replace('\n', '<br/>')
    elements.append(Paragraph(contatti_formatted, style_footer))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- BARRA LATERALE CON LOGO ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    st.markdown("### 🔵🟢 Futuro Semplice")
    st.write("Consulenza energetica, CAF e Patronato.")
    st.markdown("---")
    st.markdown("💡 **Come funziona:**")
    st.markdown("1. Scegli se sei Casa o Business.")
    st.markdown("2. Inserisci i dati della tua bolletta.")
    st.markdown("3. Scopri l'analisi, scarica il PDF o contattaci su WhatsApp.")

# --- HERO BANNER ---
st.markdown("""
    <div class="hero-banner">
        <span style="background-color: #8ED704; color: #111827; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 800; text-transform: uppercase;">⚡ Tariffa Bloccata 2026</span>
        <h1 style="margin-top: 10px; margin-bottom: 5px; color: white; font-size: 26px;">Analizza i tuoi Consumi</h1>
        <p style="font-size: 14px; margin: 0; color: #e0f2fe;">Inserisci i dati della tua bolletta e scopri subito i vantaggi delle nostre offerte a prezzo fisso.</p>
    </div>
""", unsafe_allow_html=True)

segmento_opzioni = ["Casa (Residenziale)", "Business (Partita IVA)"]
segmento_scelto = st.radio(
    "🎯 Seleziona la tipologia di utenza:",
    segmento_opzioni,
    index=segmento_opzioni.index(st.session_state.segmento) if st.session_state.segmento in segmento_opzioni else 0,
    horizontal=True,
    key="segmento"
)

is_business = "Business" in segmento_scelto
cat_attivo = "Business" if is_business else "Residenziale"

st.markdown("### 📋 I tuoi dati di riferimento")
if is_business:
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        client_name = st.text_input("Ragione Sociale", placeholder="Es. Rossi Srl", key="client_name")
    with col_a2:
        client_piva = st.text_input("Partita IVA", placeholder="Es. 01234567890", key="client_piva")
    nome_visualizzato = f"{client_name} (P.IVA: {client_piva})" if client_name and client_piva else (client_name if client_name else "[Azienda Cliente]")
else:
    client_name = st.text_input("Nome e Cognome", placeholder="Es. Mario Rossi", key="client_name_res")
    nome_visualizzato = client_name if client_name else "[Nome Cliente]"

st.markdown("---")

if is_business:
    tab_luce, tab_gas = st.tabs(["💡 Utenza Luce (Business)", "🔥 Utenza Gas (Business)"])
else:
    tab_luce, tab_gas = st.tabs(["💡 Utenza Luce", "🔥 Utenza Gas"])

# ==================== SEZIONE LUCE ====================
with tab_luce:
    st.subheader(f"Confronto Utenza Luce ({cat_attivo})")
    offerte_luce_disponibili = [k for k in OFFERTE_CATALOGO[cat_attivo].keys() if "Luce" in k]
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.markdown("#### 📄 Dati della tua Bolletta Luce")
        modo_calcolo_luce = st.radio(
            "Modalità di inserimento consumo Luce:",
            ["Consumo Annuo (Ultimi 12 mesi)", "Singola Bolletta (Periodo)"],
            key="modo_luce"
        )
        
        if modo_calcolo_luce == "Singola Bolletta (Periodo)":
            periodo_luce = st.selectbox("A che periodo si riferisce la bolletta?", ["1 Mese", "2 Mesi (Bimestrale)"], key="per_luce")
            fattore_moltiplicativo_luce = 12.0 if periodo_luce == "1 Mese" else 6.0
        else:
            fattore_moltiplicativo_luce = 1.0
            
        consumo_input_luce = st.number_input("Consumo Luce (kWh)", step=100.0, key="l_cons_in", help="Somma totale (F1 + F2 + F3).")
        luce_consumo = consumo_input_luce * fattore_moltiplicativo_luce
        if fattore_moltiplicativo_luce > 1.0:
            st.caption(f"🔄 Consumo stimato su base annua: **{luce_consumo:,.0f} kWh/anno**")
        
        if modo_calcolo_luce == "Singola Bolletta (Periodo)":
            st.caption("💡 *Nota: Se inserisci la quota fissa mensile/bimestrale, ricorda che verrà moltiplicata per 12 (o rapportata all'anno) per il calcolo della comparazione annuale.*")
        else:
            st.caption("💡 *Inserisci la quota fissa totale su base annua.*")

        luce_curr_fixed_input = st.number_input("Quota Fissa (€)", step=1.0, key="l_cf_in")
        luce_curr_fixed = luce_curr_fixed_input * fattore_moltiplicativo_luce
        
        luce_curr_var = st.number_input("Costo Materia Prima Attuale (€/kWh)", format="%.4f", key="l_cv_curr")
        
    with col_l2:
        st.markdown(f"#### ⚡ Offerta Futuro Semplice")
        scelta_offerta_luce = st.selectbox("Seleziona l'offerta da confrontare", offerte_luce_disponibili, key="sel_luce")
        
        luce_offer_fixed = OFFERTE_CATALOGO[cat_attivo][scelta_offerta_luce]["quota_fissa"]
        luce_offer_var = OFFERTE_CATALOGO[cat_attivo][scelta_offerta_luce]["materia_prima"]
        luce_durata_str = OFFERTE_CATALOGO[cat_attivo][scelta_offerta_luce]["durata"]
        
        st.metric(label="Quota Fissa Offerta", value=f"{luce_offer_fixed:.2f} €/anno")
        st.metric(label="Materia Prima Offerta", value=f"{luce_offer_var:.4f} €/kWh")
        st.info(f"⏳ **Durata:** {luce_durata_str}")
        
        if OFFERTE_CATALOGO[cat_attivo][scelta_offerta_luce]["ha_oneri_recesso"]:
            st.warning("⚠️ Condizioni a prezzo fisso con eventuali oneri di recesso anticipato.")
        else:
            st.success("✅ Nessun onere di recesso previsto.")

    dati_luce_completi = (consumo_input_luce > 0) and (luce_curr_fixed_input > 0) and (luce_curr_var > 0)

    if dati_luce_completi:
        spesa_curr_luce = luce_curr_fixed + (luce_consumo * luce_curr_var)
        spesa_off_luce = luce_offer_fixed + (luce_consumo * luce_offer_var)
        risparmio_luce = spesa_curr_luce - spesa_off_luce
        durata_luce_raw = OFFERTE_CATALOGO[cat_attivo][scelta_offerta_luce]["durata"]
        
        if risparmio_luce > 10:
            st.success(f"💡 **Risparmio Annuo Stimato Luce:** **+{risparmio_luce:.2f} €** (Spesa attuale: {spesa_curr_luce:.2f} € vs Nuova: {spesa_off_luce:.2f} €). *Oltre al risparmio immediato, goditi la totale tranquillità di una tariffa a prezzo fisso protetta dai rincari!*")
        elif -10 <= risparmio_luce <= 10:
            st.info(f"⚖️ **Prezzo allineato ({risparmio_luce:+.2f} €/anno):** La spesa è allineata a quella attuale, ma bloccare il prezzo ({durata_luce_raw}) ti garantisce la sicurezza di non subire le oscillazioni e i rincari del mercato libero.")
        else:
            st.info(f"🛡️ **Prezzo bloccato di sicurezza:** Questa offerta comporta una variazione di {-risparmio_luce:.2f} €/anno. Tuttavia, in un mercato in continuo aumento, sottoscrivere un contratto a prezzo fisso bloccato ({durata_luce_raw}) rappresenta una garanzia fondamentale per il futuro.")
    else:
        spesa_curr_luce = 0.0
        spesa_off_luce = 0.0
        risparmio_luce = 0.0
        st.caption("ℹ️ Inserisci i tre campi della bolletta (Consumo, Quota Fissa e Costo Materia Prima) per visualizzare l'analisi dettagliata.")

# ==================== SEZIONE GAS ====================
with tab_gas:
    st.subheader(f"Confronto Utenza Gas ({cat_attivo})")
    offerte_gas_disponibili = [k for k in OFFERTE_CATALOGO[cat_attivo].keys() if "Gas" in k]
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("#### 📄 Dati della tua Bolletta Gas")
        if offerte_gas_disponibili:
            modo_calcolo_gas = st.radio(
                "Modalità di inserimento consumo Gas:",
                ["Consumo Annuo (Ultimi 12 mesi)", "Singola Bolletta (Periodo)"],
                key="modo_gas"
            )
            if modo_calcolo_gas == "Singola Bolletta (Periodo)":
                periodo_gas = st.selectbox("A che periodo si riferisce la bolletta?", ["1 Mese", "2 Mesi (Bimestrale)"], key="per_gas")
                fattore_moltiplicativo_gas = 12.0 if periodo_gas == "1 Mese" else 6.0
            else:
                fattore_moltiplicativo_gas = 1.0
                
            consumo_input_gas = st.number_input("Consumo Gas (Smc)", step=50.0, key="g_cons_in")
            gas_consumo = consumo_input_gas * fattore_moltiplicativo_gas
            if fattore_moltiplicativo_gas > 1.0:
                st.caption(f"🔄 Consumo stimato su base annua: **{gas_consumo:,.0f} Smc/anno**")
            
            if modo_calcolo_gas == "Singola Bolletta (Periodo)":
                st.caption("💡 *Nota: Se inserisci la quota fissa mensile/bimestrale, ricorda che verrà moltiplicata per 12 (o rapportata all'anno) per il calcolo della comparazione annuale.*")
            else:
                st.caption("💡 *Inserisci la quota fissa totale su base annua.*")

            gas_curr_fixed_input = st.number_input("Quota Fissa (€)", step=1.0, key="g_cf_in")
            gas_curr_fixed = gas_curr_fixed_input * fattore_moltiplicativo_gas
            
            gas_curr_var = st.number_input("Costo Materia Prima Attuale (€/Smc)", format="%.3f", key="g_cv_curr")
        else:
            gas_consumo = 0.0
            gas_curr_fixed = 0.0
            gas_curr_var = 0.0
            consumo_input_gas = 0.0
            gas_curr_fixed_input = 0.0
            gas_curr_var = 0.0
            
    with col_g2:
        st.markdown(f"#### 🔥 Offerta Futuro Semplice")
        if offerte_gas_disponibili:
            scelta_offerta_gas = st.selectbox("Seleziona l'offerta da confrontare", offerte_gas_disponibili, key="sel_gas")
            gas_offer_fixed = OFFERTE_CATALOGO[cat_attivo][scelta_offerta_gas]["quota_fissa"]
            gas_offer_var = OFFERTE_CATALOGO[cat_attivo][scelta_offerta_gas]["materia_prima"]
            gas_durata_str = OFFERTE_CATALOGO[cat_attivo][scelta_offerta_gas]["durata"]
            
            st.metric(label="Quota Fissa Offerta", value=f"{gas_offer_fixed:.2f} €/anno")
            st.metric(label="Materia Prima Offerta", value=f"{gas_offer_var:.3f} €/Smc")
            st.info(f"⏳ **Durata:** {gas_durata_str}")
        else:
            st.info("Nessuna offerta gas disponibile al momento per questo segmento.")
            scelta_offerta_gas = ""
            gas_offer_fixed = 0.0
            gas_offer_var = 0.0

    dati_gas_completi = (consumo_input_gas > 0) and (gas_curr_fixed_input > 0) and (gas_curr_var > 0) if offerte_gas_disponibili else False

    if offerte_gas_disponibili and dati_gas_completi:
        spesa_curr_gas = gas_curr_fixed + (gas_consumo * gas_curr_var)
        spesa_off_gas = gas_offer_fixed + (gas_consumo * gas_offer_var)
        risparmio_gas = spesa_curr_gas - spesa_off_gas
        durata_gas_raw = OFFERTE_CATALOGO[cat_attivo][scelta_offerta_gas]["durata"]
        
        if risparmio_gas > 10:
            st.success(f"🔥 **Risparmio Annuo Stimato Gas:** **+{risparmio_gas:.2f} €** (Spesa attuale: {spesa_curr_gas:.2f} € vs Nuova: {spesa_off_gas:.2f} €). *Oltre al risparmio, bloccando il prezzo ti metti al sicuro da future impennate del gas!*")
        elif -10 <= risparmio_gas <= 10:
            st.info(f"⚖️ **Prezzo allineato ({risparmio_gas:+.2f} €/anno):** Variazione minima, ma bloccare il prezzo ({durata_gas_raw}) ti offre la massima tranquillità contro i rincari.")
        else:
            st.info(f"🛡️ **Prezzo bloccato di sicurezza:** Questa offerta comporta una differenza di {-risparmio_gas:.2f} €/anno. Tuttavia, bloccare il prezzo in un mercato energetico volatile è una scelta intelligente e sicura per il futuro.")
    else:
        spesa_curr_gas = 0.0
        spesa_off_gas = 0.0
        risparmio_gas = 0.0
        if offerte_gas_disponibili:
            st.caption("ℹ️ Inserisci i tre campi della bolletta Gas (Consumo, Quota Fissa e Costo Materia Prima) per visualizzare l'analisi.")

# ==================== RIEPILOGO & DOWNLOAD PDF ====================
ha_dati_utili = (dati_luce_completi or dati_gas_completi)

if ha_dati_utili:
    st.markdown("---")
    st.subheader("📊 Report di Sintesi & Azioni")

    ha_luce = dati_luce_completi
    ha_gas = dati_gas_completi and len(offerte_gas_disponibili) > 0

    risparmio_totale = 0.0
    if ha_luce:
        risparmio_totale += risparmio_luce
    if ha_gas:
        risparmio_totale += risparmio_gas

    if ha_luce and ha_gas:
        tipo_utenza_str = "Luce e Gas"
    elif ha_luce:
        tipo_utenza_str = "Luce"
    else:
        tipo_utenza_str = "Gas"

    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="💰 Bilancio Economico Annuo Complessivo", value=f"{risparmio_totale:+.2f} €", delta="Prezzo allineato" if -10 <= risparmio_totale <= 10 else ("Vantaggio attivo" if risparmio_totale > 10 else "Prezzo bloccato di sicurezza"))
    with m2:
        st.metric(label="👤 Intestatario / Utente", value=nome_visualizzato if nome_visualizzato else "Non specificato")

    filename_pdf = f"Comparazione Energia Futuro Semplice ({segmento_scelto}).pdf"
    dati_pdf_struttura = []

    if ha_luce:
        nota_recesso_l = "Condizioni a prezzo fisso con eventuali oneri applicabili in caso di recesso anticipato." if OFFERTE_CATALOGO[cat_attivo][scelta_offerta_luce]["ha_oneri_recesso"] else ""
        dati_pdf_struttura.append({
            'titolo_sezione': f"💡 Utenza Luce ({segmento_scelto})",
            'offerta': scelta_offerta_luce,
            'risparmio': risparmio_luce,
            'q_fissa': f"{luce_offer_fixed:.2f} €/anno",
            'materia': f"{luce_offer_var:.4f} €/kWh",
            'durata': OFFERTE_CATALOGO[cat_attivo][scelta_offerta_luce]["durata"],
            'spesa_corr': spesa_curr_luce,
            'spesa_off': spesa_off_luce,
            'nota': nota_recesso_l,
            'totale_risparmio': risparmio_totale
        })

    if ha_gas:
        dati_pdf_struttura.append({
            'titolo_sezione': f"🔥 Utenza Gas ({segmento_scelto})",
            'offerta': scelta_offerta_gas,
            'risparmio': risparmio_gas,
            'q_fissa': f"{gas_offer_fixed:.2f} €/anno",
            'materia': f"{gas_offer_var:.3f} €/Smc",
            'durata': OFFERTE_CATALOGO[cat_attivo][scelta_offerta_gas]["durata"],
            'spesa_corr': spesa_curr_gas,
            'spesa_off': spesa_off_gas,
            'nota': "",
            'totale_risparmio': risparmio_totale
        })

    recapiti_testo = "<b>Futuro Semplice CAF Patronato Assicurazioni Luce & GAS Telefonia</b><br/>Via Ungaretti 1/b - Corropoli (TE)<br/>Tel: 331-1776713 | Email: tsp301@team-service.it"

    testo_completo_anteprima = f"Cliente: {nome_visualizzato} ({segmento_scelto})\n\n"
    if ha_luce:
        testo_completo_anteprima += f"• Luce ({scelta_offerta_luce}) -> Differenza: {risparmio_luce:+.2f} €/anno [{OFFERTE_CATALOGO[cat_attivo][scelta_offerta_luce]['durata']}]\n"
    if ha_gas:
        testo_completo_anteprima += f"• Gas ({scelta_offerta_gas}) -> Differenza: {risparmio_gas:+.2f} €/anno [{OFFERTE_CATALOGO[cat_attivo][scelta_offerta_gas]['durata']}]\n"

    testo_completo_anteprima += f"\n💰 Bilancio Annuo Complessivo: {risparmio_totale:+.2f} €\n\n---------------------------------------------\nFuturo Semplice CAF Patronato Assicurazioni Luce & GAS Telefonia\nVia Ungaretti 1/b - Corropoli (TE)\nTel: 331-1776713 | Email: tsp301@team-service.it"

    with st.expander("🔍 Visualizza Anteprima Testo Preventivo"):
        st.text_area("Testo grezzo per copia/incolla:", value=testo_completo_anteprima, height=160)

    # ==================== PULSANTI IN BASSO ====================
    st.write("")
    col_pdf, col_wa, col_reset, col_esci = st.columns([2, 2, 1, 1])

    with col_pdf:
        pdf_file = genera_pdf_preventivo(nome_visualizzato, dati_pdf_struttura, recapiti_testo, tipo_utenza_str, segmento_scelto)
        st.download_button(
            label=f"📥 Scarica Preventivo PDF",
            data=pdf_file,
            file_name=filename_pdf,
            mime="application/pdf",
            type="primary"
        )

    with col_wa:
        testo_wa = f"Salve, sono {nome_visualizzato}. Ho effettuato un'analisi per {tipo_utenza_str} con un bilancio stimato di {risparmio_totale:+.2f} €/anno. Vorrei bloccare il prezzo e procedere."
        link_wa = f"https://wa.me/393311776713?text={urllib.parse.quote(testo_wa)}"
        st.markdown(f"""
            <a href="{link_wa}" target="_blank">
                <button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:10px; font-weight:bold; cursor:pointer; text-align:center;">
                    💬 Invia su WhatsApp
                </button>
            </a>
        """, unsafe_allow_html=True)

    with col_reset:
        if st.button("🔄 Reset"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    with col_esci:
        st.markdown(
            '<a href="https://futurosemplicecaf.altervista.org/" target="_self"><button style="width:100%; background-color:#ef4444; color:white; border:none; padding:10px; border-radius:10px; font-weight:bold; cursor:pointer;">🚪 Esci</button></a>',
            unsafe_allow_html=True
        )
else:
    st.markdown("---")
    col_res, col_esc = st.columns([1, 1])
    with col_res:
        if st.button("🔄 Reset Campi"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col_esc:
        st.markdown(
            '<a href="https://futurosemplicecaf.altervista.org/" target="_self"><button style="width:100%; background-color:#ef4444; color:white; border:none; padding:10px; border-radius:10px; font-weight:bold; cursor:pointer;">🚪 Esci</button></a>',
            unsafe_allow_html=True
        )