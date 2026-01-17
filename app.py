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
# 1. CONFIGURACIÓN E INTERFAZ DE ALTO NIVEL (UI/UX)
# =============================================================================
st.set_page_config(
    page_title="FlexyLabel Enterprise | Control de Producción",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def inject_full_industrial_theme():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

            /* Fondo y Tipografía Base */
            .stApp {
                background: radial-gradient(circle at top right, #1e293b, #0f172a);
                color: #f8fafc !important;
                font-family: 'Inter', sans-serif;
            }

            /* INPUTS: FONDO BLANCO, LETRA NEGRA (PEDIDO IVÁN) */
            input, select, textarea, div[data-baseweb="input"] input {
                color: #000000 !important;
                background-color: #ffffff !important;
                border-radius: 10px !important;
                font-weight: 700 !important;
                border: 2px solid #3b82f6 !important;
                font-size: 1rem !important;
            }
            
            /* Etiquetas de campo */
            label {
                color: #94a3b8 !important;
                font-size: 0.85rem !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: 0.5rem !important;
            }

            /* Contenedores de Formulario */
            div[data-testid="stForm"] {
                background: rgba(30, 41, 59, 0.7) !important;
                backdrop-filter: blur(15px);
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 24px !important;
                padding: 4rem !important;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7) !important;
            }

            /* Botón de Acción Principal */
            .stButton button {
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
                color: #ffffff !important;
                height: 4.5rem !important;
                border-radius: 15px !important;
                font-weight: 800 !important;
                font-size: 1.3rem !important;
                text-transform: uppercase;
                letter-spacing: 1px;
                border: none !important;
                width: 100% !important;
                box-shadow: 0 10px 20px rgba(37, 99, 235, 0.3) !important;
                transition: 0.3s all ease-in-out;
            }
            .stButton button:hover {
                transform: translateY(-3px);
                box-shadow: 0 15px 30px rgba(37, 99, 235, 0.5) !important;
            }

            /* Caja de Métricas */
            .metric-card {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-radius: 15px;
                border-left: 5px solid #3b82f6;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. MOTOR TÉCNICO DE PDF (DISEÑO PROFESIONAL)
# =============================================================================
class PDF_Industrial(FPDF):
    def header(self):
        # Fondo cabecera
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 45, 'F')
        self.set_xy(15, 15)
        self.set_font('Arial', 'B', 24)
        self.set_text_color(59, 130, 246)
        self.cell(0, 10, 'FLEXYLABEL ENTERPRISE', ln=True)
        self.set_font('Arial', '', 10)
        self.set_text_color(148, 163, 184)
        self.cell(0, 5, f'ORDEN DE TRABAJO | {datetime.datetime.now().strftime("%d/%m/%Y")}', ln=True)
        self.ln(20)

    def section_header(self, title):
        self.ln(5)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(30, 41, 59)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"  {title.upper()}", ln=True, fill=True)
        self.ln(4)

    def data_row(self, label, value, label2="", value2=""):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(71, 85, 105)
        self.cell(45, 8, f"{label}:", 0)
        self.set_font('Arial', '', 10)
        self.set_text_color(15, 23, 42)
        self.cell(55, 8, f"{value}", 0)
        if label2:
            self.set_font('Arial', 'B', 10)
            self.set_text_color(71, 85, 105)
            self.cell(45, 8, f"{label2}:", 0)
            self.set_font('Arial', '', 10)
            self.set_text_color(15, 23, 42)
            self.cell(0, 8, f"{value2}", 0)
        self.ln(8)

# =============================================================================
# 3. SISTEMA DE COMUNICACIONES (ENVÍO DUAL)
# =============================================================================
def ejecutar_logistica_envio(pdf_path, af_file, datos):
    try:
        user = st.secrets["email_usuario"]
        pwd = st.secrets["email_password"]

        # --- EMAIL PARA TALLER ---
        msg_t = MIMEMultipart()
        msg_t['From'] = user
        msg_t['To'] = "covet@etiquetes.com"
        msg_t['Subject'] = f"🔴 NUEVA ORDEN: {datos['cliente']} | REF: {datos['ref']}"
        msg_t.attach(MIMEText(f"Adjunta ficha técnica para producción de {datos['cliente']}.", 'plain'))

        # --- EMAIL PARA CLIENTE ---
        msg_c = MIMEMultipart()
        msg_c['From'] = user
        msg_c['To'] = datos['email_c']
        msg_c['Subject'] = "Confirmación de Pedido - FlexyLabel"
        msg_c.attach(MIMEText(f"Hola {datos['cliente']},\nHemos recibido tu pedido correctamente. Gracias.", 'plain'))

        # Proceso de Adjuntos
        with open(pdf_path, "rb") as f:
            payload = f.read()
            for m in [msg_t, msg_c]:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(payload)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="Ficha_{datos["ref"]}.pdf"')
                m.attach(part)

        # Arte Final (Solo Taller)
        af_part = MIMEBase('application', 'octet-stream')
        af_part.set_payload(af_file.getvalue())
        encoders.encode_base64(af_part)
        af_part.add_header('Content-Disposition', f'attachment; filename="DISENO_{datos["cliente"]}.pdf"')
        msg_t.attach(af_part)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(user, pwd)
        server.send_message(msg_t)
        server.send_message(msg_c)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error crítico de envío: {e}")
        return False

# =============================================================================
# 4. LÓGICA DE APLICACIÓN Y RENDERIZADO
# =============================================================================
inject_full_industrial_theme()

st.markdown("<h1 style='text-align:center;'>PORTAL DE PRODUCCIÓN <span style='font-weight:300;'>FLEXYLABEL</span></h1>", unsafe_allow_html=True)

# Layout de columnas laterales estéticas
L_COL, M_COL, R_COL = st.columns([1, 5, 1])

with M_COL:
    # --- SECCIÓN DINÁMICA DE BOBINADO (FUERA DEL FORM PARA REFRESCO INSTANTÁNEO) ---
    st.write("### ⚙️ CONFIGURACIÓN DE BOBINADO")
    
    # Imagen de mapa universal (Corregida)
    
    st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", 
             caption="MAPA DE REFERENCIA DE SALIDAS (1-8)", use_container_width=True)
    
    # SLIDER DINÁMICO: Al moverlo, el número de abajo cambia al instante
    sentido_final = st.select_slider("DESLIZA PARA SELECCIONAR LA POSICIÓN DE SALIDA", options=[str(i) for i in range(1, 9)], value="1")
    
    # RECUADRO DE CONFIRMACIÓN VISUAL (Iván, este es el que ahora sí se actualiza)
    st.markdown(f"""
        <div style="background:#1e40af; padding:30px; border-radius:20px; text-align:center; border:4px solid #3b82f6; margin-bottom:30px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <p style="color:#bfdbfe; font-size:1.1rem; margin:0; text-transform:uppercase; font-weight:800; letter-spacing:2px;">Sentido Seleccionado</p>
            <h1 style="margin:0; color:white; font-size:5rem; line-height:1;">{sentido_final}</h1>
            <p style="color:#60a5fa; margin:0; font-weight:600;">Comprueba que este número coincide con el esquema superior</p>
        </div>
    """, unsafe_allow_html=True)

    # --- FORMULARIO DE DATOS ---
    with st.form("main_enterprise_form"):
        st.write("### 🏢 INFORMACIÓN DEL PROYECTO")
        c1, c2, c3 = st.columns([2, 2, 1])
        cliente = c1.text_input("CLIENTE / RAZÓN SOCIAL")
        email_cliente = c2.text_input("EMAIL DE CONTACTO CLIENTE")
        referencia = c3.text_input("REF. INTERNA", value=f"FX-{datetime.date.today().year}")

        st.write("### 📐 DATOS TÉCNICOS")
        c4, c5, c6 = st.columns(3)
        ancho = c4.number_input("ANCHO (mm)", value=100)
        largo = c5.number_input("LARGO (mm)", value=100)
        cantidad = c6.number_input("CANTIDAD TOTAL", value=5000)

        c7, c8, c9 = st.columns(3)
        material = c7.selectbox("MATERIAL", ["PP Blanco", "PP Transparente", "Couché", "Térmico", "Verjurado"])
        mandril = c8.selectbox("MANDRIL", ["76mm", "40mm", "25mm"])
        etq_rollo = c9.number_input("ETIQ / ROLLO", value=1000)

        st.write("### 📂 ARCHIVOS Y TALLER")
        archivo_pdf = st.file_uploader("SUBIR ARTE FINAL (PDF)", type=["pdf"])
        observaciones = st.text_area("INSTRUCCIONES ESPECIALES PARA PRODUCCIÓN")

        # Cálculo de metros lineales automático
        ml_total = (cantidad * (largo + 3)) / 1000
        st.markdown(f"""
            <div class="metric-card">
                <p style="margin:0; font-size:0.8rem; color:#94a3b8;">CONSUMO DE MATERIA PRIMA</p>
                <h2 style="margin:0; color:#3b82f6;">{round(ml_total, 2)} Metros Lineales</h2>
            </div>
        """, unsafe_allow_html=True)

        # BOTÓN DE ENVÍO
        if st.form_submit_button("🚀 CONFIRMAR Y LANZAR ORDEN"):
            if not cliente or not archivo_pdf or not email_cliente:
                st.error("⚠️ Faltan datos obligatorios para procesar la orden.")
            else:
                # 1. Crear PDF Profesional
                pdf = PDF_Industrial()
                pdf.add_page()
                pdf.section_header("Información Comercial")
                pdf.data_row("Cliente", cliente, "Referencia", referencia)
                pdf.data_row("Email", email_cliente)
                
                pdf.section_header("Ficha de Materiales")
                pdf.data_row("Soporte", material, "Cantidad", f"{cantidad} uds")
                pdf.data_row("Medidas", f"{ancho} x {largo} mm", "Etiq/Rollo", etq_rollo)
                
                pdf.section_header("Especificaciones de Taller")
                pdf.data_row("Sentido Salida", sentido_final, "Mandril", mandril)
                pdf.data_row("Consumo", f"{round(ml_total, 2)} ml")
                
                if observaciones:
                    pdf.section_header("Notas Adicionales")
                    pdf.set_font("Arial", "", 10)
                    pdf.multi_cell(0, 8, observaciones)

                temp_file = f"ORDEN_{referencia}.pdf"
                pdf.output(temp_file)

                # 2. Enviar emails
                with st.spinner("Procesando envío..."):
                    if ejecutar_logistica_envio(temp_file, archivo_pdf, 
                                               {"cliente": cliente, "email_c": email_cliente, "ref": referencia}):
                        st.success(f"ORDEN {referencia} REGISTRADA CORRECTAMENTE.")
                        st.balloons()
                        if os.path.exists(temp_file): os.remove(temp_file)

st.markdown("<p style='text-align:center; color:#475569; font-size:0.8rem; margin-top:5rem;'>FlexyLabel Order System v4.6 Enterprise | 2026</p>", unsafe_allow_html=True)
