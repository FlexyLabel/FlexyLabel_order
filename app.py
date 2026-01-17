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

            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            
            hr {{
                border: 0;
                height: 1px;
                background: linear-gradient(to right, transparent, {COLOR_NEON_BLUE}, transparent);
                margin: 2rem 0;
            }}
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. CALCULATION ENGINE
# =============================================================================
def get_label_specs(cantidad, ancho, largo):
    gap = 3 
    metros_lineales = (cantidad * (largo + gap)) / 1000
    m2 = (ancho / 1000) * metros_lineales
    return round(metros_lineales, 2), round(m2, 2)

# =============================================================================
# 3. PREMIUM PDF RENDERER
# =============================================================================
class FlexyDarkPDF(FPDF):
    def __init__(self, datos, modelos):
        super().__init__()
        self.datos_grales = datos
        self.modelos = modelos
        self.blue_neon = (88, 166, 255)
        self.dark_bg = (13, 17, 23)

    def header(self):
        self.set_fill_color(*self.dark_bg)
        self.rect(0, 0, 210, 40, 'F')
        self.set_xy(10, 10)
        self.set_font("Courier", 'B', 24)
        self.set_text_color(*self.blue_neon)
        self.cell(0, 15, "FLEXYLABEL // PRODUCTION ORDER", ln=True, align='L')
        self.ln(10)

    def draw_data_block(self, title, items):
        self.set_font("Courier", 'B', 12)
        self.set_fill_color(30, 35, 45)
        self.set_text_color(*self.blue_neon)
        self.cell(0, 10, f" > {title}", ln=True, fill=True)
        self.set_font("Arial", '', 10)
        self.set_text_color(0, 0, 0)
        self.ln(2)
        for key, value in items.items():
            self.set_font("Arial", 'B', 10)
            self.cell(50, 7, f"{key}:", 0)
            self.set_font("Arial", '', 10)
            self.cell(0, 7, str(value), 0, 1)
        self.ln(3)

# =============================================================================
# 4. SECURE DISPATCHER (CON CONFIRMACIÓN A CLIENTE)
# =============================================================================
def dispatch_neon_order(pdf_path, modelos, d):
    try:
        sender = st.secrets["email_usuario"]
        pwd = st.secrets["email_password"]
        
        # Enviamos a Taller y al Cliente
        destinatarios = [DESTINATARIO_FINAL, d['email']]
        
        for recipient in destinatarios:
            msg = MIMEMultipart()
            is_cliente = (recipient == d['email'])
            msg['Subject'] = f"{'CONFIRMACIÓN' if is_cliente else '🔵 ORDEN'} : {d['cliente']} | {d['ref']}"
            msg['From'] = sender
            msg['To'] = recipient
            
            cuerpo = f"SISTEMA FLEXYLABEL\n\nHola {d['cliente']},\nAdjuntamos la orden técnica de producción."
            msg.attach(MIMEText(cuerpo, 'plain'))

            with open(pdf_path, "rb") as f:
                part = MIMEBase('application', 'pdf')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={pdf_path}')
                msg.attach(part)

            # Adjuntar artes finales solo al taller para no saturar al cliente
            if not is_cliente:
                for m in modelos:
                    if m['archivo']:
                        part_af = MIMEBase('application', 'octet-stream')
                        part_af.set_payload(m['archivo'].getvalue())
                        encoders.encode_base64(part_af)
                        part_af.add_header('Content-Disposition', f'attachment; filename="AF_{m["ref"]}.pdf"')
                        msg.attach(part_af)

            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(sender, pwd)
            server.send_message(msg)
            server.quit()
        return True
    except Exception as e:
        st.error(f"Fallo en el protocolo: {e}")
        return False

# =============================================================================
# 5. MAIN APPLICATION (UI)
# =============================================================================
def main():
    inject_dark_neon_ui()
    st.markdown('<h1 class="neon-title">FLEXYLABEL</h1>', unsafe_allow_html=True)
    
    # Manejo de múltiples modelos
    if 'n_modelos' not in st.session_state: st.session_state.n_modelos = 1

    with st.form("neon_industrial_form"):
        st.markdown("### 💠 DATOS DEL EXPEDIENTE")
        c_c1, c_c2 = st.columns(2)
        with c_c1:
            cliente = st.text_input("RAZÓN SOCIAL / CLIENTE")
            email_c = st.text_input("EMAIL DE CONFIRMACIÓN")
        with c_c2:
            referencia_gral = st.text_input("REFERENCIA GENERAL DEL PEDIDO")
            fecha_e = st.date_input("FECHA DE ENTREGA")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 📦 MODELOS A IMPRIMIR")
        
        # Pestañas para no ver la página vacía ni desordenada
        tab_list = st.tabs([f"Modelo {i+1}" for i in range(st.session_state.n_modelos)])
        modelos_data = []

        for i in range(st.session_state.n_modelos):
            with tab_list[i]:
                col_m1, col_m2, col_m3 = st.columns([2,1,1])
                ref = col_m1.text_input(f"Referencia Diseño", key=f"ref_{i}")
                anc = col_m2.number_input(f"Ancho (mm)", 1, 500, 100, key=f"anc_{i}")
                lar = col_m3.number_input(f"Largo (mm)", 1, 500, 100, key=f"lar_{i}")
                
                col_m4, col_m5, col_m6 = st.columns(3)
                cnt = col_m4.number_input(f"Cantidad", 100, 1000000, 5000, key=f"cnt_{i}")
                rol = col_m5.number_input(f"Etiquetas por Rollo", 50, 20000, 1000, key=f"rol_{i}")
                pdf_file = col_m6.file_uploader(f"Arte Final PDF", type=["pdf"], key=f"pdf_{i}")
                
                modelos_data.append({"ref": ref, "ancho": anc, "largo": lar, "cant": cnt, "rollo": rol, "archivo": pdf_file})

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 🌀 CONFIGURACIÓN DE TALLER")
        col6, col7 = st.columns(2)
        with col6:
            st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", caption="Esquema de Posiciones de Salida", width=400)
            sentido = st.select_slider("POSICIÓN DE BOBINADO", options=[str(i) for i in range(1, 9)], value="3")
            salida_cara = st.radio("CARA DE IMPRESIÓN", ["EXTERIOR", "INTERIOR"], horizontal=True)
        with col7:
            material = st.selectbox("SOPORTE", ["PP BLANCO", "COUCHÉ", "TRANSPARENTE", "VERJURADO"])
            mandril = st.selectbox("MANDRIL", ["76mm", "40mm", "25mm"])
            observaciones = st.text_area("OBSERVACIONES TÉCNICAS")

        btn_submit = st.form_submit_button("Lanzar Orden a Producción")

        if btn_submit:
            if not cliente or not email_c:
                st.error("ERROR: SE REQUIEREN DATOS DE CLIENTE.")
            else:
                with st.spinner("PROCESANDO..."):
                    datos_grales = {"cliente": cliente, "email": email_c, "ref": referencia_gral}
                    pdf = FlexyDarkPDF(datos_grales, modelos_data)
                    pdf.add_page()
                    pdf.draw_data_block("CLIENTE", {"Nombre": cliente, "Email": email_c, "Entrega": str(fecha_e)})
                    
                    for i, m in enumerate(modelos_data):
                        pdf.draw_data_block(f"MODELO {i+1}: {m['ref']}", {
                            "Medidas": f"{m['ancho']}x{m['largo']}mm",
                            "Cantidad": m['cant'],
                            "Etq/Rollo": m['rollo']
                        })
                    
                    pdf.draw_data_block("BOBINADO", {"Posición": sentido, "Salida": salida_cara, "Mandril": mandril, "Material": material})
                    
                    path = f"ORDEN_{cliente}.pdf".replace(" ", "_")
                    pdf.output(path)
                    
                    if dispatch_neon_order(path, modelos_data, datos_grales):
                        st.success(f"ORDEN ENVIADA A TALLER Y CONFIRMACIÓN A {email_c}")
                        st.balloons()
                        if os.path.exists(path): os.remove(path)

    if st.button("➕ AÑADIR OTRO MODELO"):
        st.session_state.n_modelos += 1
        st.rerun()

if __name__ == "__main__":
    main()
