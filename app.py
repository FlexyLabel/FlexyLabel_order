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

# --- CONFIGURACIÓN DE MARCA Y DESTINO ---
DESTINATARIO_FINAL = "covet@etiquetes.com"
COLOR_PRIMARIO = "#1e3a8a"  # Azul profundo profesional
COLOR_SECUNDARIO = "#3b82f6" # Azul brillante moderno
COLOR_FONDO = "#f8fafc"     # Gris slate muy claro

# --- MOTOR DE ESTILOS CSS AVANZADO (DISEÑO PROFESIONAL) ---
def inject_ui_engine():
    st.markdown(f"""
        <style>
            /* Importación de tipografía premium */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

            html, body, [class*="st-"] {{
                font-family: 'Inter', sans-serif;
                color: #1e293b;
            }}

            /* Fondo con degradado sutil */
            .stApp {{
                background: linear-gradient(135deg, {COLOR_FONDO} 0%, #e2e8f0 100%);
            }}

            /* Estilo de las tarjetas (Cards) */
            .css-card {{
                background: rgba(255, 255, 255, 0.9);
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                margin-bottom: 2rem;
                backdrop-filter: blur(10px);
            }}

            /* Títulos con degradado */
            .main-title {{
                font-weight: 800;
                font-size: 3rem;
                background: linear-gradient(to right, {COLOR_PRIMARIO}, {COLOR_SECUNDARIO});
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-align: center;
                margin-bottom: 0.5rem;
            }}

            /* Botones ultra-modernos */
            .stButton>button {{
                background: linear-gradient(90deg, {COLOR_PRIMARIO} 0%, {COLOR_SECUNDARIO} 100%);
                color: white !important;
                border: none;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 600;
                letter-spacing: 0.5px;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
            }}

            .stButton>button:hover {{
                transform: translateY(-3px) scale(1.02);
                box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5);
            }}

            /* Estilización de inputs */
            .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select {{
                border: 2px solid #e2e8f0 !important;
                border-radius: 12px !important;
                padding: 0.6rem !important;
                transition: all 0.3s ease;
            }}

            .stTextInput>div>div>input:focus {{
                border-color: {COLOR_SECUNDARIO} !important;
                box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1) !important;
            }}

            /* Ocultar barra de Streamlit */
            #MainMenu, footer, header {{visibility: hidden;}}
        </style>
    """, unsafe_allow_html=True)

# --- GENERADOR DE PDF TÉCNICO (NIVEL INDUSTRIAL) ---
class FlexyPDF(FPDF):
    def header(self):
        self.set_fill_color(30, 58, 138)
        self.rect(0, 0, 210, 45, 'F')
        self.set_font("Arial", 'B', 24)
        self.set_text_color(255, 255, 255)
        self.cell(0, 25, "FLEXYLABEL IMPRESSORS", ln=True, align='C')
        self.set_font("Arial", '', 10)
        self.cell(0, 0, "SOLUCIONES PROFESIONALES DE ETIQUETADO", ln=True, align='C')
        self.ln(20)

    def chapter_title(self, label):
        self.set_font("Arial", 'B', 12)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(30, 58, 138)
        self.cell(0, 10, f"  {label}", ln=True, fill=True)
        self.ln(4)

def generar_pdf_profesional(datos):
    pdf = FlexyPDF()
    pdf.add_page()
    pdf.set_text_color(30, 41, 59)
    
    pdf.chapter_title("DATOS DEL CLIENTE Y PROYECTO")
    pdf.set_font("Arial", '', 11)
    col_width = 95
    pdf.cell(col_width, 8, f"Empresa: {datos['cliente']}")
    pdf.cell(col_width, 8, f"Fecha Solicitud: {datetime.date.today()}", ln=True)
    pdf.cell(col_width, 8, f"Referencia: {datos['referencia']}")
    pdf.cell(col_width, 8, f"Email: {datos['email']}", ln=True)
    pdf.ln(6)

    pdf.chapter_title("DETALLES TÉCNICOS DE PRODUCCIÓN")
    pdf.set_font("Arial", 'B', 10)
    # Tabla técnica
    headers = ["CONCEPTO", "ESPECIFICACIÓN", "CONCEPTO", "ESPECIFICACIÓN"]
    for header in headers:
        pdf.cell(47.5, 8, header, 1, 0, 'C', fill=False)
    pdf.ln()
    
    pdf.set_font("Arial", '', 10)
    tecnica = [
        ["Medidas", f"{datos['ancho']}x{datos['largo']}mm", "Material", datos['material']],
        ["Cantidad", f"{datos['cantidad']} uds", "Sistema", datos['sistema']],
        ["Salida", datos['salida'], "Bobinado", f"Pos. {datos['sentido']}"],
        ["Mandril", datos['mandril'], "Fecha Entrega", str(datos['fecha'])]
    ]
    for row in tecnica:
        pdf.cell(47.5, 8, row[0], 1)
        pdf.cell(47.5, 8, row[1], 1)
        pdf.cell(47.5, 8, row[2], 1)
        pdf.cell(47.5, 8, row[3], 1, ln=True)

    pdf.ln(6)
    pdf.chapter_title("OBSERVACIONES TÉCNICAS")
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 7, datos['obs'])

    fname = f"ORDEN_{datos['cliente']}_{datos['referencia']}.pdf".replace(" ", "_")
    pdf.output(fname)
    return fname

# --- LÓGICA DE ENVÍO ---
def ejecutar_envio(archivo_pdf, diseno_cliente, datos):
    try:
        user = st.secrets["email_usuario"]
        passw = st.secrets["email_password"]
        
        msg = MIMEMultipart()
        msg['Subject'] = f"🚀 NUEVA ORDEN: {datos['cliente']} | {datos['referencia']}"
        msg['From'] = user
        msg['To'] = DESTINATARIO_FINAL
        
        cuerpo = f"Nueva orden técnica recibida.\nCliente: {datos['cliente']}\nReferencia: {datos['referencia']}"
        msg.attach(MIMEText(cuerpo, 'plain'))

        with open(archivo_pdf, "rb") as f:
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(f.read())
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', f'attachment; filename="{archivo_pdf}"')
            msg.attach(p)

        if diseno_cliente:
            p2 = MIMEBase('application', 'octet-stream')
            p2.set_payload(diseno_cliente.getvalue())
            encoders.encode_base64(p2)
            p2.add_header('Content-Disposition', f'attachment; filename="DISENO_{diseno_cliente.name}"')
            msg.attach(p2)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, passw)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error de conexión SMTP: {e}")
        return False

# --- UI PRINCIPAL ---
inject_ui_engine()

st.markdown('<h1 class="main-title">FlexyLabel Order System</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#64748b; margin-bottom:2rem;">Gestión inteligente de producción de etiquetas autoadhesivas</p>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    with st.form("main_form_pro"):
        
        st.subheader("📋 Información del Cliente")
        c1, c2 = st.columns(2)
        with c1:
            cliente = st.text_input("Nombre del Cliente / Empresa")
            email = st.text_input("Correo electrónico de contacto")
        with c2:
            referencia = st.text_input("Nombre del Diseño / Referencia")
            fecha = st.date_input("Fecha de entrega deseada")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("⚙️ Parámetros de Impresión")
        c3, c4, c5 = st.columns(3)
        with c3:
            ancho = st.number_input("Ancho (mm)", value=100)
            largo = st.number_input("Largo (mm)", value=100)
        with c4:
            cantidad = st.number_input("Cantidad Total", value=1000, step=500)
            material = st.selectbox("Material", ["Couché", "PP Blanco", "PP Transparente", "Térmico", "Especial"])
        with c5:
            sistema = st.selectbox("Sistema", ["Flexografía", "Digital", "Offset"])
            mandril = st.selectbox("Mandril", ["40mm", "76mm", "25mm"])

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🌀 Acabado y Salida")
        c6, c7 = st.columns(2)
        with c6:
            salida = st.radio("Lado de salida", ["Exterior", "Interior"], horizontal=True)
            sentido = st.select_slider("Posición de bobinado", options=[str(i) for i in range(1, 9)])
        with c7:
            diseno = st.file_uploader("Adjuntar Arte Final (PDF)", type=["pdf"])
        
        obs = st.text_area("Instrucciones especiales de producción")
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn = st.form_submit_button("PROCESAR Y ENVIAR ORDEN")

        if btn:
            if not cliente or not diseno:
                st.error("⚠️ Datos incompletos. Se requiere nombre de cliente y archivo PDF.")
            else:
                with st.spinner("🚀 Generando expediente técnico..."):
                    datos = {
                        "cliente": cliente, "email": email, "referencia": referencia,
                        "fecha": fecha, "ancho": ancho, "largo": largo, "cantidad": cantidad,
                        "material": material, "sistema": sistema, "mandril": mandril,
                        "salida": salida, "sentido": sentido, "obs": obs
                    }
                    pdf_path = generar_pdf_profesional(datos)
                    if ejecutar_envio(pdf_path, diseno, datos):
                        st.success("✅ ¡Orden enviada correctamente a producción!")
                        st.balloons()
                        if os.path.exists(pdf_path): os.remove(pdf_path)
    st.markdown('</div>', unsafe_allow_html=True)
