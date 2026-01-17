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
# 1. MOTOR DE ESTILOS "OBSIDIAN NEON" (DISEÑO PREMIUM)
# =============================================================================
def aplicar_estilos_premium():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap');

            /* Fondo y Scroll */
            .stApp {
                background-color: #0d1117;
                color: #58a6ff;
                font-family: 'Inter', sans-serif;
            }

            /* Título Impactante */
            .main-title {
                font-family: 'Orbitron', sans-serif;
                font-size: 3.5rem;
                text-align: center;
                color: #58a6ff;
                text-shadow: 0 0 20px rgba(88, 166, 255, 0.6);
                margin-top: -50px;
                margin-bottom: 2rem;
            }

            /* Tarjetas de Modelos (Glassmorphism Dark) */
            .css-card {
                background: rgba(22, 27, 34, 0.8);
                padding: 2rem;
                border-radius: 20px;
                border: 1px solid #30363d;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                margin-bottom: 2rem;
            }

            /* Inputs Personalizados Azul Neón */
            input, select, textarea {
                background-color: #0d1117 !important;
                color: #58a6ff !important;
                border: 1px solid #30363d !important;
            }
            
            label {
                color: #58a6ff !important;
                font-family: 'Orbitron', sans-serif !important;
                font-size: 0.8rem !important;
                letter-spacing: 1px;
            }

            /* Botones Pro */
            .stButton>button {
                background: linear-gradient(135deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: white !important;
                border: none !important;
                font-family: 'Orbitron', sans-serif !important;
                font-weight: 700 !important;
                border-radius: 12px !important;
                transition: 0.3s all ease;
            }
            
            .stButton>button:hover {
                transform: translateY(-3px);
                box-shadow: 0 0 20px rgba(88, 166, 255, 0.8) !important;
            }

            /* Sidebar y Tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 10px;
                background-color: transparent;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: #161b22;
                border: 1px solid #30363d;
                color: #8b949e;
                border-radius: 10px 10px 0 0;
                padding: 10px 20px;
            }
            .stTabs [aria-selected="true"] {
                color: #58a6ff !important;
                border-color: #58a6ff !important;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. LÓGICA DE ESTADO (MULTIMODELO)
# =============================================================================
if 'num_modelos' not in st.session_state:
    st.session_state.num_modelos = 1

def añadir_modelo():
    st.session_state.num_modelos += 1

# =============================================================================
# 3. GENERADOR DE PDF TÉCNICO
# =============================================================================
class FlexyIndustrialPDF(FPDF):
    def header(self):
        self.set_fill_color(13, 17, 23)
        self.rect(0, 0, 210, 50, 'F')
        self.set_xy(10, 15)
        self.set_font("Arial", 'B', 30)
        self.set_text_color(88, 166, 255)
        self.cell(0, 15, "FLEXYLABEL PRODUCTION", ln=True)
        self.set_font("Arial", 'I', 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, "ORDEN TÉCNICA MULTI-MODELO // CONFIRMACIÓN DE PEDIDO", ln=True)
        self.ln(20)

# =============================================================================
# 4. ENVÍO DE CORREOS (TALLER + CLIENTE)
# =============================================================================
def enviar_notificaciones(pdf_path, artes_finales, datos_c):
    try:
        user = st.secrets["email_usuario"]
        pwd = st.secrets["email_password"]
        destinos = [("TALLER", "covet@etiquetes.com"), ("CLIENTE", datos_c['email'])]

        for tipo, correo in destinos:
            msg = MIMEMultipart()
            msg['From'] = user
            msg['To'] = correo
            msg['Subject'] = f"🟢 {'ORDEN DE TRABAJO' if tipo == 'TALLER' else 'CONFIRMACIÓN DE PEDIDO'} - {datos_c['cliente']}"
            
            cuerpo = f"Adjuntamos el documento técnico para el cliente {datos_c['cliente']}.\n"
            if tipo == "CLIENTE":
                cuerpo += "\nGracias por su pedido. Adjuntamos la confirmación técnica para su revisión."
            
            msg.attach(MIMEText(cuerpo, 'plain'))

            with open(pdf_path, "rb") as f:
                p = MIMEBase('application', 'octet-stream')
                p.set_payload(f.read())
                encoders.encode_base64(p)
                p.add_header('Content-Disposition', f'attachment; filename={pdf_path}')
                msg.attach(p)

            if tipo == "TALLER":
                for af in artes_finales:
                    if af:
                        p_af = MIMEBase('application', 'octet-stream')
                        p_af.set_payload(af.getvalue())
                        encoders.encode_base64(p_af)
                        p_af.add_header('Content-Disposition', f'attachment; filename="AF_{af.name}"')
                        msg.attach(p_af)

            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(user, pwd)
            server.send_message(msg)
            server.quit()
        return True
    except Exception as e:
        st.error(f"Error crítico en el servidor: {e}")
        return False

# =============================================================================
# 5. UI PRINCIPAL
# =============================================================================
aplicar_estilos_premium()

st.markdown('<h1 class="main-title">FLEXYLABEL</h1>', unsafe_allow_html=True)

# Bloque 1: Cliente
with st.container():
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 🏢 DATOS DE IDENTIFICACIÓN")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        cliente = st.text_input("EMPRESA / CLIENTE")
    with col_c2:
        email_cliente = st.text_input("EMAIL PARA CONFIRMACIÓN")
    st.markdown('</div>', unsafe_allow_html=True)

# Bloque 2: Modelos (Pestañas Dinámicas)
st.markdown("### 📦 REFERENCIAS Y DISEÑOS")
tabs = st.tabs([f"MODELO {i+1}" for i in range(st.session_state.num_modelos)])
modelos_data = []

for i in range(st.session_state.num_modelos):
    with tabs[i]:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            ref = st.text_input(f"Nombre del Diseño / Referencia", key=f"ref_{i}")
        with col2:
            ancho = st.number_input(f"Ancho (mm)", 1, 500, 100, key=f"anc_{i}")
        with col3:
            largo = st.number_input(f"Largo (mm)", 1, 500, 100, key=f"lar_{i}")
        
        col4, col5, col6 = st.columns(3)
        with col4:
            cant = st.number_input(f"Cantidad Total", 100, 1000000, 5000, key=f"cant_{i}")
        with col5:
            etq_r = st.number_input(f"Etiquetas por Rollo", 50, 10000, 1000, key=f"etq_{i}")
        with col6:
            archivo = st.file_uploader(f"Subir Arte Final (PDF)", type=["pdf"], key=f"file_{i}")
        
        modelos_data.append({"ref": ref, "ancho": ancho, "largo": largo, "cant": cant, "etq_r": etq_r, "archivo": archivo})
        st.markdown('</div>', unsafe_allow_html=True)

if st.button("➕ AÑADIR OTRA REFERENCIA"):
    añadir_modelo()
    st.rerun()

# Bloque 3: Producción General
st.markdown("### ⚙️ ESPECIFICACIONES DE TALLER")
with st.container():
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.write("**Sentido de Salida (Posiciones 1-8)**")
        
        sentido = st.select_slider("Selecciona posición", options=[str(i) for i in range(1, 9)], value="3")
        salida = st.radio("Bobinado", ["Exterior", "Interior"], horizontal=True)
    with col_t2:
        material = st.selectbox("Material de Soporte", ["PP Blanco", "Couché", "Térmico", "Verjurado"])
        mandril = st.selectbox("Diámetro Mandril", ["76mm", "40mm", "25mm"])
        obs = st.text_area("Observaciones Generales de Producción")
    st.markdown('</div>', unsafe_allow_html=True)

# Botón Final
if st.button("🚀 VALIDAR Y ENVIAR TODO EL PEDIDO"):
    if not cliente or not email_cliente:
        st.error("❌ Iván, rellena los datos del cliente antes de enviar.")
    else:
        with st.spinner("Generando documentación técnica..."):
            pdf = FlexyIndustrialPDF()
            pdf.add_page()
            
            # Datos Cliente en PDF
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, f"CLIENTE: {cliente}", ln=True)
            pdf.ln(5)

            artes = []
            for m in modelos_data:
                pdf.set_fill_color(240, 240, 240)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, f"MODELO: {m['ref']}", ln=True, fill=True)
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 8, f"Medidas: {m['ancho']}x{m['largo']}mm | Cant: {m['cant']} | Etq/Rollo: {m['etq_r']}", ln=True)
                pdf.ln(2)
                artes.append(m['archivo'])

            # Footer PDF con datos de taller
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "ESPECIFICACIONES DE BOBINADO", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Sentido: Posición {sentido} | Salida: {salida} | Mandril: {mandril}", ln=True)
            pdf.cell(0, 8, f"Material: {material}", ln=True)

            nombre_pdf = f"ORDEN_{cliente}.pdf".replace(" ", "_")
            pdf.output(nombre_pdf)
            
            if enviar_notificaciones(nombre_pdf, artes, {"cliente": cliente, "email": email_cliente}):
                st.success("✅ ¡Éxito! Pedido enviado a taller y confirmación enviada al cliente.")
                st.balloons()
                time.sleep(3)
                if os.path.exists(nombre_pdf): os.remove(nombre_pdf)
