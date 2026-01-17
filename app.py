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
import math
import random

# =============================================================================
# 1. CORE CONFIGURATION & NEON THEME (CSS INJECTION)
# =============================================================================
DESTINATARIO_FINAL = "covet@etiquetes.com"
COLOR_FONDO_DARK = "#0d1117"  # Gris casi negro (GitHub Dark)
COLOR_CARD = "#161b22"        # Gris azulado oscuro
COLOR_NEON_BLUE = "#58a6ff"   # Azul brillante
COLOR_NEON_GLOW = "0 0 15px rgba(88, 166, 255, 0.5)"

def inject_dark_neon_ui():
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap');

            /* Configuración Global */
            .stApp {{
                background-color: {COLOR_FONDO_DARK};
                color: #c9d1d9;
                font-family: 'Inter', sans-serif;
            }}

            /* Título Principal con Efecto Neón */
            .neon-title {{
                font-family: 'Orbitron', sans-serif;
                font-size: 3.5rem;
                font-weight: 700;
                color: {COLOR_NEON_BLUE};
                text-shadow: {COLOR_NEON_GLOW};
                text-align: center;
                margin-bottom: 0.5rem;
                letter-spacing: 4px;
            }}

            /* Contenedores de Sección (Cards) */
            .st-emotion-cache-1r6slb0 {{
                background-color: {COLOR_CARD} !important;
                border: 1px solid #30363d !important;
                border-radius: 15px !important;
                padding: 2.5rem !important;
                box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
            }}

            /* Inputs y Selectores */
            .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {{
                background-color: {COLOR_FONDO_DARK} !important;
                color: {COLOR_NEON_BLUE} !important;
                border: 1px solid #30363d !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
            }}

            .stTextInput input:focus {{
                border-color: {COLOR_NEON_BLUE} !important;
                box-shadow: {COLOR_NEON_GLOW} !important;
            }}

            /* Etiquetas de Texto (Labels) */
            label {{
                color: {COLOR_NEON_BLUE} !important;
                font-family: 'Orbitron', sans-serif !important;
                font-size: 0.9rem !important;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}

            /* Botón de Lanzamiento (Submit) */
            .stButton button {{
                background: linear-gradient(90deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: white !important;
                border: none !important;
                height: 3.5rem !important;
                font-family: 'Orbitron', sans-serif !important;
                font-weight: 700 !important;
                border-radius: 10px !important;
                box-shadow: {COLOR_NEON_GLOW} !important;
                transition: 0.3s all ease !important;
                width: 100% !important;
            }}

            .stButton button:hover {{
                transform: scale(1.02) !important;
                box-shadow: 0 0 25px rgba(88, 166, 255, 0.8) !important;
            }}

            /* Ocultar elementos de Streamlit */
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            
            /* Separadores Neón */
            hr {{
                border: 0;
                height: 1px;
                background: linear-gradient(to right, transparent, {COLOR_NEON_BLUE}, transparent);
                margin: 2rem 0;
            }}
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. CALCULATION ENGINE (INDUSTRIAL LOGIC)
# =============================================================================
def get_label_specs(cantidad, ancho, largo, material):
    # Cálculo de metros lineales necesarios
    gap = 3 # 3mm entre etiquetas
    metros_lineales = (cantidad * (largo + gap)) / 1000
    # Cálculo de metros cuadrados
    m2 = (ancho / 1000) * metros_lineales
    return round(metros_lineales, 2), round(m2, 2)

# =============================================================================
# 3. PREMIUM PDF RENDERER (DARK MODE THEME)
# =============================================================================
class FlexyDarkPDF(FPDF):
    def __init__(self, datos):
        super().__init__()
        self.d = datos
        self.blue_neon = (88, 166, 255)
        self.dark_bg = (13, 17, 23)

    def header(self):
        # Fondo oscuro en el header del PDF
        self.set_fill_color(*self.dark_bg)
        self.rect(0, 0, 210, 50, 'F')
        
        self.set_xy(10, 15)
        self.set_font("Courier", 'B', 30)
        self.set_text_color(*self.blue_neon)
        self.cell(0, 15, "FLEXYLABEL // PRODUCTION", ln=True, align='L')
        
        self.set_font("Courier", 'B', 10)
        self.set_text_color(200, 200, 200)
        self.cell(0, 5, "ORDER TECHNICAL SPECIFICATION SHEET", ln=True, align='L')
        self.ln(20)

    def draw_data_block(self, title, items):
        self.set_font("Courier", 'B', 12)
        self.set_fill_color(30, 35, 45)
        self.set_text_color(*self.blue_neon)
        self.cell(0, 10, f" > {title}", ln=True, fill=True)
        
        self.set_font("Arial", '', 10)
        self.set_text_color(50, 50, 50)
        self.ln(2)
        for key, value in items.items():
            self.set_font("Arial", 'B', 10)
            self.cell(40, 7, f"{key}:", 0)
            self.set_font("Arial", '', 10)
            self.cell(0, 7, str(value), 0, 1)
        self.ln(5)

# =============================================================================
# 4. SECURE DISPATCHER
# =============================================================================
def dispatch_neon_order(pdf_path, design_file, d):
    try:
        sender = st.secrets["email_usuario"]
        pwd = st.secrets["email_password"]
        
        msg = MIMEMultipart()
        msg['Subject'] = f"🔵 SYSTEM_ORDER: {d['cliente']} | {d['ref']}"
        msg['From'] = sender
        msg['To'] = DESTINATARIO_FINAL
        
        cuerpo = f"""
        SISTEMA DE PRODUCCIÓN FLEXYLABEL
        ----------------------------------
        CLIENTE: {d['cliente']}
        REFERENCIA: {d['ref']}
        MATERIAL: {d['material']}
        CANTIDAD: {d['cantidad']} uds
        
        Se adjunta el paquete de datos técnicos y arte final.
        """
        msg.attach(MIMEText(cuerpo, 'plain'))

        # Adjunto de la Orden PDF
        with open(pdf_path, "rb") as f:
            part = MIMEBase('application', 'pdf')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={pdf_path}')
            msg.attach(part)

        # Adjunto del Cliente
        if design_file:
            part2 = MIMEBase('application', 'octet-stream')
            part2.set_payload(design_file.getvalue())
            encoders.encode_base64(part2)
            part2.add_header('Content-Disposition', f'attachment; filename="SOURCE_{design_file.name}"')
            msg.attach(part2)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender, pwd)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Fallo en el protocolo de envío: {e}")
        return False

# =============================================================================
# 5. MAIN APPLICATION (UI)
# =============================================================================
def main():
    inject_dark_neon_ui()
    
    st.markdown('<h1 class="neon-title">FLEXYLABEL</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center; color:#58a6ff; font-family:Orbitron; font-size:0.8rem;">ENGINEERING & PRINTING CONSOLE</p>', unsafe_allow_html=True)
    
    with st.container():
        with st.form("neon_industrial_form"):
            st.markdown("### 💠 DATOS DEL EXPEDIENTE")
            col1, col2 = st.columns(2)
            with col1:
                cliente = st.text_input("RAZÓN SOCIAL / CLIENTE", placeholder="CLIENTE S.A.")
                email_c = st.text_input("EMAIL DE CONTACTO")
            with col2:
                referencia = st.text_input("REFERENCIA DEL DISEÑO")
                fecha_e = st.date_input("FECHA DE ENTREGA")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("### 📐 PARÁMETROS TÉCNICOS")
            col3, col4, col5 = st.columns(3)
            with col3:
                ancho = st.number_input("ANCHO (mm)", 1, 500, 100)
                largo = st.number_input("LARGO (mm)", 1, 500, 100)
            with col4:
                cantidad = st.number_input("CANTIDAD TOTAL", 100, 1000000, 5000, step=1000)
                material = st.selectbox("SOPORTE", ["PP BLANCO", "COUCHÉ", "TRANSPARENTE", "VERJURADO"])
            with col5:
                mandril = st.selectbox("MANDRIL", ["76mm", "40mm", "25mm"])
                sistema = st.selectbox("TECNOLOGÍA", ["FLEXOGRAFÍA", "DIGITAL", "OFFSET"])

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("### 🌀 CONFIGURACIÓN DE SALIDA")
            col6, col7 = st.columns(2)
            with col6:
                
                sentido = st.select_slider("POSICIÓN DE BOBINADO", options=[str(i) for i in range(1, 9)], value="3")
                salida_cara = st.radio("CARA DE IMPRESIÓN", ["EXTERIOR", "INTERIOR"], horizontal=True)
            with col7:
                archivo_af = st.file_uploader("ARTE FINAL (PDF ALTA RESOLUCIÓN)", type=["pdf"])
                observaciones = st.text_area("OBSERVACIONES TÉCNICAS (PANTONES, TROQUEL, ETC)")

            # Cálculos en vivo
            m_lineales, m2_totales = get_label_specs(cantidad, ancho, largo, material)
            st.markdown(f"""
                <div style="background:#1f2937; padding:15px; border-radius:10px; border-left:4px solid #58a6ff;">
                    <span style="color:#58a6ff; font-weight:bold;">PRE-FLIGHT INFO:</span><br>
                    Consumo estimado: <b>{m_lineales} metros lineales</b> | Superficie: <b>{m2_totales} m²</b>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            btn_submit = st.form_submit_button("Lanzar Orden a Producción")

            if btn_submit:
                if not cliente or not archivo_af:
                    st.error("ERROR: SE REQUIERE CLIENTE Y ARCHIVO PDF.")
                else:
                    with st.spinner("CODIFICANDO Y ENVIANDO..."):
                        datos = {
                            "cliente": cliente, "email": email_c, "ref": referencia,
                            "fecha": str(fecha_e), "ancho": ancho, "largo": largo,
                            "cantidad": cantidad, "material": material, "sistema": sistema,
                            "mandril": mandril, "sentido": sentido, "salida": salida_cara,
                            "obs": observaciones
                        }
                        
                        pdf = FlexyDarkPDF(datos)
                        pdf.add_page()
                        pdf.draw_data_block("GENERAL", {"Cliente": cliente, "Ref": referencia, "Fecha": fecha_e})
                        pdf.draw_data_block("TÉCNICO", {"Medida": f"{ancho}x{largo}mm", "Material": material, "Cant": cantidad})
                        pdf.draw_data_block("BOBINADO", {"Sentido": sentido, "Mandril": mandril, "Cara": salida_cara})
                        
                        path = f"ORDEN_{cliente}.pdf".replace(" ", "_")
                        pdf.output(path)
                        
                        if dispatch_neon_order(path, archivo_af, datos):
                            st.success("ORDEN ENVIADA AL SERVIDOR DE PRODUCCIÓN")
                            st.balloons()
                            if os.path.exists(path): os.remove(path)

if __name__ == "__main__":
    main()
