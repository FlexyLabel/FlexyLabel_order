import streamlit as st
from fpdf import FPDF
import datetime
import os
import time

# =============================================================================
# 1. INTERFAZ ULTRA-DETALLADA (LETRAS BLANCAS Y HOVER DINÁMICO)
# =============================================================================
st.set_page_config(page_title="FlexyLabel Order | Industrial Printing", layout="wide", page_icon="🏷️")

def inject_ui_flexo_final():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&family=JetBrains+Mono&display=swap');

            /* Fondo y color de texto base */
            .stApp {
                background-color: #0b0e14;
                color: #ffffff !important; /* LETRAS EN BLANCO */
                font-family: 'Inter', sans-serif;
            }

            /* Título Superior */
            .main-title {
                font-family: 'Orbitron', sans-serif;
                font-size: 4rem;
                font-weight: 900;
                color: #ffffff; /* Título en blanco */
                text-shadow: 0 0 15px rgba(88,166,255,0.6);
                text-align: center;
                letter-spacing: 8px;
                margin-bottom: 2rem;
            }

            /* RECUADROS QUE RESALTAN (HOVER) */
            div[data-testid="stForm"], .css-1r6slb0, .st-emotion-cache-1r6slb0 {
                background: rgba(22, 27, 34, 0.95) !important;
                border: 2px solid #30363d !important; /* Borde más visible */
                border-radius: 20px !important;
                padding: 3rem !important;
                transition: all 0.3s ease-in-out !important;
            }

            /* EFECTO CUANDO EL CURSOR PASA POR ENCIMA */
            div[data-testid="stForm"]:hover, .st-emotion-cache-1r6slb0:hover {
                border-color: #58a6ff !important;
                box-shadow: 0 0 40px rgba(88, 166, 255, 0.3) !important; /* Brillo neón */
                transform: translateY(-5px); /* Se eleva un poco */
            }

            /* Estilo de todos los textos de etiquetas */
            label, .stMarkdown p, .stMarkdown h3 {
                color: #ffffff !important; /* Forzado a blanco */
                font-family: 'Orbitron', sans-serif !important;
                letter-spacing: 1px;
            }

            /* Inputs y Selectores */
            .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
                background-color: #1c2128 !important;
                border: 1px solid #444c56 !important;
                color: #ffffff !important;
                font-size: 1rem !important;
            }

            /* Imágenes Laterales */
            .flexo-side img {
                width: 100%;
                border-radius: 12px;
                margin-bottom: 20px;
                border: 2px solid #30363d;
                transition: 0.4s;
            }
            .flexo-side img:hover {
                border-color: #58a6ff;
                transform: scale(1.05);
            }

            /* Botón Principal */
            .stButton button {
                background: linear-gradient(90deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: white !important;
                height: 4rem !important;
                font-family: 'Orbitron', sans-serif !important;
                font-weight: 800 !important;
                border-radius: 15px !important;
                transition: 0.4s !important;
                border: none !important;
            }
            .stButton button:hover {
                box-shadow: 0 0 30px rgba(88, 166, 255, 0.7) !important;
                letter-spacing: 3px;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. LÓGICA TÉCNICA
# =============================================================================
def calcular_metricas(cantidad, ancho, largo):
    gap = 3 
    ml = (cantidad * (largo + gap)) / 1000
    m2 = (ancho / 1000) * ml
    return round(ml, 2), round(m2, 2)

# =============================================================================
# 3. CONSTRUCCIÓN DE LA PÁGINA
# =============================================================================
inject_ui_flexo_final()

# Título Principal
st.markdown('<h1 class="main-title">FLEXYLABEL ORDER</h1>', unsafe_allow_html=True)

# Layout: [Imagen Lateral] [Formulario] [Imagen Lateral]
L_COL, MAIN_COL, R_COL = st.columns([1, 4, 1])

with L_COL:
    st.markdown('<div class="flexo-side">', unsafe_allow_html=True)
    # Imágenes estables de Unsplash sobre impresión
    st.image("https://images.unsplash.com/photo-1610473069150-13645396b270?auto=format&fit=crop&w=400&q=80")
    st.image("https://images.unsplash.com/photo-1563089145-599997674d42?auto=format&fit=crop&w=400&q=80")
    st.image("https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=400&q=80")
    st.markdown('</div>', unsafe_allow_html=True)

with MAIN_COL:
    with st.form("main_order_form"):
        st.write("### 💠 01. REGISTRO DE CLIENTE")
        c1, c2 = st.columns(2)
        cliente = c1.text_input("NOMBRE DE LA EMPRESA")
        email_c = c2.text_input("EMAIL DE NOTIFICACIÓN")
        
        st.write("### 📐 02. INGENIERÍA DE ETIQUETA")
        c3, c4, c5 = st.columns(3)
        ancho = c3.number_input("ANCHO (mm)", 10, 500, 100)
        largo = c4.number_input("LARGO (mm)", 10, 500, 100)
        cantidad = c5.number_input("CANTIDAD TOTAL", 100, 1000000, 5000)
        
        c6, c7 = st.columns(2)
        material = c6.selectbox("MATERIAL", ["PP Blanco", "PP Transparente", "Couché", "Verjurado Vino", "Térmico"])
        etq_r = c7.number_input("ETIQUETAS POR ROLLO", 50, 10000, 1000)
        
        st.write("### ⚙️ 03. PARÁMETROS DE TALLER")
        c8, c9 = st.columns([2, 1])
        with c8:
            # Diagrama de bobinado
            st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", width=350)
            sentido = st.select_slider("SENTIDO DE BOBINADO", options=[str(i) for i in range(1, 9)], value="3")
        with c9:
            mandril = st.selectbox("MANDRIL", ["76mm", "40mm", "25mm"])
            archivo_af = st.file_uploader("SUBIR ARTE FINAL (PDF)", type=["pdf"])
        
        ml, m2 = calcular_metricas(cantidad, ancho, largo)
        st.markdown(f"""
            <div style="background: rgba(88, 166, 255, 0.1); border-left: 5px solid #58a6ff; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <p style="margin:0; color:#ffffff; font-weight:bold;">PRE-CÁLCULO TÉCNICO:</p>
                <p style="margin:0; color:#58a6ff; font-family:'JetBrains Mono'; font-size:1.2rem;">{ml} m lineales / {m2} m² de material</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        submit = st.form_submit_button("🚀 ENVIAR ORDEN A PRODUCCIÓN")
        
        if submit:
            if not cliente or not archivo_af:
                st.error("⚠️ Iván, el nombre del cliente y el PDF son obligatorios.")
            else:
                st.success(f"ORDEN DE {cliente.upper()} RECIBIDA CORRECTAMENTE.")
                st.balloons()

with R_COL:
    st.markdown('<div class="flexo-side">', unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1590402494682-cd3fb53b1f71?auto=format&fit=crop&w=400&q=80")
    st.image("https://images.unsplash.com/photo-1626785774573-4b799315345d?auto=format&fit=crop&w=400&q=80")
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=400&q=80")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<p style='text-align:center; color:#444c56; font-size:0.8rem; margin-top:50px;'>FlexyLabel Order Management System v4.0 © 2026</p>", unsafe_allow_html=True)
