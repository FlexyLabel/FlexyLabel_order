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
import pandas as pd
import base64

# =============================================================================
# 1. CONFIGURACIÓN E INTERFAZ INDUSTRIAL (DARK MODE IVÁN)
# =============================================================================
st.set_page_config(
    page_title="FlexyLabel Enterprise v4.5 | Production System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_base64_bin(file_path):
    """Auxiliar para codificación de imágenes locales si fuera necesario"""
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_full_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');

            /* Estética de Fondo */
            .stApp {
                background: radial-gradient(circle at top right, #0f172a, #020617);
                color: #f8fafc !important;
                font-family: 'Inter', sans-serif;
            }

            /* RECUADROS DE ENTRADA: Contraste Máximo Iván */
            input, select, textarea, div[data-baseweb="input"] {
                color: #000000 !important;
                background-color: #ffffff !important;
                border-radius: 8px !important;
                font-weight: 700 !important;
                border: 2px solid #3b82f6 !important;
            }
            
            /* Etiquetas de Formulario */
            label {
                color: #94a3b8 !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-size: 0.85rem !important;
                margin-bottom: 8px !important;
            }

            /* Contenedor del Formulario Principal */
            div[data-testid="stForm"] {
                background: rgba(30, 41, 59, 0.4) !important;
                backdrop-filter: blur(15px);
                border: 1px solid rgba(59, 130, 246, 0.3) !important;
                border-radius: 24px !important;
                padding: 4rem !important;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }

            /* Botón de Envío de Gran Formato */
            .stButton button {
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
                color: #ffffff !important;
                height: 5rem !important;
                border-radius: 16px !important;
                font-weight: 800 !important;
                font-size: 1.5rem !important;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                border: none !important;
                box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            .stButton button:hover {
                transform: translateY(-2px);
                box-shadow: 0 20px 25px -5px rgba(37, 99, 235, 0.5);
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            }

            /* Métricas de Ingeniería */
            .metric-card {
                background: rgba(15, 23, 42, 0.6);
                padding: 20px;
                border-radius: 16px;
                border-left: 6px solid #3b82f6;
                margin-bottom: 20px;
            }
            .metric-value {
                color: #3b82f6;
                font-size: 1.8rem;
                font-weight: 800;
                font-family: 'JetBrains Mono', monospace;
            }
            .metric-label {
                color: #64748b;
                font-size: 0.75rem;
                text-transform: uppercase;
                font-weight: 700;
            }

            /* Separadores */
            hr {
                border: 0;
                height: 1px;
                background-image: linear-gradient(to right, rgba(59,130,246,0), rgba(59,130,246,0.75), rgba(59,130,246,0));
                margin: 40px 0;
            }

            /* Estilo para los Checkboxes de Bobinado */
            .stCheckbox label {
                background: #1e293b;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #334155;
                width: 100%;
                text-align: center;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. MOTOR DE GENERACIÓN DE PDF (FPDF ENGINE CUSTOM)
# =============================================================================
class PDF_Factory(FPDF):
    def header(self):
        # Fondo decorativo de cabecera
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 45, 'F')
        
        # Logo de texto
        self.set_xy(12, 15)
        self.set_font('Helvetica', 'B', 26)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'FLEXYLABEL PRODUCTION', ln=True)
        
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(59, 130, 246)
        self.cell(0, 5, 'SISTEMA DE GESTION DE PEDIDOS INDUSTRIALES v4.5', ln=True)
        
        self.set_xy(150, 15)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(148, 163, 184)
        ahora = datetime.datetime.now().strftime("%d/%m/%Y | %H:%M:%S")
        self.cell(50, 5, f'FECHA EMISION: {ahora}', align='R', ln=True)
        self.ln(25)

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Pagina {self.page_no()} | FlexyLabel Enterprise Solution | Documento Confidencial de Produccion', align='C')

    def add_section_header(self, label):
        self.ln(5)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(30, 41, 59)
        self.set_font('Helvetica', 'B', 11)
        self.cell(0, 10, f"  {label}", ln=True, fill=True)
        self.ln(3)

    def add_data_row(self, label1, value1, label2="", value2=""):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(71, 85, 105)
        self.cell(40, 8, f"{label1.upper()}:", 0)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(15, 23, 42)
        self.cell(55, 8, f"{value1}", 0)
        
        if label2:
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(71, 85, 105)
            self.cell(40, 8, f"{label2.upper()}:", 0)
            self.set_font('Helvetica', '', 10)
            self.set_text_color(15, 23, 42)
            self.cell(0, 8, f"{value2}", 0)
        self.ln(8)

# =============================================================================
# 3. LOGICA DE NEGOCIO Y CALCULOS DE INGENIERIA
# =============================================================================
def calcular_metricas(ancho, largo, cantidad, separacion=3):
    """Calcula metros lineales y metros cuadrados con desperdicio técnico"""
    metros_lineales = (cantidad * (largo + separacion)) / 1000
    metros_cuadrados = (ancho * largo * cantidad) / 1000000
    return round(metros_lineales, 2), round(metros_cuadrados, 2)

# =============================================================================
# 4. SISTEMA DE ENVIO DE CORREOS (CORE)
# =============================================================================
def procesar_envio_final(config_datos, file_pdf, file_af):
    try:
        smtp_user = st.secrets["email_usuario"]
        smtp_pass = st.secrets["email_password"]
        
        # 1. Configurar Mensaje para Taller
        msg_taller = MIMEMultipart()
        msg_taller['From'] = smtp_user
        msg_taller['To'] = "covet@etiquetes.com"
        msg_taller['Subject'] = f"🚀 [NUEVA ORDEN] {config_datos['cliente']} | REF: {config_datos['ref']}"
        
        cuerpo_taller = f"""
        NUEVA ORDEN DE PRODUCCION RECIBIDA
        ----------------------------------
        Cliente: {config_datos['cliente']}
        Referencia: {config_datos['ref']}
        Fecha: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
        
        Se adjunta ficha tecnica y arte final.
        """
        msg_taller.attach(MIMEText(cuerpo_taller, 'plain'))

        # 2. Adjuntar Ficha Técnica PDF
        with open(file_pdf, "rb") as f:
            adj_pdf = MIMEBase('application', 'octet-stream')
            adj_pdf.set_payload(f.read())
            encoders.encode_base64(adj_pdf)
            adj_pdf.add_header('Content-Disposition', f'attachment; filename="FICHA_{config_datos["ref"]}.pdf"')
            msg_taller.attach(adj_pdf)

        # 3. Adjuntar Arte Final
        adj_af = MIMEBase('application', 'octet-stream')
        adj_af.set_payload(file_af.getvalue())
        encoders.encode_base64(adj_af)
        adj_af.add_header('Content-Disposition', f'attachment; filename="ARTE_FINAL_{config_datos["ref"]}.pdf"')
        msg_taller.attach(adj_af)

        # 4. Enviar mediante SMTP_SSL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg_taller)
            
        return True, "Orden procesada y enviada a taller correctamente."
    except Exception as e:
        return False, f"Error en el motor de envío: {str(e)}"

# =============================================================================
# 5. CONSTRUCCION DE LA APLICACIÓN (UI/UX)
# =============================================================================
inject_full_css()

# Control de estado para bobinado
if 'pos_bobinado' not in st.session_state:
    st.session_state.pos_bobinado = "1"

st.markdown("<h1 style='text-align:center; margin-bottom:0;'>FLEXYLABEL <span style='font-weight:200;'>OPERATIONS</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#475569; margin-bottom:50px;'>Industrial Order & Production Management System v4.5</p>", unsafe_allow_html=True)

container_main = st.container()

with container_main:
    L, M, R = st.columns([0.5, 9, 0.5])
    
    with M:
        with st.form("master_form_industrial"):
            
            # --- SECCIÓN 1: IDENTIFICACIÓN ---
            st.write("### 🏢 1. IDENTIFICACIÓN DEL PROYECTO")
            col1, col2, col3 = st.columns([3, 3, 2])
            
            cliente = col1.text_input("Razón Social / Cliente", placeholder="Ej. Inditex S.A.")
            email_c = col2.text_input("Email de Seguimiento", placeholder="logistica@cliente.com")
            ref_int = col3.text_input("Referencia Interna", value=f"FXL-{datetime.date.today().year}-")
            
            # --- SECCIÓN 2: ESPECIFICACIONES TÉCNICAS ---
            st.write("### 📐 2. ESPECIFICACIONES TÉCNICAS")
            col4, col5, col6 = st.columns(3)
            
            ancho_mm = col4.number_input("Ancho Etiqueta (mm)", min_value=1, value=100)
            largo_mm = col5.number_input("Largo Etiqueta (mm)", min_value=1, value=100)
            uds_totales = col6.number_input("Cantidad Total (Uds)", min_value=1, value=5000)
            
            col7, col8, col9 = st.columns(3)
            soporte = col7.selectbox("Material / Soporte", ["PP Blanco", "PP Transparente", "Couché Brillante", "Mate", "Térmico Protegido", "Verjurado Mancha", "Metalizado"])
            mandril = col8.selectbox("Diámetro Mandril", ["Ø 76 mm", "Ø 40 mm", "Ø 25 mm"])
            uds_rollo = col9.number_input("Uds por Rollo", min_value=1, value=1000)

            # --- SECCIÓN 3: BOBINADO (IVÁN ORDER) ---
            st.markdown("<hr>", unsafe_allow_html=True)
            st.write("### ⚙️ 3. SENTIDO DE BOBINADO")
            
            # Imagen de referencia unificada
            
            st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", 
                     caption="Diagrama Técnico de Salida de Etiquetas", use_container_width=True)
            
            # Grid compacto de selección
            st.write("Selecciona la posición técnica de salida:")
            cols_bob = st.columns(8)
            for i in range(1, 9):
                with cols_bob[i-1]:
                    if st.checkbox(f"P{i}", key=f"sel_{i}"):
                        st.session_state.pos_bobinado = str(i)
            
            # Visualizador de selección actual
            st.markdown(f"""
                <div style="background: rgba(37, 99, 235, 0.2); border: 2px solid #2563eb; padding: 15px; border-radius: 12px; text-align: center; margin: 15px 0;">
                    <span style="color: #93c5fd; font-weight: 700;">SALIDA ACTIVA:</span>
                    <span style="color: #ffffff; font-size: 1.8rem; font-weight: 900; margin-left: 20px;">POSICIÓN {st.session_state.pos_bobinado}</span>
                </div>
            """, unsafe_allow_html=True)

            # --- SECCIÓN 4: LOGÍSTICA Y ACABADOS ---
            st.write("### 📂 4. DOCUMENTACIÓN Y ACABADOS")
            col10, col11 = st.columns([1, 1])
            
            with col10:
                af_upload = st.file_uploader("Adjuntar Arte Final (PDF Alta Resolución)", type=["pdf"])
                acabado = st.multiselect("Acabados Especiales", ["Barniz UV", "Laminado Brillo", "Laminado Mate", "Stamp Oro", "Relieve"])
            
            with col11:
                observaciones = st.text_area("Instrucciones Especiales para Maquinista", height=150, placeholder="Ej: Centrar bien el troquel, tensión suave en rebobinado...")

            # --- CÁLCULOS DINÁMICOS ---
            ml_calc, m2_calc = calcular_metricas(ancho_mm, largo_mm, uds_totales)
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Metros Lineales Estimados</div><div class="metric-value">{ml_calc} m</div></div>""", unsafe_allow_html=True)
            with col_m2:
                st.markdown(f"""<div class="metric-card"><div class="metric-label">Superficie Total Material</div><div class="metric-value">{m2_calc} m²</div></div>""", unsafe_allow_html=True)

            # --- BOTÓN DE LANZAMIENTO ---
            submit = st.form_submit_button("🚀 GENERAR Y LANZAR ORDEN A TALLER")

            if submit:
                if not cliente or not af_upload or not email_c:
                    st.error("❌ ERROR CRÍTICO: Debes completar el Cliente, su Email y adjuntar el diseño.")
                else:
                    with st.spinner("🛠️ Generando Documentación Técnica..."):
                        # 1. Crear el PDF
                        pdf_report = PDF_Factory()
                        pdf_report.add_page()
                        
                        pdf_report.add_section_header("DATOS DEL CLIENTE Y LOGISTICA")
                        pdf_report.add_data_row("Cliente", cliente, "Referencia", ref_int)
                        pdf_report.add_data_row("Email", email_c, "Fecha", datetime.date.today().strftime("%d/%m/%Y"))
                        
                        pdf_report.add_section_header("ESPECIFICACIONES DEL PRODUCTO")
                        pdf_report.add_data_row("Ancho", f"{ancho_mm} mm", "Largo", f"{largo_mm} mm")
                        pdf_report.add_data_row("Material", soporte, "Adhesivo", "Permanente Estándar")
                        pdf_report.add_data_row("Cantidad", f"{uds_totales} uds", "Etq/Rollo", f"{uds_rollo}")
                        
                        pdf_report.add_section_header("CONFIGURACION DE MAQUINARIA")
                        pdf_report.add_data_row("Sentido Salida", f"POSICION {st.session_state.pos_bobinado}", "Mandril", mandril)
                        pdf_report.add_data_row("Metros Lineales", f"{ml_calc} m", "M2 Totales", f"{m2_calc} m2")
                        
                        if observaciones:
                            pdf_report.add_section_header("OBSERVACIONES DE PRODUCCION")
                            pdf_report.set_font('Helvetica', '', 10)
                            pdf_report.multi_cell(0, 7, observaciones)

                        tmp_filename = f"ORDEN_{ref_int}.pdf"
                        pdf_report.output(tmp_filename)

                        # 2. Enviar por correo
                        exito, mensaje = procesar_envio_final(
                            {"cliente": cliente, "ref": ref_int, "email_c": email_c},
                            tmp_filename,
                            af_upload
                        )

                        if exito:
                            st.success(f"✅ {mensaje}")
                            st.balloons()
                            # Limpieza
                            if os.path.exists(tmp_filename):
                                os.remove(tmp_filename)
                        else:
                            st.error(mensaje)

st.markdown(f"""
    <div style="text-align: center; padding: 50px; color: #475569; font-size: 0.8rem;">
        FLEXYLABEL ENTERPRISE SYSTEM v4.5.0 | Logged as: {cliente if cliente else 'Guest'} | 
        System Status: Online | {datetime.datetime.now().year}
    </div>
""", unsafe_allow_html=True)
