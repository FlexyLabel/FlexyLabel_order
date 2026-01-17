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

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y CONSTANTES (NO TOCAR)
# =============================================================================
st.set_page_config(
    page_title="FLEXYLABEL ORDER v4.0 | Production System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

FILE_TEMP_PDF = "ORDEN_PRODUCCION_DETALLADA.pdf"
DESTINATARIO_TALLER = "covet@etiquetes.com"

# =============================================================================
# 2. MOTOR DE ESTILO CSS (LETRAS BLANCAS Y HOVER DINÁMICO)
# =============================================================================
def apply_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

            .stApp {
                background-color: #0d1117;
                color: #ffffff !important;
                font-family: 'Inter', sans-serif;
            }

            h1, h2, h3, label, p, span, .stMarkdown {
                color: #ffffff !important;
                font-family: 'Orbitron', sans-serif !important;
            }

            .main-header {
                text-align: center;
                padding: 2.5rem;
                background: linear-gradient(180deg, #161b22 0%, transparent 100%);
                border-bottom: 1px solid #30363d;
                margin-bottom: 2rem;
            }

            /* EFECTO HOVER REALZADO */
            div[data-testid="stForm"], .st-emotion-cache-1r6slb0 {
                background: rgba(22, 27, 34, 0.95) !important;
                border: 2px solid #30363d !important;
                border-radius: 20px !important;
                padding: 3rem !important;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            }

            div[data-testid="stForm"]:hover {
                border-color: #58a6ff !important;
                box-shadow: 0 0 40px rgba(88, 166, 255, 0.3) !important;
                transform: translateY(-5px);
            }

            .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
                background-color: #0d1117 !important;
                border: 1px solid #30363d !important;
                color: #58a6ff !important;
                font-family: 'JetBrains Mono', monospace !important;
            }

            .side-img {
                width: 100%;
                border-radius: 12px;
                border: 1px solid #30363d;
                margin-bottom: 1.5rem;
                transition: 0.5s;
            }
            .side-img:hover {
                border-color: #58a6ff;
                transform: scale(1.02);
            }

            .stButton button {
                background: linear-gradient(90deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: white !important;
                height: 4.5rem !important;
                border-radius: 15px !important;
                font-weight: 800 !important;
                text-transform: uppercase;
                letter-spacing: 3px;
                border: none !important;
                width: 100% !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 3. CLASE GENERADORA DE PDF TÉCNICO CON INTEGRACIÓN DE IMAGEN
# =============================================================================
class PDF_Orden_Completa(FPDF):
    def header(self):
        self.set_fill_color(22, 27, 34)
        self.rect(0, 0, 210, 40, 'F')
        self.set_xy(10, 12)
        self.set_font('Arial', 'B', 22)
        self.set_text_color(88, 166, 255)
        self.cell(0, 10, 'FLEXYLABEL // PRODUCTION SHEET', ln=True)
        self.set_font('Arial', '', 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f'ORDEN GENERADA: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True)
        self.ln(15)

    def seccion(self, titulo):
        self.ln(5)
        self.set_fill_color(48, 54, 61)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 8, f'  {titulo}', ln=True, fill=True)
        self.ln(3)

    def dato(self, txt_l, txt_v, txt_l2="", txt_v2=""):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(40, 40, 40)
        self.cell(35, 7, f"{txt_l}:", 0)
        self.set_font('Arial', '', 10)
        self.cell(60, 7, f"{txt_v}", 0)
        if txt_l2:
            self.set_font('Arial', 'B', 10)
            self.cell(35, 7, f"{txt_l2}:", 0)
            self.set_font('Arial', '', 10)
            self.cell(0, 7, f"{txt_v2}", 0)
        self.ln(7)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(170, 170, 170)
        self.cell(0, 10, f'Hoja de Producción FlexyLabel v4.0 - Página {self.page_no()}', 0, 0, 'C')

# =============================================================================
# 4. FUNCIONES DE CÁLCULO Y ENVÍO
# =============================================================================
def calcular_tecnico(cantidad, ancho, largo):
    gap = 3
    ml = (cantidad * (largo + gap)) / 1000
    m2 = (ancho / 1000) * ml
    return round(ml, 2), round(m2, 2)

def despachar_email(pdf_ficha, arte_final, datos):
    try:
        remitente = st.secrets["email_usuario"]
        password = st.secrets["email_password"]

        msg = MIMEMultipart()
        msg['From'] = remitente
        msg['To'] = f"{DESTINATARIO_TALLER}, {datos['email']}"
        msg['Subject'] = f"🔵 ORDEN FABRICACIÓN: {datos['cliente']} | {datos['ref']}"

        cuerpo = f"Nueva orden procesada.\nCliente: {datos['cliente']}\nMaterial: {datos['material']}\nCantidad: {datos['cantidad']}"
        msg.attach(MIMEText(cuerpo, 'plain'))

        with open(pdf_ficha, "rb") as f:
            p1 = MIMEBase('application', 'octet-stream')
            p1.set_payload(f.read())
            encoders.encode_base64(p1)
            p1.add_header('Content-Disposition', f'attachment; filename="FICHA_TECNICA_{datos["cliente"]}.pdf"')
            msg.attach(p1)

        if arte_final:
            p2 = MIMEBase('application', 'octet-stream')
            p2.set_payload(arte_final.getvalue())
            encoders.encode_base64(p2)
            p2.add_header('Content-Disposition', f'attachment; filename="DISENO_{datos["cliente"]}.pdf"')
            msg.attach(p2)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error en envío: {e}")
        return False

# =============================================================================
# 5. APLICACIÓN PRINCIPAL (UI INTEGRAL)
# =============================================================================
def main():
    apply_custom_css()
    
    # Galería de imágenes Flexo reales
    L, M, R = st.columns([0.8, 4, 0.8])
    
    with L:
        st.image("https://images.unsplash.com/photo-1610473069150-13645396b270?w=400")
        st.image("https://images.unsplash.com/photo-1563089145-599997674d42?w=400")
    with R:
        st.image("https://images.unsplash.com/photo-1590402494682-cd3fb53b1f71?w=400")
        st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400")

    with M:
        st.markdown('<div class="main-header"><h1>FLEXYLABEL ORDER</h1></div>', unsafe_allow_html=True)
        
        with st.form("master_form"):
            st.write("### 🏢 IDENTIFICACIÓN")
            c1, c2, c3 = st.columns([2,2,1])
            cliente = c1.text_input("CLIENTE / RAZÓN SOCIAL")
            email_c = c2.text_input("EMAIL CONFIRMACIÓN")
            ref = c3.text_input("REFERENCIA", value="FX-2026")

            st.write("---")
            st.write("### 📐 ESPECIFICACIONES TÉCNICAS")
            c4, c5, c6 = st.columns(3)
            ancho = c4.number_input("ANCHO (mm)", 10, 500, 100)
            largo = c5.number_input("LARGO (mm)", 10, 500, 100)
            cantidad = c6.number_input("CANTIDAD", 100, 2000000, 5000)

            c7, c8, c9 = st.columns(3)
            material = c7.selectbox("MATERIAL", ["PP Blanco", "Couché", "Térmico", "Verjurado"])
            mandril = c8.selectbox("MANDRIL", ["76mm", "40mm", "25mm"])
            etq_r = c9.number_input("ETIQ. POR ROLLO", 50, 10000, 1000)

            st.write("---")
            st.write("### ⚙️ PRODUCCIÓN Y DISEÑO")
            c10, c11 = st.columns([2, 1])
            with c10:
                st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", width=380)
                sentido = st.select_slider("SENTIDO BOBINADO", options=[str(i) for i in range(1, 9)], value="3")
            with c11:
                archivo_af = st.file_uploader("ARTE FINAL (PDF)", type=["pdf"])
                obs = st.text_area("NOTAS TALLER")

            ml, m2 = calcular_tecnico(cantidad, ancho, largo)
            st.info(f"Cálculo: {ml} ml | {m2} m²")

            if st.form_submit_button("🚀 PROCESAR ORDEN"):
                if not cliente or not archivo_af:
                    st.error("Iván, faltan datos obligatorios.")
                else:
                    # GENERACIÓN DE FICHA TÉCNICA
                    pdf = PDF_Orden_Completa()
                    pdf.add_page()
                    
                    pdf.seccion("DATOS GENERALES")
                    pdf.dato("Cliente", cliente, "Referencia", ref)
                    pdf.dato("Email", email_c)
                    
                    pdf.seccion("ESPECIFICACIONES TÉCNICAS")
                    pdf.dato("Material", material, "Cantidad", f"{cantidad} uds")
                    pdf.dato("Medida", f"{ancho}x{largo} mm", "Etiq/Rollo", etq_r)
                    
                    pdf.seccion("TALLER / LOGÍSTICA")
                    pdf.dato("Sentido", sentido, "Mandril", mandril)
                    pdf.dato("Metros", f"{ml} ml", "Superficie", f"{m2} m2")
                    
                    if obs:
                        pdf.seccion("OBSERVACIONES")
                        pdf.set_font("Arial", "", 10)
                        pdf.multi_cell(0, 7, obs)

                    # NOTA: En PDF es complejo "pegar" otro PDF sin librerías pesadas, 
                    # pero incluimos un recordatorio visual en la ficha.
                    pdf.seccion("VISUALIZACIÓN DE ARTE FINAL")
                    pdf.set_font("Arial", "I", 10)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 10, "Ver archivo adjunto 'DISENO_...' para pre-impresión.", ln=True)

                    pdf.output(FILE_TEMP_PDF)
                    
                    datos_e = {"cliente": cliente, "email": email_c, "material": material, "cantidad": cantidad, "ref": ref}
                    
                    if despachar_email(FILE_TEMP_PDF, archivo_af, datos_e):
                        st.success("ORDEN ENVIADA AL TALLER")
                        st.balloons()
                        if os.path.exists(FILE_TEMP_PDF): os.remove(FILE_TEMP_PDF)

if __name__ == "__main__":
    main()
