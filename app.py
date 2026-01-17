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
# 1. CONFIGURACIÓN E INTERFAZ INDUSTRIAL "FLEXYLABEL ORDER"
# =============================================================================
st.set_page_config(page_title="FlexyLabel Order | Industrial Printing", layout="wide", page_icon="🏷️")

def inject_ui_flexo():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&family=JetBrains+Mono&display=swap');

            .stApp {
                background-color: #0b0e14;
                color: #c9d1d9;
                font-family: 'Inter', sans-serif;
            }

            /* Título FlexyLabel Order */
            .main-header {
                background: linear-gradient(180deg, #161b22 0%, transparent 100%);
                padding: 2.5rem 1rem;
                text-align: center;
                border-bottom: 1px solid #30363d;
                margin-bottom: 2rem;
            }

            .main-title {
                font-family: 'Orbitron', sans-serif;
                font-size: 4rem;
                font-weight: 900;
                color: #58a6ff;
                text-shadow: 0 0 20px rgba(88,166,255,0.4);
                letter-spacing: 8px;
                margin: 0;
            }

            /* Contenedores Dinámicos con Hover */
            div[data-testid="stForm"] {
                background: rgba(22, 27, 34, 0.9) !important;
                border: 1px solid #30363d !important;
                border-radius: 20px !important;
                padding: 3rem !important;
                transition: all 0.4s ease-in-out !important;
            }

            div[data-testid="stForm"]:hover {
                border-color: #58a6ff !important;
                box-shadow: 0 0 35px rgba(88, 166, 255, 0.1);
            }

            /* Galería Lateral de Flexografía */
            .flexo-side img {
                width: 100%;
                border-radius: 10px;
                margin-bottom: 15px;
                filter: grayscale(100%) brightness(0.6);
                border: 1px solid #30363d;
                transition: all 0.5s ease;
            }

            .flexo-side img:hover {
                filter: grayscale(0%) brightness(1);
                border-color: #58a6ff;
                transform: scale(1.05);
            }

            /* Inputs Estilo Consola */
            .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
                background-color: #0d1117 !important;
                border: 1px solid #30363d !important;
                color: #58a6ff !important;
                font-family: 'JetBrains Mono', monospace !important;
            }

            label {
                font-family: 'Orbitron', sans-serif !important;
                color: #8b949e !important;
                font-size: 0.8rem !important;
                letter-spacing: 1px !important;
            }

            /* Botón de Lanzamiento */
            .stButton button {
                background: linear-gradient(90deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: white !important;
                height: 4rem !important;
                font-family: 'Orbitron', sans-serif !important;
                font-weight: 800 !important;
                border-radius: 12px !important;
                border: none !important;
                transition: 0.4s all !important;
                text-transform: uppercase;
                letter-spacing: 2px;
            }

            .stButton button:hover {
                box-shadow: 0 0 25px rgba(88, 166, 255, 0.5) !important;
                transform: translateY(-2px);
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. MOTOR TÉCNICO
# =============================================================================
def calcular_metricas(cantidad, ancho, largo):
    gap = 3 
    ml = (cantidad * (largo + gap)) / 1000
    m2 = (ancho / 1000) * ml
    return round(ml, 2), round(m2, 2)

# =============================================================================
# 3. INTERFAZ PRINCIPAL
# =============================================================================
inject_ui_flexo()

# Estructura de 3 Columnas para Galería Flexo
L_COL, MAIN_COL, R_COL = st.columns([1, 5, 1])

with L_COL:
    st.markdown('<div class="flexo-side">', unsafe_allow_html=True)
    # Imágenes Reales de Flexografía (Rodillos, Máquina, Tintas)
    st.image("https://cdn.pixabay.com/photo/2014/11/24/14/41/printing-machine-544111_1280.jpg")
    st.image("https://cdn.pixabay.com/photo/2014/05/21/15/28/cylinders-350021_1280.jpg")
    st.image("https://cdn.pixabay.com/photo/2013/07/19/12/36/ink-165518_1280.jpg")
    st.markdown('</div>', unsafe_allow_html=True)

with MAIN_COL:
    st.markdown('<div class="main-header"><h1 class="main-title">FLEXYLABEL ORDER</h1><p style="color:#8b949e; letter-spacing:3px;">SISTEMA DE GESTIÓN FLEXOGRÁFICA</p></div>', unsafe_allow_html=True)

    with st.form("flexo_form"):
        st.markdown("### 💠 01. REGISTRO DE CLIENTE")
        c1, c2 = st.columns(2)
        cliente = c1.text_input("RAZÓN SOCIAL / CLIENTE")
        email_c = c2.text_input("EMAIL DE CONTACTO")

        st.markdown("<hr style='border:0.5px solid #30363d'>", unsafe_allow_html=True)
        
        st.markdown("### 📐 02. ESPECIFICACIONES TÉCNICAS")
        c3, c4, c5, c6 = st.columns(4)
        ancho = c3.number_input("ANCHO (mm)", 10, 500, 100)
        largo = c4.number_input("LARGO (mm)", 10, 500, 100)
        cantidad = c5.number_input("CANTIDAD UDS", 100, 1000000, 5000)
        referencia = c6.text_input("REF. TRABAJO")

        c7, c8 = st.columns(2)
        material = c7.selectbox("MATERIAL / SOPORTE", ["PP Blanco", "PP Transparente", "Couché Brillante", "Verjurado", "Térmico"])
        etq_r = c8.number_input("ETIQUETAS POR ROLLO", 50, 10000, 1000)

        st.markdown("<hr style='border:0.5px solid #30363d'>", unsafe_allow_html=True)

        st.markdown("### ⚙️ 03. MONTAJE Y SALIDA")
        c9, c10 = st.columns([2, 1])
        with c9:
            st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", width=300)
            sentido = st.select_slider("SENTIDO DE SALIDA", options=[str(i) for i in range(1, 9)], value="3")
        with c10:
            mandril = st.selectbox("DIÁMETRO MANDRIL", ["76mm", "40mm", "25mm"])
            archivo_af = st.file_uploader("ARTE FINAL (PDF)", type=["pdf"])

        ml, m2 = calcular_metricas(cantidad, ancho, largo)
        st.markdown(f"""
            <div style="background: rgba(88, 166, 255, 0.05); border-left: 5px solid #58a6ff; padding: 20px; border-radius: 10px;">
                <p style="margin:0; font-family:'JetBrains Mono';"><b>ANÁLISIS DE CONSUMO:</b> {ml} Metros Lineales | {m2} Metros Cuadrados</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("🚀 ENVIAR ORDEN A PRODUCCIÓN")

        if submit:
            if not cliente or not archivo_af:
                st.error("⚠️ CAMPOS OBLIGATORIOS: Cliente y Arte Final.")
            else:
                st.success(f"ORDEN PARA {cliente.upper()} PROCESADA CON ÉXITO")
                st.balloons()

with R_COL:
    st.markdown('<div class="flexo-side">', unsafe_allow_html=True)
    st.image("https://cdn.pixabay.com/photo/2021/01/21/15/54/printing-press-5937748_1280.jpg")
    st.image("https://cdn.pixabay.com/photo/2022/01/10/15/29/industrial-6928581_1280.jpg")
    st.image("https://cdn.pixabay.com/photo/2016/11/23/15/33/industrial-1853561_1280.jpg")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<p style='text-align:center; color:#30363d; font-family:Orbitron; font-size:0.7rem; margin-top:50px;'>FlexyLabel Order Management System v4.0 © 2026</p>", unsafe_allow_html=True)
