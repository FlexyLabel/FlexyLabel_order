import streamlit as st
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime
import os
import time

# =============================================================================
# 1. CONFIGURACIÓN Y ESTÉTICA INDUSTRIAL "ULTRA"
# =============================================================================
st.set_page_config(page_title="FLEXYLABEL | Production OS", layout="wide", page_icon="🏷️")

def inject_full_industrial_ui():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

            /* Reset Global */
            .stApp {
                background-color: #0b0e14;
                color: #c9d1d9;
                font-family: 'Inter', sans-serif;
            }

            /* Cabecera Cinemática */
            .main-header {
                background: linear-gradient(180deg, #161b22 0%, transparent 100%);
                padding: 3rem 1rem;
                text-align: center;
                border-bottom: 1px solid #30363d;
                margin-bottom: 3rem;
            }

            .main-title {
                font-family: 'Orbitron', sans-serif;
                font-size: 4.5rem;
                font-weight: 900;
                background: linear-gradient(90deg, #58a6ff, #1f6feb, #58a6ff);
                background-size: 200% auto;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                animation: shine 3s linear infinite;
                letter-spacing: 10px;
                margin: 0;
            }

            @keyframes shine {
                to { background-position: 200% center; }
            }

            /* Contenedores con Efecto de Profundidad (Hovers) */
            div[data-testid="stForm"] {
                background: rgba(22, 27, 34, 0.8) !important;
                border: 1px solid #30363d !important;
                border-radius: 24px !important;
                padding: 4rem !important;
                backdrop-filter: blur(12px);
                transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            }

            div[data-testid="stForm"]:hover {
                border-color: #58a6ff !important;
                box-shadow: 0 0 40px rgba(88, 166, 255, 0.15);
                transform: scale(1.005);
            }

            /* Imágenes Laterales con Efecto Industrial */
            .side-gallery img {
                width: 100%;
                border-radius: 12px;
                margin-bottom: 20px;
                filter: grayscale(100%) contrast(1.2) brightness(0.7);
                border: 1px solid #30363d;
                transition: all 0.6s ease;
            }

            .side-gallery img:hover {
                filter: grayscale(0%) brightness(1);
                border-color: #58a6ff;
                transform: rotate(1deg) scale(1.08);
                box-shadow: 0 0 25px rgba(88, 166, 255, 0.4);
            }

            /* Inputs y Selectores Estilo Consola */
            .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
                background-color: #0d1117 !important;
                border: 1px solid #30363d !important;
                border-radius: 12px !important;
                color: #58a6ff !important;
                font-family: 'JetBrains Mono', monospace !important;
                padding: 12px !important;
            }

            /* Labels */
            label {
                font-family: 'Orbitron', sans-serif !important;
                color: #8b949e !important;
                font-size: 0.75rem !important;
                letter-spacing: 2px !important;
                text-transform: uppercase;
                margin-bottom: 8px !important;
            }

            /* Botón de Lanzamiento */
            .stButton button {
                background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: white !important;
                height: 4.5rem !important;
                font-family: 'Orbitron', sans-serif !important;
                font-weight: 800 !important;
                font-size: 1.2rem !important;
                border-radius: 15px !important;
                border: none !important;
                letter-spacing: 3px !important;
                transition: all 0.4s ease !important;
                box-shadow: 0 10px 20px rgba(0,0,0,0.4) !important;
                text-transform: uppercase;
            }

            .stButton button:hover {
                letter-spacing: 6px !important;
                box-shadow: 0 0 30px rgba(88, 166, 255, 0.6) !important;
                transform: translateY(-3px);
            }

            /* Divisores Neón */
            hr {
                border: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, #30363d, #58a6ff, #30363d, transparent);
                margin: 3rem 0;
            }

            /* Barra lateral de métricas */
            .metric-card {
                background: #161b22;
                border-left: 4px solid #58a6ff;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 15px;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. LOGICA DE CÁLCULO
# =============================================================================
def calcular_metricas(cantidad, ancho, largo):
    gap = 3 
    ml = (cantidad * (largo + gap)) / 1000
    m2 = (ancho / 1000) * ml
    return round(ml, 2), round(m2, 2)

# =============================================================================
# 3. INTERFAZ DE USUARIO
# =============================================================================
inject_full_industrial_ui()

# Estructura Principal de 3 Columnas
COL_LEFT, COL_MAIN, COL_RIGHT = st.columns([1, 4.5, 1])

with COL_LEFT:
    st.markdown('<div class="side-gallery">', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1610473069150-13645396b270?q=80&w=400") # Maquinaria
    st.image("https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=400") # Tintas
    st.image("https://images.unsplash.com/photo-1581092160607-ee22621dd758?q=80&w=400") # Engranajes
    st.image("https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?q=80&w=400") # Bobinas
    st.markdown('</div>', unsafe_allow_html=True)

with COL_MAIN:
    st.markdown('<div class="main-header"><h1 class="main-title">FLEXYLABEL</h1><p style="letter-spacing:5px; color:#8b949e;">CLOUD PRINTING INFRASTRUCTURE</p></div>', unsafe_allow_html=True)

    with st.form("industrial_order_form"):
        # SECCIÓN 1: IDENTIFICACIÓN
        st.markdown("### 💠 01. IDENTIFICACIÓN DEL PROYECTO")
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            cliente = st.text_input("RAZÓN SOCIAL / CLIENTE", placeholder="Nombre de la empresa...")
        with c2:
            email_c = st.text_input("EMAIL DE NOTIFICACIÓN", placeholder="logistica@empresa.com")
        with c3:
            referencia = st.text_input("ORDEN REF", placeholder="FX-2026")
        
        st.markdown("<hr>", unsafe_allow_html=True)

        # SECCIÓN 2: PARÁMETROS TÉCNICOS
        st.markdown("### 📐 02. INGENIERÍA DE PRODUCTO")
        c4, c5, c6, c7 = st.columns(4)
        with c4:
            ancho = st.number_input("ANCHO NETO (mm)", 10, 500, 100)
        with c5:
            largo = st.number_input("LARGO NETO (mm)", 10, 500, 100)
        with c6:
            cantidad = st.number_input("CANTIDAD TOTAL", 100, 1000000, 5000)
        with c7:
            etq_rollo = st.number_input("ETQ POR ROLLO", 50, 20000, 1000)

        c8, c9 = st.columns(2)
        with c8:
            material = st.selectbox("SOPORTE FÍSICO", ["PP BLANCO", "PP TRANSPARENTE", "COUCHÉ BRILLANTE", "VERJURADO CREMA", "TÉRMICO TOP"])
        with c9:
            acabado = st.multiselect("TRATAMIENTOS ADICIONALES", ["Barniz Brillo", "Barniz Mate", "Laminado", "Estampado Oro", "Relieve Serigráfico"])

        st.markdown("<hr>", unsafe_allow_html=True)

        # SECCIÓN 3: LOGÍSTICA DE TALLER
        st.markdown("### ⚙️ 03. CONFIGURACIÓN INDUSTRIAL")
        c10, c11 = st.columns([2, 1])
        with c10:
            st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", caption="Esquema de Sentido de Bobinado v2.0")
            sentido = st.select_slider("ORIENTACIÓN DE SALIDA (POSICIÓN)", options=[str(i) for i in range(1, 9)], value="3")
        with c11:
            mandril = st.radio("DIÁMETRO DE MANDRIL (EJE)", ["76mm (Industrial)", "40mm (Semi-automático)", "25mm (Manual)"])
            st.markdown("<br>", unsafe_allow_html=True)
            archivo_af = st.file_uploader("ARTE FINAL (FORMATO PDF/X-4)", type=["pdf"])

        st.markdown("<hr>", unsafe_allow_html=True)

        # SECCIÓN 4: OBSERVACIONES Y CÁLCULO
        st.markdown("### 📝 04. CONTROL DE CALIDAD Y NOTAS")
        observaciones = st.text_area("INSTRUCCIONES ESPECIALES (PANTONES, TROQUELADO, ETC.)", height=120)
        
        ml, m2 = calcular_metricas(cantidad, ancho, largo)
        
        # Panel de Resumen Técnico
        st.markdown(f"""
            <div style="background: rgba(88, 166, 255, 0.05); border: 1px solid #58a6ff; padding: 25px; border-radius: 15px; margin-top: 20px;">
                <h4 style="color: #58a6ff; margin-top: 0; font-family: 'Orbitron'; font-size: 0.8rem;">DATOS DE PRE-VUELO</h4>
                <div style="display: flex; gap: 40px;">
                    <div><small style="color:#8b949e">DISTANCIA TOTAL:</small><br><b style="font-size: 1.5rem; font-family: 'JetBrains Mono';">{ml} m</b></div>
                    <div><small style="color:#8b949e">SUPERFICIE MATERIAL:</small><br><b style="font-size: 1.5rem; font-family: 'JetBrains Mono';">{m2} m²</b></div>
                    <div><small style="color:#8b949e">PESO EST. MATERIA PRIMA:</small><br><b style="font-size: 1.5rem; font-family: 'JetBrains Mono';">{round(m2 * 0.12, 2)} kg</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.form_submit_button("🚀 EJECUTAR ORDEN DE PRODUCCIÓN"):
            if not cliente or not archivo_af:
                st.warning("⚠️ PROTOCOLO INCOMPLETO: Se requiere Cliente y Archivo Técnico.")
            else:
                with st.spinner("Sincronizando con Servidor de Impresión..."):
                    time.sleep(2)
                    st.success(f"ORDEN {referencia} DESPACHADA CORRECTAMENTE")
                    st.balloons()

with COL_RIGHT:
    st.markdown('<div class="side-gallery">', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590402494682-cd3fb53b1f71?q=80&w=400") # Flexo
    st.image("https://images.unsplash.com/photo-1626785774573-4b799315345d?q=80&w=400") # Pantones
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=400") # Laboratorio
    st.image("https://images.unsplash.com/photo-1589793463357-5fb813435467?q=80&w=400") # Logística
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br><p style='text-align:center; color:#30363d; font-family:Orbitron; font-size:0.7rem;'>FLEXYLABEL OS v4.0 // ENGINEERED BY IVÁN // 2026</p>", unsafe_allow_html=True)
