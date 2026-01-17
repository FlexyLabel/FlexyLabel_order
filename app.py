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
import re

# =============================================================================
# SECTION 1: SYSTEM ARCHITECTURE & CORE CONSTANTS (Líneas 1-150)
# =============================================================================
SYSTEM_VERSION = "2.5.0-ENTERPRISE"
LAST_UPDATE = "2026-01-17"
COMPANY_NAME = "FLEXYLABEL IMPRESSORS S.L."
ADMIN_EMAIL = "covet@etiquetes.com"

# Definición de Temas Visuales (Variables de Diseño)
UI_THEME = {
    "primary": "#002366",       # Blue Royal
    "secondary": "#00D4FF",     # Electric Cyan
    "accent": "#F59E0B",        # Amber
    "success": "#10B981",       # Emerald
    "danger": "#EF4444",        # Rose
    "neutral": "#F8FAFC",       # Slate 50
    "border": "#E2E8F0",        # Slate 200
    "text_main": "#0F172A",     # Slate 900
    "text_muted": "#64748B"     # Slate 500
}

# Base de Datos Técnica de Materiales (Lógica Industrial)
MATERIAL_DB = {
    "Papel Couché Brillante": {"micras": 80, "gramaje": 82, "adhesivo": "Acrílico Permanente"},
    "Polipropileno Blanco": {"micras": 60, "gramaje": 58, "adhesivo": "Hotmelt Fuerte"},
    "Polipropileno Transparente": {"micras": 50, "gramaje": 48, "adhesivo": "Acrílico Extra-Clear"},
    "Papel Térmico Top": {"micras": 75, "gramaje": 78, "adhesivo": "Congelación"},
    "Papel Verjurado Crema": {"micras": 95, "gramaje": 90, "adhesivo": "Especial Vinos"},
    "PET Metalizado Oro": {"micras": 50, "gramaje": 55, "adhesivo": "Permanente Industrial"}
}

# =============================================================================
# SECTION 2: ADVANCED CSS UI ENGINE (Líneas 151-500)
# =============================================================================
def apply_enterprise_styles():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400&display=swap');

        /* Global Reset */
        .main {{
            background: linear-gradient(180deg, {UI_THEME['neutral']} 0%, #EDF2F7 100%);
            font-family: 'Inter', sans-serif;
            color: {UI_THEME['text_main']};
        }}

        /* Dashboard Cards */
        .st-emotion-cache-1r6slb0 {{
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.95);
            padding: 3rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            border: 1px solid white;
            backdrop-filter: blur(20px);
        }}

        /* Header Animation */
        .header-title {{
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, {UI_THEME['primary']}, {UI_THEME['secondary']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            letter-spacing: -0.05em;
            margin-bottom: 0;
        }}

        /* Input Styling */
        .stTextInput input, .stNumberInput input, .stSelectbox select {{
            border: 2px solid {UI_THEME['border']} !important;
            border-radius: 12px !important;
            padding: 0.75rem !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .stTextInput input:focus {{
            border-color: {UI_THEME['secondary']} !important;
            box-shadow: 0 0 0 4px rgba(0, 212, 255, 0.15) !important;
        }}

        /* Industrial Submit Button */
        .stButton button {{
            background: {UI_THEME['primary']} !important;
            background: linear-gradient(135deg, {UI_THEME['primary']} 0%, #1e3a8a 100%) !important;
            color: white !important;
            height: 60px !important;
            border-radius: 16px !important;
            font-weight: 700 !important;
            font-size: 1.1rem !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            border: none !important;
            box-shadow: 0 10px 15px -3px rgba(30, 58, 138, 0.3) !important;
            transition: all 0.4s ease !important;
            width: 100% !important;
        }}

        .stButton button:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 25px -5px rgba(30, 58, 138, 0.4) !important;
        }}

        /* Tooltip and badges */
        .tech-badge {{
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            background: {UI_THEME['secondary']};
            color: white;
            margin-left: 10px;
        }}
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# SECTION 3: CALCULATION ENGINE (Líneas 501-700)
# =============================================================================
def calcular_diametro_bobina(cantidad, ancho, largo, mandril_mm):
    # Lógica física de bobinado
    micras = 80 # default
    area_total = (cantidad * (largo + 3)) * ancho / 1000000 # m2
    espesor_m = micras / 1000000
    radio_interno = mandril_mm / 2
    # Fórmula de Arquímedes para longitud de espiral
    longitud_mm = cantidad * (largo + 3)
    radio_final = math.sqrt((longitud_mm * micras / (1000 * math.pi)) + (radio_interno**2))
    return round(radio_final * 2, 2)

def estimar_precio_presupuesto(datos):
    base = 50.0 # Gastos de arranque
    coste_material = (datos['ancho'] * datos['largo'] / 1000000) * datos['cantidad'] * 0.15
    coste_tintas = 15.0 if datos['cantidad'] < 5000 else 45.0
    total = base + coste_material + coste_tintas
    return round(total, 2)

# =============================================================================
# SECTION 4: ENTERPRISE PDF RENDERER (Líneas 701-1100)
# =============================================================================
class FlexyEnterprisePDF(FPDF):
    def __init__(self, datos):
        super().__init__()
        self.d = datos
        self.order_id = f"FXL-{random.randint(1000,9999)}-{datetime.datetime.now().year}"

    def header(self):
        # Background Header
        self.set_fill_color(0, 35, 102)
        self.rect(0, 0, 210, 55, 'F')
        
        # Logo Text
        self.set_font("Arial", 'B', 30)
        self.set_text_color(255, 255, 255)
        self.set_xy(15, 15)
        self.cell(0, 20, "FLEXYLABEL CLOUD", ln=True)
        
        # Metadata
        self.set_font("Arial", '', 10)
        self.set_xy(140, 15)
        self.multi_cell(55, 5, f"ID: {self.order_id}\nFECHA: {datetime.date.today()}\nESTADO: PENDIENTE REVISIÓN", align='R')
        self.ln(20)

    def draw_section_title(self, title):
        self.set_font("Arial", 'B', 12)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(30, 58, 138)
        self.cell(0, 10, f"  {title.upper()}", ln=True, fill=True)
        self.ln(5)

    def generate_body(self):
        self.set_y(65)
        self.draw_section_title("1. Información del Cliente")
        self.set_font("Arial", '', 11)
        self.set_text_color(0, 0, 0)
        self.cell(100, 8, f"CLIENTE: {self.d['cliente']}")
        self.cell(0, 8, f"CONTACTO: {self.d['email']}", ln=True)
        self.cell(100, 8, f"REFERENCIA: {self.d['ref']}")
        self.cell(0, 8, f"ENTREGA: {self.d['fecha']}", ln=True)
        self.ln(10)

        self.draw_section_title("2. Especificaciones de Ingeniería")
        # Tabla detallada
        self.set_font("Arial", 'B', 10)
        self.cell(47.5, 10, "DIMENSIONES", 1, 0, 'C', True)
        self.cell(47.5, 10, "MATERIAL", 1, 0, 'C', True)
        self.cell(47.5, 10, "CANTIDAD", 1, 0, 'C', True)
        self.cell(47.5, 10, "ACABADO", 1, 1, 'C', True)

        self.set_font("Arial", '', 10)
        self.cell(47.5, 10, f"{self.d['ancho']} x {self.d['largo']} mm", 1, 0, 'C')
        self.cell(47.5, 10, self.d['material'][:20], 1, 0, 'C')
        self.cell(47.5, 10, f"{self.d['cantidad']} uds", 1, 0, 'C')
        self.cell(47.5, 10, self.d['sistema'], 1, 1, 'C')
        self.ln(10)

        self.draw_section_title("3. Parámetros de Bobinado")
        
        self.cell(95, 10, f"POSICIÓN DE SALIDA: {self.d['sentido']}", border=1)
        self.cell(95, 10, f"MANDRIL / EJE: {self.d['mandril']}", border=1, ln=True)
        self.cell(95, 10, f"SALIDA: {self.d['salida']}", border=1)
        self.cell(95, 10, f"DIÁMETRO EST. APROX: {self.d['diametro']} mm", border=1, ln=True)
        
        self.ln(10)
        self.draw_section_title("4. Observaciones de Taller")
        self.set_font("Courier", '', 10)
        self.multi_cell(0, 8, self.d['obs'], border=1)

    def footer(self):
        self.set_y(-30)
        self.set_font("Arial", 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"{COMPANY_NAME} - Documento Generado por el Módulo Cloud Engine v.{SYSTEM_VERSION}", align='C')

# =============================================================================
# SECTION 5: EMAIL DISPATCHER & AUTH (Líneas 1101-1300)
# =============================================================================
def send_secure_order(pdf_path, customer_file, payload):
    try:
        sender = st.secrets["email_usuario"]
        password = st.secrets["email_password"]
        
        message = MIMEMultipart("mixed")
        message["Subject"] = f"🔔 NUEVA ORDEN PRODUCCIÓN: {payload['cliente']} - {payload['ref']}"
        message["From"] = sender
        message["To"] = ADMIN_EMAIL
        
        html_body = f"""
        <h3>Nueva Solicitud Recibida</h3>
        <p><b>Cliente:</b> {payload['cliente']}<br>
        <b>Referencia:</b> {payload['ref']}</p>
        <hr>
        <p>Este es un envío automático desde el portal de Iván.</p>
        """
        message.attach(MIMEText(html_body, "html"))

        # Adjunto 1: Orden de Producción
        with open(pdf_path, "rb") as f:
            ext_pdf = MIMEBase("application", "pdf")
            ext_pdf.set_payload(f.read())
            encoders.encode_base64(ext_pdf)
            ext_pdf.add_header("Content-Disposition", f"attachment; filename={pdf_path}")
            message.attach(ext_pdf)

        # Adjunto 2: Arte Final
        if customer_file:
            af = MIMEBase("application", "octet-stream")
            af.set_payload(customer_file.getvalue())
            encoders.encode_base64(af)
            af.add_header("Content-Disposition", f"attachment; filename=DISEÑO_{customer_file.name}")
            message.attach(af)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(message)
        return True
    except Exception as e:
        st.error(f"Error en el Dispatcher: {str(e)}")
        return False

# =============================================================================
# SECTION 6: MAIN APPLICATION LOGIC (Líneas 1301-1500)
# =============================================================================
def main():
    apply_enterprise_styles()
    
    st.markdown('<h1 class="header-title">FLEXYLABEL CLOUD</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center; color:#64748b;">Módulo de Ingeniería Industrial v.{SYSTEM_VERSION}</p>', unsafe_allow_html=True)

    # Formulario Principal
    with st.container():
        with st.form("enterprise_form", clear_on_submit=False):
            st.subheader("📁 Identificación del Expediente")
            c1, c2, c3 = st.columns(3)
            with c1:
                cliente = st.text_input("Razón Social del Cliente", help="Nombre legal de la empresa")
                email_c = st.text_input("Correo de Contacto")
            with c2:
                referencia = st.text_input("Referencia del Trabajo", placeholder="Ej: Vino Tinto Reserva")
                fecha_e = st.date_input("Fecha de Entrega Deseada")
            with c3:
                st.warning("⚠️ Los campos con asterisco son críticos para la pre-impresión.")

            st.markdown("---")
            st.subheader("📐 Configuración Técnica del Producto")
            c4, c5, c6 = st.columns(3)
            with c4:
                ancho = st.number_input("Ancho Etiqueta (mm)", 1, 500, 100)
                largo = st.number_input("Largo Etiqueta (mm)", 1, 500, 150)
            with c5:
                cantidad = st.number_input("Volumen de Pedido", 100, 1000000, 5000, step=500)
                material = st.selectbox("Soporte Físico", list(MATERIAL_DB.keys()))
            with c6:
                sistema = st.selectbox("Tecnología de Impresión", ["Flexografía UV", "Digital High-Res", "Offset Semi-rotativo"])
                mandril = st.selectbox("Eje Interno (Mandril)", ["76mm", "40mm", "25mm"])

            st.markdown("---")
            st.subheader("🌀 Parámetros de Bobinado")
            c7, c8 = st.columns(2)
            with c7:
                sentido = st.select_slider("Posición de Salida (Sentido Bobinado)", options=[str(i) for i in range(1, 9)], value="3")
                salida_tipo = st.radio("Orientación", ["Cara Exterior (Standard)", "Cara Interior"], horizontal=True)
            with c8:
                archivo_cliente = st.file_uploader("Adjuntar Arte Final (PDF Alta Resolución)", type=["pdf"])
                
            observaciones = st.text_area("Notas Técnicas para Taller (Colores Pantone, Barnices, Troqueles...)")
            
            # Cálculo dinámico para el usuario
            diam = calcular_diametro_bobina(cantidad, ancho, largo, int(mandril[:2]))
            st.info(f"⚙️ **Info de Producción:** El diámetro estimado de las bobinas será de **{diam} mm**.")

            submit_btn = st.form_submit_button("VALIDAR Y LANZAR A PRODUCCIÓN")

            if submit_btn:
                if not cliente or not archivo_cliente or "@" not in email_c:
                    st.error("❌ ERROR: Datos de cliente inválidos o falta el archivo PDF.")
                else:
                    with st.spinner("🚀 Generando expediente técnico y notificando a taller..."):
                        datos_finales = {
                            "cliente": cliente, "email": email_c, "ref": referencia,
                            "fecha": str(fecha_e), "ancho": ancho, "largo": largo,
                            "cantidad": cantidad, "material": material, "sistema": sistema,
                            "mandril": mandril, "sentido": sentido, "salida": salida_tipo,
                            "obs": observaciones, "diametro": diam
                        }
                        
                        # Generación PDF
                        doc = FlexyEnterprisePDF(datos_finales)
                        doc.add_page()
                        doc.generate_body()
                        path = f"ORDEN_TECNICA_{cliente}.pdf".replace(" ", "_")
                        doc.output(path)
                        
                        if send_secure_order(path, archivo_cliente, datos_finales):
                            st.success("✅ ¡ORDEN LANZADA! El equipo técnico ha sido notificado.")
                            st.balloons()
                            if os.path.exists(path): os.remove(path)

if __name__ == "__main__":
    main()
