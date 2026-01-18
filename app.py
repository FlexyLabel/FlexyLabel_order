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
import base64
import logging
from dataclasses import dataclass
from typing import List, Optional

# =============================================================================
# 1. ARQUITECTURA DEL SISTEMA Y LOGGING (CORE INDUSTRIAL)
# =============================================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("FlexyLabel_Enterprise")

st.set_page_config(
    page_title="FlexyLabel Enterprise v5.1 | Production System",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DTOs (Estructuras de Datos) ---
@dataclass
class ClienteDTO:
    razon_social: str
    email_contacto: str
    referencia_interna: str

@dataclass
class EspecificacionesDTO:
    ancho_mm: float
    largo_mm: float
    cantidad_total: int
    material: str
    mandril: str
    uds_rollo: int

@dataclass
class ProduccionDTO:
    sentido_bobinado: str
    notas_maquinista: str
    arte_final: any

# =============================================================================
# 2. MOTOR GRÁFICO VECTORIAL (SVG GENERATOR)
# =============================================================================
def get_winding_svg(position_id: int) -> str:
    """Genera gráficos SVG para bobinado sin depender de internet."""
    colors = {
        "bg": "#1e293b", "label": "#ffffff", "arrow": "#3b82f6", "text": "#94a3b8", "border": "#334155"
    }
    
    base_svg = f"""
    <svg width="100%" height="120" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="35" stroke="{colors['border']}" stroke-width="2" fill="none" />
        <circle cx="50" cy="50" r="10" stroke="{colors['border']}" stroke-width="2" fill="{colors['bg']}" />
    """

    is_in = position_id > 4
    arrow_path = ""
    label_rect = ""
    
    if position_id in [1, 5]: # TOP
        arrow_path = '<path d="M50 15 L50 5 M45 10 L50 5 L55 10" stroke="#3b82f6" stroke-width="3" fill="none"/>'
        label_rect = '<rect x="35" y="15" width="30" height="20" fill="white" stroke="#3b82f6"/>' if not is_in else ''
    elif position_id in [2, 6]: # BOTTOM
        arrow_path = '<path d="M50 85 L50 95 M45 90 L50 95 L55 90" stroke="#3b82f6" stroke-width="3" fill="none"/>'
        label_rect = '<rect x="35" y="65" width="30" height="20" fill="white" stroke="#3b82f6"/>' if not is_in else ''
    elif position_id in [3, 7]: # RIGHT
        arrow_path = '<path d="M85 50 L95 50 M90 45 L95 50 L90 55" stroke="#3b82f6" stroke-width="3" fill="none"/>'
        label_rect = '<rect x="65" y="35" width="20" height="30" fill="white" stroke="#3b82f6"/>' if not is_in else ''
    elif position_id in [4, 8]: # LEFT
        arrow_path = '<path d="M15 50 L5 50 M10 45 L5 50 L10 55" stroke="#3b82f6" stroke-width="3" fill="none"/>'
        label_rect = '<rect x="15" y="35" width="20" height="30" fill="white" stroke="#3b82f6"/>' if not is_in else ''
    
    winding_type = "INT" if is_in else "EXT"
    color_type = "#ef4444" if is_in else "#10b981"
    
    svg_content = base_svg + label_rect + arrow_path + f"""
        <text x="50" y="110" font-family="Arial" font-size="10" fill="white" text-anchor="middle" font-weight="bold">POS {position_id}</text>
        <text x="50" y="54" font-family="Arial" font-size="8" fill="{color_type}" text-anchor="middle">{winding_type}</text>
    </svg>
    """
    b64 = base64.b64encode(svg_content.encode('utf-8')).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"

# =============================================================================
# 3. ESTILOS CSS (High Contrast)
# =============================================================================
def inject_industrial_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
            .stApp {
                background-color: #0f172a;
                background-image: radial-gradient(#1e293b 1px, transparent 1px);
                background-size: 20px 20px;
                color: #f1f5f9;
                font-family: 'Inter', sans-serif;
            }
            div[data-testid="stForm"] {
                background: rgba(15, 23, 42, 0.8);
                backdrop-filter: blur(20px);
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 3rem 2rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }
            input, .stSelectbox div[data-baseweb="select"] > div, textarea {
                background-color: #ffffff !important;
                color: #000000 !important;
                font-weight: 800 !important;
                border: 2px solid #cbd5e1 !important;
                border-radius: 6px !important;
                font-size: 1rem !important;
            }
            input:focus, textarea:focus {
                border-color: #3b82f6 !important;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3) !important;
            }
            label {
                color: #94a3b8 !important;
                font-size: 0.75rem !important;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                font-weight: 700 !important;
                margin-bottom: 0.5rem !important;
            }
            .metric-container { display: flex; gap: 20px; margin-top: 20px; }
            .metric-card {
                background: #1e293b; border-left: 4px solid #3b82f6;
                padding: 15px 25px; border-radius: 8px; flex: 1;
            }
            .metric-val { font-size: 1.5rem; font-weight: 800; color: #ffffff; }
            .metric-lbl { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; }
            .stButton > button {
                background: linear-gradient(to right, #2563eb, #3b82f6);
                border: none; color: white; font-weight: 800; text-transform: uppercase;
                letter-spacing: 1px; padding: 1rem 2rem; border-radius: 8px;
                width: 100%; margin-top: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. MOTOR DE PDF
# =============================================================================
class EnterprisePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 40, 'F')
        self.set_xy(10, 10)
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'FLEXYLABEL PRODUCTION', ln=True)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(148, 163, 184)
        self.cell(0, 5, 'SISTEMA DE GESTIÓN DE ORDENES DE TRABAJO v5.1', ln=True)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(15, 23, 42)
        self.ln(5)
        self.cell(0, 10, f"  {label.upper()}", 0, 1, 'L', True)
        self.ln(2)

    def chapter_body_row(self, label, value, label2=None, value2=None):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 116, 139)
        self.cell(40, 8, f"{label}:", 0)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(15, 23, 42)
        self.cell(55, 8, f"{value}", 0)
        if label2 and value2:
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(100, 116, 139)
            self.cell(40, 8, f"{label2}:", 0)
            self.set_font('Helvetica', '', 10)
            self.set_text_color(15, 23, 42)
            self.cell(0, 8, f"{value2}", 0)
        self.ln(8)

    def add_notes(self, text):
        self.ln(5)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5, text)

# =============================================================================
# 5. SERVICIO DE CORREO (CORREGIDO: DUAL SEND)
# =============================================================================
class EmailService:
    @staticmethod
    def send_production_order(client_data: ClienteDTO, prod_data: ProduccionDTO, pdf_path: str):
        try:
            user = st.secrets["email_usuario"]
            pwd = st.secrets["email_password"]
            
            # -----------------------------------------------------------
            # CORREO 1: PARA EL TALLER (Con Arte Final + Ficha)
            # -----------------------------------------------------------
            msg_taller = MIMEMultipart()
            msg_taller['From'] = user
            msg_taller['To'] = "covet@etiquetes.com"
            msg_taller['Subject'] = f"🚀 PROD: {client_data.razon_social} | REF: {client_data.referencia_interna}"
            
            body_taller = f"""
            ORDEN DE PRODUCCIÓN
            -------------------
            Cliente: {client_data.razon_social}
            Ref: {client_data.referencia_interna}
            Fecha: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
            """
            msg_taller.attach(MIMEText(body_taller, 'plain'))

            # Adjuntar PDF Ficha al Taller
            with open(pdf_path, "rb") as f:
                pdf_data = f.read() # Leer una vez para usar en ambos
                
                part_taller = MIMEBase('application', 'octet-stream')
                part_taller.set_payload(pdf_data)
                encoders.encode_base64(part_taller)
                part_taller.add_header('Content-Disposition', f'attachment; filename="Ficha_{client_data.referencia_interna}.pdf"')
                msg_taller.attach(part_taller)

            # Adjuntar Arte Final al Taller (Solo Taller)
            if prod_data.arte_final:
                af_part = MIMEBase('application', 'octet-stream')
                af_part.set_payload(prod_data.arte_final.getvalue())
                encoders.encode_base64(af_part)
                af_part.add_header('Content-Disposition', f'attachment; filename="ARTE_{client_data.referencia_interna}.pdf"')
                msg_taller.attach(af_part)

            # -----------------------------------------------------------
            # CORREO 2: PARA EL CLIENTE (Confirmación + Ficha Técnica)
            # -----------------------------------------------------------
            msg_cliente = MIMEMultipart()
            msg_cliente['From'] = user
            msg_cliente['To'] = client_data.email_contacto
            msg_cliente['Subject'] = f"✅ Confirmación Pedido: {client_data.referencia_interna} - FlexyLabel"

            body_cliente = f"""
            Estimado cliente,

            Hemos recibido correctamente su pedido para {client_data.razon_social}.
            Adjuntamos la ficha técnica de producción para su referencia.
            
            Referencia: {client_data.referencia_interna}
            
            Atentamente,
            El equipo de FlexyLabel.
            """
            msg_cliente.attach(MIMEText(body_cliente, 'plain'))

            # Adjuntar PDF Ficha al Cliente
            part_cliente = MIMEBase('application', 'octet-stream')
            part_cliente.set_payload(pdf_data) # Reutilizamos los bytes leídos
            encoders.encode_base64(part_cliente)
            part_cliente.add_header('Content-Disposition', f'attachment; filename="Ficha_Tecnica.pdf"')
            msg_cliente.attach(part_cliente)

            # -----------------------------------------------------------
            # ENVÍO DE AMBOS CORREOS
            # -----------------------------------------------------------
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(user, pwd)
                server.send_message(msg_taller)
                server.send_message(msg_cliente)
                
            logger.info(f"Correos enviados: Taller (OK) y Cliente ({client_data.email_contacto}) (OK)")
            return True
            
        except Exception as e:
            logger.error(f"Error crítico en envío de correos: {e}")
            st.error(f"Error de conexión SMTP: {e}")
            return False

# =============================================================================
# 6. LÓGICA DE CÁLCULO
# =============================================================================
class CalculadoraProduccion:
    @staticmethod
    def calcular_consumos(specs: EspecificacionesDTO):
        gap = 3 
        ml = (specs.cantidad_total * (specs.largo_mm + gap)) / 1000
        m2 = (specs.ancho_mm * specs.largo_mm * specs.cantidad_total) / 1_000_000
        return round(ml, 2), round(m2, 2)

# =============================================================================
# 7. INTERFAZ DE USUARIO (MAIN APP)
# =============================================================================
def main():
    inject_industrial_css()
    
    if 'winding_pos' not in st.session_state:
        st.session_state.winding_pos = "3"

    st.markdown("""
        <div style="text-align: center; margin-bottom: 40px;">
            <h1 style="font-weight: 800; font-size: 3rem; margin-bottom: 0; 
            background: -webkit-linear-gradient(#60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            FLEXYLABEL ENTERPRISE</h1>
            <p style="color: #94a3b8; font-size: 1.1rem; letter-spacing: 2px;">SISTEMA INTEGRAL DE PRODUCCIÓN v5.1</p>
        </div>
    """, unsafe_allow_html=True)

    main_col_l, main_col_center, main_col_r = st.columns([1, 6, 1])

    with main_col_center:
        with st.form("production_form"):
            
            # SECCIÓN 1
            st.markdown("### 🏢 1. DATOS DEL CLIENTE")
            c1, c2, c3 = st.columns([3, 3, 2])
            cliente_input = c1.text_input("Razón Social", placeholder="Nombre de la empresa")
            email_input = c2.text_input("Email Confirmación", placeholder="contacto@cliente.com")
            ref_input = c3.text_input("Ref. Interna", value=f"ORD-{datetime.date.today().year}-001")

            st.markdown("---")

            # SECCIÓN 2
            st.markdown("### 📐 2. FICHA TÉCNICA")
            c4, c5, c6 = st.columns(3)
            ancho_val = c4.number_input("Ancho (mm)", min_value=10, value=100, step=1)
            largo_val = c5.number_input("Largo (mm)", min_value=10, value=100, step=1)
            cant_val = c6.number_input("Cantidad (Uds)", min_value=100, value=5000, step=100)

            c7, c8, c9 = st.columns(3)
            mat_val = c7.selectbox("Material", ["Polipropileno Blanco", "PP Transparente", "Couché", "Térmico Eco", "Térmico Top", "Verjurado"])
            mandril_val = c8.selectbox("Mandril", ["Ø 76 mm", "Ø 40 mm", "Ø 25 mm"])
            etq_rollo_val = c9.number_input("Uds / Rollo", min_value=100, value=1000)

            st.markdown("---")

            # SECCIÓN 3: BOBINADO SVG (SIN TOCAR)
            st.markdown("### ⚙️ 3. SENTIDO DE BOBINADO (VISUALIZACIÓN VECTORIAL)")
            st.write("Seleccione la posición técnica:")
            
            cols_svg = st.columns(8)
            for i in range(1, 9):
                with cols_svg[i-1]:
                    svg_data = get_winding_svg(i)
                    st.image(svg_data, use_container_width=True)
                    is_checked = (str(i) == st.session_state.winding_pos)
                    if st.checkbox(f"P{i}", value=is_checked, key=f"chk_{i}"):
                        st.session_state.winding_pos = str(i)
            
            st.markdown(f"""
                <div style="background: rgba(30, 58, 138, 0.6); border: 2px solid #3b82f6; border-radius: 12px; padding: 15px; text-align: center; margin-top: 15px;">
                    <span style="color: #93c5fd; font-weight: bold; font-size: 0.9rem;">CONFIGURACIÓN ACTIVA:</span>
                    <span style="color: white; font-weight: 900; font-size: 1.5rem; margin-left: 15px;">POSICIÓN {st.session_state.winding_pos}</span>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            # SECCIÓN 4
            st.markdown("### 📂 4. GESTIÓN DE ARCHIVOS")
            c10, c11 = st.columns([1, 1])
            archivo_af = c10.file_uploader("Arte Final (PDF)", type=["pdf"])
            notas_prod = c11.text_area("Observaciones Producción", height=100)

            # CÁLCULOS
            calc = CalculadoraProduccion()
            specs_obj = EspecificacionesDTO(ancho_val, largo_val, cant_val, mat_val, mandril_val, etq_rollo_val)
            ml_res, m2_res = calc.calcular_consumos(specs_obj)

            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-card"><div class="metric-lbl">Metros Lineales Estimados</div><div class="metric-val">{ml_res} ml</div></div>
                    <div class="metric-card"><div class="metric-lbl">Superficie Total</div><div class="metric-val">{m2_res} m²</div></div>
                </div>
            """, unsafe_allow_html=True)

            submit_btn = st.form_submit_button("🚀 PROCESAR ORDEN DE FABRICACIÓN")

            if submit_btn:
                if not cliente_input or not archivo_af or not email_input:
                    st.error("⚠️ VALIDACIÓN FALLIDA: Revise Cliente, Email y Arte Final.")
                else:
                    with st.spinner("🔄 Generando documentación técnica y enviando correos..."):
                        # DTOs
                        cliente_dto = ClienteDTO(cliente_input, email_input, ref_input)
                        prod_dto = ProduccionDTO(st.session_state.winding_pos, notas_prod, archivo_af)

                        # Generar PDF
                        pdf = EnterprisePDF()
                        pdf.add_page()
                        pdf.chapter_title("Datos Generales")
                        pdf.chapter_body_row("Cliente", cliente_dto.razon_social, "Referencia", cliente_dto.referencia_interna)
                        pdf.chapter_body_row("Email", cliente_dto.email_contacto, "Fecha", datetime.date.today().strftime("%d/%m/%Y"))
                        
                        pdf.chapter_title("Especificaciones de Producto")
                        pdf.chapter_body_row("Material", specs_obj.material, "Mandril", specs_obj.mandril)
                        pdf.chapter_body_row("Medidas", f"{specs_obj.ancho_mm} x {specs_obj.largo_mm} mm", "Cantidad", f"{specs_obj.cantidad_total} uds")
                        
                        pdf.chapter_title("Parámetros de Maquinaria")
                        pdf.chapter_body_row("Sentido Bobinado", f"POSICIÓN {prod_dto.sentido_bobinado}", "Etiq/Rollo", str(specs_obj.uds_rollo))
                        pdf.chapter_body_row("Consumo ML", f"{ml_res} m", "Consumo M2", f"{m2_res} m2")
                        
                        if prod_dto.notas_maquinista:
                            pdf.chapter_title("Notas de Operario")
                            pdf.add_notes(prod_dto.notas_maquinista)

                        temp_pdf_name = f"OT_{cliente_dto.referencia_interna}.pdf"
                        pdf.output(temp_pdf_name)

                        # Enviar Dual (Taller + Cliente)
                        email_service = EmailService()
                        success = email_service.send_production_order(cliente_dto, prod_dto, temp_pdf_name)

                        if success:
                            st.success(f"✅ ORDEN ENVIADA EXITOSAMENTE A TALLER Y A {cliente_dto.email_contacto}")
                            st.balloons()
                            if os.path.exists(temp_pdf_name):
                                os.remove(temp_pdf_name)

if __name__ == "__main__":
    main()
