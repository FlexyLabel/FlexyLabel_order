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
# 1. CONFIGURACIÓN DE PÁGINA Y CONSTANTES
# =============================================================================
st.set_page_config(
    page_title="FLEXYLABEL ORDER v4.0 | Production System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuración de rutas y nombres
FILE_TEMP_PDF = "ORDEN_PRODUCCION_TEMP.pdf"
DESTINATARIO_TALLER = "covet@etiquetes.com"

# =============================================================================
# 2. MOTOR DE ESTILO CSS (DARK INDUSTRIAL & NEÓN)
# =============================================================================
def apply_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

            /* Base App */
            .stApp {
                background-color: #0d1117;
                color: #ffffff !important;
                font-family: 'Inter', sans-serif;
            }

            /* Títulos y Etiquetas */
            h1, h2, h3, label, p, .stMarkdown {
                color: #ffffff !important;
                font-family: 'Orbitron', sans-serif !important;
            }

            .main-header {
                text-align: center;
                padding: 2rem;
                background: linear-gradient(180deg, #161b22 0%, transparent 100%);
                border-bottom: 1px solid #30363d;
                margin-bottom: 2rem;
            }

            /* Efecto Hover en Contenedores */
            div[data-testid="stForm"], .st-emotion-cache-1r6slb0 {
                background: rgba(22, 27, 34, 0.9) !important;
                border: 2px solid #30363d !important;
                border-radius: 20px !important;
                padding: 2.5rem !important;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            }

            div[data-testid="stForm"]:hover {
                border-color: #58a6ff !important;
                box-shadow: 0 0 30px rgba(88, 166, 255, 0.2) !important;
                transform: translateY(-5px);
            }

            /* Inputs */
            .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
                background-color: #0d1117 !important;
                border: 1px solid #30363d !important;
                color: #58a6ff !important;
                font-family: 'JetBrains Mono', monospace !important;
            }

            /* Imágenes Laterales */
            .side-img {
                width: 100%;
                border-radius: 12px;
                border: 1px solid #30363d;
                margin-bottom: 1.5rem;
                filter: grayscale(80%);
                transition: 0.5s;
            }
            .side-img:hover {
                filter: grayscale(0%);
                border-color: #58a6ff;
            }

            /* Botón Principal */
            .stButton button {
                background: linear-gradient(90deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: white !important;
                height: 4rem !important;
                border-radius: 12px !important;
                font-weight: 800 !important;
                text-transform: uppercase;
                letter-spacing: 2px;
                border: none !important;
                width: 100% !important;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 3. CLASE GENERADORA DE PDF TÉCNICO (EL CORAZÓN DEL PROGRAMA)
# =============================================================================
class PDF_Orden(FPDF):
    def header(self):
        # Fondo decorativo en cabecera
        self.set_fill_color(22, 27, 34)
        self.rect(0, 0, 210, 45, 'F')
        
        self.set_xy(10, 15)
        self.set_font('Arial', 'B', 24)
        self.set_text_color(88, 166, 255)
        self.cell(0, 10, 'FLEXYLABEL // HOJA DE PRODUCCIÓN', ln=True, align='L')
        
        self.set_font('Arial', '', 10)
        self.set_text_color(150, 150, 150)
        fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 10, f'Generado el: {fecha} | Sistema V4.0', ln=True, align='L')
        self.ln(10)

    def seccion_titulo(self, titulo):
        self.set_fill_color(48, 54, 61)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'  {titulo}', ln=True, fill=True)
        self.ln(4)

    def fila_datos(self, label, valor, label2="", valor2=""):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(50, 50, 50)
        self.cell(40, 8, f"{label}:", 0)
        self.set_font('Arial', '', 10)
        self.cell(55, 8, f"{valor}", 0)
        
        if label2:
            self.set_font('Arial', 'B', 10)
            self.cell(40, 8, f"{label2}:", 0)
            self.set_font('Arial', '', 10)
            self.cell(0, 8, f"{valor2}", 0)
        self.ln(8)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, 'Este documento es una orden oficial de producción de FlexyLabel.', 0, 0, 'C')
        self.ln(5)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

# =============================================================================
# 4. LÓGICA DE CÁLCULO DE INGENIERÍA
# =============================================================================
def calcular_ingenieria(cantidad, ancho, largo, avance=3):
    try:
        metros_lineales = (cantidad * (largo + avance)) / 1000
        metros_cuadrados = (ancho / 1000) * metros_lineales
        peso_aprox = metros_cuadrados * 0.15 # Estimación base
        return round(metros_lineales, 2), round(metros_cuadrados, 2), round(peso_aprox, 2)
    except:
        return 0, 0, 0

# =============================================================================
# 5. FUNCIÓN DE ENVÍO DE EMAIL (BLINDADA)
# =============================================================================
def enviar_orden_completa(archivo_pdf_tecnico, archivo_arte_final, datos):
    try:
        user = st.secrets["email_usuario"]
        passw = st.secrets["email_password"]

        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = f"{DESTINATARIO_TALLER}, {datos['email_usuario']}"
        msg['Subject'] = f"🔴 NUEVA ORDEN: {datos['cliente']} | {datos['referencia']}"

        # Cuerpo del mensaje
        cuerpo = f"""
        SISTEMA DE PRODUCCIÓN FLEXYLABEL
        ----------------------------------
        Se ha generado una nueva orden de impresión.
        
        CLIENTE: {datos['cliente']}
        REFERENCIA: {datos['referencia']}
        MATERIAL: {datos['material']}
        CANTIDAD: {datos['cantidad']} uds.
        
        Se adjuntan dos archivos:
        1. Ficha Técnica (PDF generado por el sistema)
        2. Arte Final (PDF subido por el cliente)
        """
        msg.attach(MIMEText(cuerpo, 'plain'))

        # Adjuntar 1: Ficha Técnica
        with open(archivo_pdf_tecnico, "rb") as f:
            part1 = MIMEBase('application', 'octet-stream')
            part1.set_payload(f.read())
            encoders.encode_base64(part1)
            part1.add_header('Content-Disposition', f'attachment; filename="FICHA_TECNICA_{datos["cliente"]}.pdf"')
            msg.attach(part1)

        # Adjuntar 2: Arte Final
        if archivo_arte_final:
            part2 = MIMEBase('application', 'octet-stream')
            part2.set_payload(archivo_arte_final.getvalue())
            encoders.encode_base64(part2)
            part2.add_header('Content-Disposition', f'attachment; filename="ARTE_FINAL_{datos["referencia"]}.pdf"')
            msg.attach(part2)

        # Conexión SMTP
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(user, passw)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Fallo crítico en el servidor de correo: {e}")
        return False

# =============================================================================
# 6. ESTRUCTURA DE LA APLICACIÓN (FRONTEND)
# =============================================================================
def main():
    apply_custom_css()

    # Layout de 3 Columnas
    col_l, col_main, col_r = st.columns([0.8, 4, 0.8])

    with col_l:
        st.image("https://images.unsplash.com/photo-1610473069150-13645396b270?w=400", use_container_width=True)
        st.image("https://images.unsplash.com/photo-1563089145-599997674d42?w=400", use_container_width=True)
        st.image("https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=400", use_container_width=True)

    with col_r:
        st.image("https://images.unsplash.com/photo-1590402494682-cd3fb53b1f71?w=400", use_container_width=True)
        st.image("https://images.unsplash.com/photo-1626785774573-4b799315345d?w=400", use_container_width=True)
        st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400", use_container_width=True)

    with col_main:
        st.markdown('<div class="main-header"><h1>FLEXYLABEL ORDER v4.0</h1></div>', unsafe_allow_html=True)

        with st.form("form_produccion"):
            # SECCIÓN CLIENTE
            st.write("### 🏢 INFORMACIÓN COMERCIAL")
            c1, c2, c3 = st.columns([2, 2, 1])
            cliente = c1.text_input("RAZÓN SOCIAL / CLIENTE")
            email_usuario = c2.text_input("EMAIL PARA COPIA DE ORDEN")
            referencia = c3.text_input("REF. INTERNA", value="ORD-001")

            st.write("---")

            # SECCIÓN TÉCNICA
            st.write("### 📐 ESPECIFICACIONES DE PRODUCTO")
            c4, c5, c6 = st.columns(3)
            ancho = c4.number_input("ANCHO ETIQUETA (mm)", 10, 500, 100)
            largo = c5.number_input("LARGO ETIQUETA (mm)", 10, 500, 100)
            cantidad = c6.number_input("CANTIDAD TOTAL (uds)", 100, 2000000, 5000)

            c7, c8, c9 = st.columns(3)
            material = c7.selectbox("SOPORTE / PAPEL", ["PP Blanco", "PP Transparente", "Couché Brillante", "Térmico Protegido", "Verjurado Mancha"])
            mandril = c8.selectbox("DIÁMETRO MANDRIL", ["76mm", "40mm", "25mm"])
            etq_rollo = c9.number_input("ETIQUETAS POR ROLLO", 50, 10000, 1000)

            st.write("---")

            # SECCIÓN TALLER
            st.write("### ⚙️ PARÁMETROS DE BOBINADO")
            c10, c11 = st.columns([2, 1])
            with c10:
                st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", width=400)
                sentido = st.select_slider("SENTIDO DE SALIDA", options=[str(i) for i in range(1, 9)], value="3")
            with c11:
                archivo_af = st.file_uploader("SUBIR ARTE FINAL (PDF)", type=["pdf"])
                observaciones = st.text_area("OBSERVACIONES DE PRODUCCIÓN", placeholder="Ej: Tintas Pantone, troquel especial...")

            # Cálculos automáticos en pantalla
            ml, m2, peso = calcular_ingenieria(cantidad, ancho, largo)
            st.info(f"💡 RESUMEN TÉCNICO: {ml} metros lineales | {m2} m² estimados.")

            # BOTÓN DE ENVÍO
            if st.form_submit_button("🚀 GENERAR Y ENVIAR ORDEN"):
                if not cliente or not archivo_af or not email_usuario:
                    st.error("⚠️ Iván, no puedo procesar la orden sin Cliente, Email o PDF.")
                else:
                    # 1. Crear el PDF Técnico
                    pdf = PDF_Orden()
                    pdf.add_page()
                    
                    pdf.seccion_titulo("DATOS DEL CLIENTE")
                    pdf.fila_datos("Cliente", cliente, "Referencia", referencia)
                    pdf.fila_datos("Email", email_usuario)
                    
                    pdf.seccion_titulo("ESPECIFICACIONES TÉCNICAS")
                    pdf.fila_datos("Medidas", f"{ancho} x {largo} mm", "Cantidad", f"{cantidad} uds")
                    pdf.fila_datos("Material", material, "Etiq/Rollo", etq_rollo)
                    
                    pdf.seccion_titulo("DATOS DE TALLER")
                    pdf.fila_datos("Sentido Salida", sentido, "Mandril", mandril)
                    pdf.fila_datos("Metros Lineales", f"{ml} m", "Superficie", f"{m2} m2")
                    
                    pdf.seccion_titulo("OBSERVACIONES")
                    pdf.set_font('Arial', '', 10)
                    pdf.multi_cell(0, 10, observaciones if observaciones else "Sin observaciones adicionales.")

                    # Guardar temporalmente
                    pdf.output(FILE_TEMP_PDF)

                    # 2. Enviar por Email
                    datos_envio = {
                        "cliente": cliente, "referencia": referencia, "material": material,
                        "cantidad": cantidad, "email_usuario": email_usuario
                    }

                    with st.spinner("Generando documentos y contactando con taller..."):
                        if enviar_orden_completa(FILE_TEMP_PDF, archivo_af, datos_envio):
                            st.success(f"✅ ORDEN ENVIADA: Se ha enviado la ficha técnica y el diseño a {DESTINATARIO_TALLER}")
                            st.balloons()
                            if os.path.exists(FILE_TEMP_PDF):
                                os.remove(FILE_TEMP_PDF)
                        else:
                            st.error("❌ Fallo en el envío. Revisa tus Secrets en Streamlit Cloud.")

    st.markdown("<p style='text-align:center; color:#30363d; font-size:0.7rem; margin-top:5rem;'>FLEXYLABEL CLOUD PRODUCTION SYSTEM // 2026</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
