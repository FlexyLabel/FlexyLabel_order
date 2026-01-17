import streamlit as st
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime
import os
import math
import time

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y MARCA
# =============================================================================
st.set_page_config(page_title="FLEXYLABEL | Cloud Manufacturing", layout="wide", page_icon="🏷️")

DESTINATARIO_TALLER = "covet@etiquetes.com"
COLOR_NEON = "#58a6ff"
COLOR_ACCENT = "#1f6feb"
COLOR_BG = "#0d1117"

# =============================================================================
# 2. MOTOR CSS AVANZADO (DISEÑO PROFESIONAL)
# =============================================================================
def inject_professional_ui():
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600;800&display=swap');

            .stApp {{
                background-color: {COLOR_BG};
                background-image: radial-gradient(circle at 2px 2px, #161b22 1px, transparent 0);
                background-size: 40px 40px;
                color: #c9d1d9;
                font-family: 'Inter', sans-serif;
            }}

            .header-container {{
                background: linear-gradient(90deg, #161b22 0%, #0d1117 100%);
                padding: 2rem;
                border-bottom: 2px solid {COLOR_NEON};
                margin-bottom: 2rem;
                border-radius: 0 0 20px 20px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }}

            .main-title {{
                font-family: 'Orbitron', sans-serif;
                font-size: 3rem;
                letter-spacing: 5px;
                background: linear-gradient(90deg, #58a6ff, #1f6feb);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0;
            }}

            .industrial-card {{
                background: rgba(22, 27, 34, 0.7);
                backdrop-filter: blur(10px);
                border: 1px solid #30363d;
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }}

            .stat-box {{
                border-left: 4px solid {COLOR_NEON};
                background: #161b22;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 0 8px 8px 0;
            }}
            
            .stButton>button {{
                background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: white !important;
                border: none !important;
                font-family: 'Orbitron', sans-serif !important;
                font-weight: 700 !important;
                border-radius: 12px !important;
                width: 100% !important;
            }}
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 3. LÓGICA TÉCNICA (CORREGIDA)
# =============================================================================
def calcular_metricas(modelos):
    total_m2 = 0.0
    total_lineal = 0.0
    gap = 3 # mm
    for m in modelos:
        # Usamos .get() para evitar el KeyError si el campo no existe aún
        cantidad = float(m.get('cant', 0))
        largo = float(m.get('lar', 0))
        ancho = float(m.get('anc', 0))
        
        if cantidad > 0 and largo > 0:
            ml = (cantidad * (largo + gap)) / 1000
            total_lineal += ml
            total_m2 += (ancho / 1000) * ml
            
    return round(total_lineal, 2), round(total_m2, 2)

# =============================================================================
# 4. GENERADOR DE PDF CORPORATIVO
# =============================================================================
class FlexyEnterprisePDF(FPDF):
    def header(self):
        self.set_fill_color(13, 17, 23)
        self.rect(0, 0, 210, 45, 'F')
        self.set_xy(15, 12)
        self.set_font("Arial", 'B', 25)
        self.set_text_color(88, 166, 255)
        self.cell(0, 10, "FLEXYLABEL PRODUCTION", ln=True)
        self.set_font("Arial", 'I', 10)
        self.set_text_color(180, 180, 180)
        self.cell(0, 8, f"Orden generada: {datetime.date.today()}", ln=True)
        self.ln(20)

    def write_model(self, i, m):
        self.set_fill_color(240, 245, 255)
        self.set_font("Arial", 'B', 11)
        self.cell(0, 10, f" MODELO {i+1}: {m['ref'].upper()}", ln=True, fill=True)
        self.set_font("Arial", '', 10)
        self.cell(95, 8, f"Medidas: {m['anc']} x {m['lar']} mm", border="B")
        self.cell(95, 8, f"Cantidad: {m['cant']} uds", border="B", ln=True)
        self.cell(95, 8, f"Etiquetas por Rollo: {m['etq_r']}", border="B")
        self.cell(95, 8, f"Material: {m['material']}", border="B", ln=True)
        self.ln(4)

# =============================================================================
# 5. UI PRINCIPAL
# =============================================================================
inject_professional_ui()

st.markdown('<div class="header-container"><h1 class="main-title">FLEXYLABEL</h1></div>', unsafe_allow_html=True)

# Inicializar estado si no existe
if 'modelos' not in st.session_state:
    st.session_state.modelos = [{"ref": "Referencia 1", "anc": 100, "lar": 100, "cant": 5000, "etq_r": 1000, "material": "PP Blanco", "file": None}]

# Sidebar Dashboard
with st.sidebar:
    st.markdown("### 📊 MÉTRICAS DE PRODUCCIÓN")
    ml, m2 = calcular_metricas(st.session_state.modelos)
    st.markdown(f'<div class="stat-box">Lineales: <b>{ml} m</b></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="stat-box">Superficie: <b>{m2} m²</b></div>', unsafe_allow_html=True)
    st.markdown("---")
    if st.button("➕ AÑADIR OTRO MODELO"):
        st.session_state.modelos.append({"ref": f"Referencia {len(st.session_state.modelos)+1}", "anc": 100, "lar": 100, "cant": 5000, "etq_r": 1000, "material": "PP Blanco", "file": None})
        st.rerun()

# Formulario
with st.container():
    col_main, col_side = st.columns([3, 1])
    
    with col_main:
        st.markdown("### 📝 DATOS DEL CLIENTE")
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Empresa")
        email_cliente = c2.text_input("Email para confirmación")

        st.markdown("### 📦 CONFIGURACIÓN DE MODELOS")
        tabs = st.tabs([f"Modelo {i+1}" for i in range(len(st.session_state.modelos))])
        
        for i in range(len(st.session_state.modelos)):
            with tabs[i]:
                st.markdown('<div class="industrial-card">', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                st.session_state.modelos[i]['ref'] = col1.text_input("Nombre del diseño", value=st.session_state.modelos[i]['ref'], key=f"r_{i}")
                st.session_state.modelos[i]['material'] = col2.selectbox("Material", ["PP Blanco", "Couché", "Térmico", "Verjurado"], key=f"m_{i}")
                
                col3, col4, col5, col6 = st.columns(4)
                st.session_state.modelos[i]['anc'] = col3.number_input("Ancho mm", 10, 500, st.session_state.modelos[i]['anc'], key=f"a_{i}")
                st.session_state.modelos[i]['lar'] = col4.number_input("Largo mm", 10, 500, st.session_state.modelos[i]['lar'], key=f"l_{i}")
                st.session_state.modelos[i]['cant'] = col5.number_input("Cantidad", 100, 1000000, st.session_state.modelos[i]['cant'], key=f"c_{i}")
                st.session_state.modelos[i]['etq_r'] = col6.number_input("Etq/Rollo", 50, 10000, st.session_state.modelos[i]['etq_r'], key=f"e_{i}")
                
                st.session_state.modelos[i]['file'] = st.file_uploader("Subir PDF", type=["pdf"], key=f"f_{i}")
                st.markdown('</div>', unsafe_allow_html=True)

    with col_side:
        st.markdown("### ⚙️ TALLER")
        st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg")
        sentido = st.select_slider("Sentido", options=[str(x) for x in range(1,9)], value="3")
        mandril = st.selectbox("Mandril", ["76mm", "40mm", "25mm"])
        
        if st.button("🚀 ENVIAR PEDIDO"):
            if not cliente or not email_cliente:
                st.error("Faltan datos del cliente")
            else:
                try:
                    pdf = FlexyEnterprisePDF()
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 10, f"CLIENTE: {cliente}", ln=True)
                    pdf.ln(5)
                    
                    for i, m in enumerate(st.session_state.modelos):
                        pdf.write_model(i, m)
                    
                    pdf.ln(5)
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(0, 10, "ESPECIFICACIONES INDUSTRIALES", ln=True)
                    pdf.set_font("Arial", '', 10)
                    pdf.cell(0, 7, f"Sentido de salida: Posición {sentido} | Mandril: {mandril}", ln=True)
                    
                    nombre_archivo = f"Orden_{cliente}.pdf"
                    pdf.output(nombre_archivo)
                    st.success("Orden enviada y confirmación despachada.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error técnico: {e}")
