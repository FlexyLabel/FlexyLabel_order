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

# =============================================================================
# 1. CONFIGURACIÓN ESTRUCTURAL (CORE)
# =============================================================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("FlexyLabel_Enterprise")

st.set_page_config(
    page_title="FlexyLabel Enterprise | V6.0 UI",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DTOs (Data Transfer Objects) ---
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
# 2. MOTOR GRÁFICO VECTORIAL (SVG GENERATOR - REFINADO)
# =============================================================================
def get_winding_svg(position_id: int) -> str:
    """Genera gráficos SVG técnicos con estética mejorada."""
    colors = {
        "bg": "#0f172a", "label": "#f8fafc", "arrow": "#0ea5e9", "text": "#94a3b8", "border": "#334155"
    }
    
    # Base más limpia
    base_svg = f"""
    <svg width="100%" height="130" viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>
        <circle cx="50" cy="50" r="35" stroke="{colors['border']}" stroke-width="2" fill="#1e293b" />
        <circle cx="50" cy="50" r="10" stroke="{colors['border']}" stroke-width="2" fill="{colors['bg']}" />
    """

    is_in = position_id > 4
    arrow_path = ""
    label_rect = ""
    
    # Lógica de dibujo
    if position_id in [1, 5]: # TOP
        arrow_path = f'<path d="M50 15 L50 5 M45 10 L50 5 L55 10" stroke="{colors["arrow"]}" stroke-width="3" fill="none" filter="url(#glow)"/>'
        label_rect = f'<rect x="35" y="15" width="30" height="20" fill="white" stroke="{colors["arrow"]}"/>' if not is_in else ''
    elif position_id in [2, 6]: # BOTTOM
        arrow_path = f'<path d="M50 85 L50 95 M45 90 L50 95 L55 90" stroke="{colors["arrow"]}" stroke-width="3" fill="none" filter="url(#glow)"/>'
        label_rect = f'<rect x="35" y="65" width="30" height="20" fill="white" stroke="{colors["arrow"]}"/>' if not is_in else ''
    elif position_id in [3, 7]: # RIGHT
        arrow_path = f'<path d="M85 50 L95 50 M90 45 L95 50 L90 55" stroke="{colors["arrow"]}" stroke-width="3" fill="none" filter="url(#glow)"/>'
        label_rect = f'<rect x="65" y="35" width="20" height="30" fill="white" stroke="{colors["arrow"]}"/>' if not is_in else ''
    elif position_id in [4, 8]: # LEFT
        arrow_path = f'<path d="M15 50 L5 50 M10 45 L5 50 L10 55" stroke="{colors["arrow"]}" stroke-width="3" fill="none" filter="url(#glow)"/>'
        label_rect = f'<rect x="15" y="35" width="20" height="30" fill="white" stroke="{colors["arrow"]}"/>' if not is_in else ''
    
    winding_type = "INTERIOR" if is_in else "EXTERIOR"
    color_type = "#f43f5e" if is_in else "#10b981"
    
    svg_content = base_svg + label_rect + arrow_path + f"""
        <rect x="20" y="105" width="60" height="20" rx="4" fill="#0f172a" stroke="{colors['border']}" />
        <text x="50" y="119" font-family="sans-serif" font-size="10" fill="white" text-anchor="middle" font-weight="bold">POS {position_id}</text>
        <text x="50" y="54" font-family="sans-serif" font-size="7" fill="{color_type}" text-anchor="middle" font-weight="bold">{winding_type}</text>
    </svg>
    """
    b64 = base64.b64encode(svg_content.encode('utf-8')).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"

# =============================================================================
# 3. ESTILOS CSS "DYNAMIC INDUSTRIAL" (V6.0)
# =============================================================================
def inject_dynamic_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=JetBrains+Mono:wght@500;800&display=swap');

            /* FONDO & BASE */
            .stApp {
                background-color: #0b1121;
                background-image: 
                    radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.1) 0px, transparent 50%),
                    radial-gradient(at 100% 100%, rgba(236, 72, 153, 0.05) 0px, transparent 50%);
                font-family: 'Inter', sans-serif;
            }

            /* ENCABEZADOS DE SECCIÓN */
            .section-header {
                display: flex;
                align-items: center;
                margin-top: 2rem;
                margin-bottom: 1rem;
                border-bottom: 1px solid rgba(148, 163, 184, 0.2);
                padding-bottom: 0.5rem;
            }
            .section-number {
                background: linear-gradient(135deg, #0ea5e9, #2563eb);
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                margin-right: 12px;
                font-family: 'JetBrains Mono', monospace;
                box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
            }
            .section-title {
                font-size: 1.1rem;
                font-weight: 700;
                color: #e2e8f0;
                letter-spacing: 0.05em;
            }

            /* CONTENEDOR PRINCIPAL "GLASS" */
            div[data-testid="stForm"] {
                background: rgba(30, 41, 59, 0.4);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
                padding: 3rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }

            /* INPUTS DINÁMICOS */
            input, select, textarea, div[data-baseweb="select"] > div {
                background-color: rgba(15, 23, 42, 0.6) !important;
                color: #f8fafc !important;
                border: 1px solid #334155 !important;
                border-radius: 8px !important;
                transition: all 0.3s ease !important;
            }
            input:focus, textarea:focus, div[data-baseweb="select"] > div:focus-within {
                border-color: #38bdf8 !important;
                box-shadow: 0 0 15px rgba(56, 189, 248, 0.2) !important;
                background-color: rgba(15, 23, 42, 0.9) !important;
            }
            
            /* LABELS */
            label {
                color: #94a3b8 !important;
                font-size: 0.8rem !important;
                font-weight: 600 !important;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            /* TARJETAS DE MÉTRICAS (HUD STYLE) */
            .hud-container {
                display: flex;
                gap: 20px;
                margin-top: 25px;
            }
            .hud-card {
                flex: 1;
                background: linear-gradient(180deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%);
                border: 1px solid #334155;
                border-top: 3px solid #0ea5e9;
                border-radius: 12px;
                padding: 20px;
                position: relative;
                overflow: hidden;
            }
            .hud-card::before {
                content: "";
                position: absolute;
                top: 0; left: 0; right: 0; height: 1px;
                background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.5), transparent);
            }
            .hud-value {
                font-family: 'JetBrains Mono', monospace;
                font-size: 1.8rem;
                font-weight: 700;
                color: #38bdf8;
                text-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
            }
            .hud-label {
                font-size: 0.75rem;
                color: #64748b;
                text-transform: uppercase;
                margin-bottom: 5px;
            }

            /* BOTÓN DE ACCIÓN */
            .stButton > button {
                background: linear-gradient(90deg, #0284c7, #2563eb);
                color: white;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                padding: 1.2rem;
                border-radius: 10px;
                border: none;
                width: 100%;
                margin-top: 2rem;
                box-shadow: 0 10px 20px -5px rgba(37, 99, 235, 0.4);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 15px 30px -5px rgba(37, 99, 235, 0.6);
                background: linear-gradient(90deg, #0ea5e9, #3b82f6);
            }
            
            /* Checkbox bobinado personalizado */
            .stCheckbox label {
                color: #cbd5e1 !important;
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
        self.rect(0, 0, 210, 45, 'F')
        self.set_xy(10, 12)
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'FLEXYLABEL PRODUCTION', ln=True)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(56, 189, 248) # Cyan Accent
        self.cell(0, 5, 'SISTEMA DE GESTIÓN DE ORDENES DE TRABAJO v6.0', ln=True)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()} | Generado por FlexyLabel Enterprise', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(15, 23, 42)
        self.ln(5)
        self.cell(0, 10, f"  {label.upper()}", 0, 1, 'L', True)
        self.ln(2)

    def chapter_body_row(self, label, value, label2=None, value2=None):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(71, 85, 105)
        self.cell(40, 8, f"{label}:", 0)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(15, 23, 42)
        self.cell(55, 8, f"{value}", 0)
        if label2 and value2:
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(71, 85, 105)
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
# 5. SERVICIO DE CORREO (DUAL SEND - FIXED)
# =============================================================================
class EmailService:
    @staticmethod
    def send_production_order(client_data: ClienteDTO, prod_data: ProduccionDTO, pdf_path: str):
        try:
            user = st.secrets["email_usuario"]
            pwd = st.secrets["email_password"]
            
            # --- 1. EMAIL TALLER ---
            msg_taller = MIMEMultipart()
            msg_taller['From'] = user
            msg_taller['To'] = "covet@etiquetes.com"
            msg_taller['Subject'] = f"🏭 [PROD] {client_data.razon_social} | REF: {client_data.referencia_interna}"
            
            msg_taller.attach(MIMEText(f"Nueva orden generada.\nCliente: {client_data.razon_social}\nRef: {client_data.referencia_interna}", 'plain'))

            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
                
                # Adjunto Ficha Taller
                part_taller = MIMEBase('application', 'octet-stream')
                part_taller.set_payload(pdf_data)
                encoders.encode_base64(part_taller)
                part_taller.add_header('Content-Disposition', f'attachment; filename="Ficha_{client_data.referencia_interna}.pdf"')
                msg_taller.attach(part_taller)

            # Adjunto Arte Final Taller
            if prod_data.arte_final:
                af_part = MIMEBase('application', 'octet-stream')
                af_part.set_payload(prod_data.arte_final.getvalue())
                encoders.encode_base64(af_part)
                af_part.add_header('Content-Disposition', f'attachment; filename="ARTE_FINAL.pdf"')
                msg_taller.attach(af_part)

            # --- 2. EMAIL CLIENTE ---
            msg_cliente = MIMEMultipart()
            msg_cliente['From'] = user
            msg_cliente['To'] = client_data.email_contacto
            msg_cliente['Subject'] = f"✅ Pedido Recibido: {client_data.referencia_interna} - FlexyLabel"

            msg_cliente.attach(MIMEText(f"Hola,\n\nSu pedido para {client_data.razon_social} está en marcha.\nAdjuntamos ficha técnica.", 'plain'))

            # Adjunto Ficha Cliente
            part_cliente = MIMEBase('application', 'octet-stream')
            part_cliente.set_payload(pdf_data)
            encoders.encode_base64(part_cliente)
            part_cliente.add_header('Content-Disposition', f'attachment; filename="Ficha_Tecnica.pdf"')
            msg_cliente.attach(part_cliente)

            # --- ENVÍO ---
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(user, pwd)
                server.send_message(msg_taller)
                server.send_message(msg_cliente)
                
            return True
        except Exception as e:
            logger.error(f"Error SMTP: {e}")
            st.error(f"Error SMTP: {e}")
            return False

# =============================================================================
# 6. LÓGICA DE NEGOCIO
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
    inject_dynamic_css()
    
    if 'winding_pos' not in st.session_state:
        st.session_state.winding_pos = "3"

    # Encabezado Minimalista
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding: 0 20px;">
            <div>
                <h1 style="font-weight: 800; font-size: 2.5rem; margin:0; background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">FLEXYLABEL</h1>
                <p style="color: #94a3b8; margin:0; font-family:'JetBrains Mono'; font-size: 0.9rem;">PRODUCTION CONTROL UNIT v6.0</p>
            </div>
            <div style="text-align:right;">
                <span style="background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; border: 1px solid rgba(52, 211, 153, 0.3);">SYSTEM ONLINE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    c_main = st.container()

    with c_main:
        with st.form("production_form"):
            
            # SECCIÓN 1
            st.markdown('<div class="section-header"><div class="section-number">1</div><div class="section-title">DATOS CLIENTE</div></div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([3, 3, 2])
            cliente_input = c1.text_input("Razón Social", placeholder="Empresa S.L.")
            email_input = c2.text_input("Email Contacto", placeholder="nombre@dominio.com")
            ref_input = c3.text_input("Ref. Pedido", value=f"ORD-{datetime.date.today().year}-X")

            # SECCIÓN 2
            st.markdown('<div class="section-header"><div class="section-number">2</div><div class="section-title">ESPECIFICACIONES</div></div>', unsafe_allow_html=True)
            c4, c5, c6 = st.columns(3)
            ancho_val = c4.number_input("Ancho (mm)", min_value=10, value=100)
            largo_val = c5.number_input("Largo (mm)", min_value=10, value=100)
            cant_val = c6.number_input("Total (Uds)", min_value=100, value=5000, step=100)

            c7, c8, c9 = st.columns(3)
            mat_val = c7.selectbox("Material", ["PP Blanco", "PP Transparente", "Couché", "Térmico Eco", "Térmico Top", "Verjurado Cream"])
            mandril_val = c8.selectbox("Mandril", ["Ø 76 mm", "Ø 40 mm", "Ø 25 mm"])
            etq_rollo_val = c9.number_input("Uds / Rollo", min_value=100, value=1000)

            # SECCIÓN 3: BOBINADO (VISUAL)
            st.markdown('<div class="section-header"><div class="section-number">3</div><div class="section-title">SENTIDO DE SALIDA</div></div>', unsafe_allow_html=True)
            
            # Contenedor con borde sutil para agrupar visualmente el bobinado
            st.markdown('<div style="background: rgba(0,0,0,0.2); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">', unsafe_allow_html=True)
            cols_svg = st.columns(8)
            for i in range(1, 9):
                with cols_svg[i-1]:
                    svg_data = get_winding_svg(i)
                    st.image(svg_data, use_container_width=True)
                    # Custom selection logic
                    is_active = (str(i) == st.session_state.winding_pos)
                    if st.checkbox(f"P{i}", value=is_active, key=f"chk_{i}"):
                        st.session_state.winding_pos = str(i)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Feedback visual
            st.markdown(f"""
                <div style="margin-top: 15px; display: flex; align-items: center; justify-content: center; gap: 10px;">
                    <span style="color: #94a3b8; font-size: 0.9rem;">CONFIGURACIÓN ACTIVA:</span>
                    <span style="color: #38bdf8; font-family: 'JetBrains Mono'; font-weight: 800; font-size: 1.2rem;">POSICIÓN {st.session_state.winding_pos}</span>
                </div>
            """, unsafe_allow_html=True)

            # SECCIÓN 4
            st.markdown('<div class="section-header"><div class="section-number">4</div><div class="section-title">ARCHIVOS</div></div>', unsafe_allow_html=True)
            c10, c11 = st.columns([1, 1])
            archivo_af = c10.file_uploader("Subir Arte Final (PDF)", type=["pdf"])
            notas_prod = c11.text_area("Notas Técnicas", height=100, placeholder="Instrucciones para operador...")

            # HUD DE MÉTRICAS
            calc = CalculadoraProduccion()
            specs_obj = EspecificacionesDTO(ancho_val, largo_val, cant_val, mat_val, mandril_val, etq_rollo_val)
            ml_res, m2_res = calc.calcular_consumos(specs_obj)

            st.markdown(f"""
                <div class="hud-container">
                    <div class="hud-card">
                        <div class="hud-label">METROS LINEALES</div>
                        <div class="hud-value">{ml_res} m</div>
                    </div>
                    <div class="hud-card">
                        <div class="hud-label">SUPERFICIE TOTAL</div>
                        <div class="hud-value">{m2_res} m²</div>
                    </div>
                    <div class="hud-card" style="border-top-color: #818cf8;">
                        <div class="hud-label">ESTADO BOBINA</div>
                        <div class="hud-value" style="color: #818cf8;">P-{st.session_state.winding_pos}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            submit_btn = st.form_submit_button("🚀 INICIAR ORDEN DE PRODUCCIÓN")

            if submit_btn:
                if not cliente_input or not archivo_af or not email_input:
                    st.error("⚠️ FALTAN DATOS CRÍTICOS: Revise Cliente, Email y Archivo.")
                else:
                    with st.spinner("⏳ PROCESANDO ORDEN..."):
                        # DTOs
                        cliente_dto = ClienteDTO(cliente_input, email_input, ref_input)
                        prod_dto = ProduccionDTO(st.session_state.winding_pos, notas_prod, archivo_af)

                        # Generar PDF
                        pdf = EnterprisePDF()
                        pdf.add_page()
                        pdf.chapter_title("Datos Generales")
                        pdf.chapter_body_row("Cliente", cliente_dto.razon_social, "Ref", cliente_dto.referencia_interna)
                        pdf.chapter_body_row("Email", cliente_dto.email_contacto, "Fecha", datetime.date.today().strftime("%d/%m/%Y"))
                        
                        pdf.chapter_title("Especificaciones")
                        pdf.chapter_body_row("Material", specs_obj.material, "Mandril", specs_obj.mandril)
                        pdf.chapter_body_row("Medidas", f"{specs_obj.ancho_mm} x {specs_obj.largo_mm} mm", "Cantidad", f"{specs_obj.cantidad_total}")
                        
                        pdf.chapter_title("Configuración")
                        pdf.chapter_body_row("Bobinado", f"POSICIÓN {prod_dto.sentido_bobinado}", "Uds/Rollo", str(specs_obj.uds_rollo))
                        pdf.chapter_body_row("Metraje", f"{ml_res} m", "Área", f"{m2_res} m2")
                        
                        if prod_dto.notas_maquinista:
                            pdf.chapter_title("Notas")
                            pdf.add_notes(prod_dto.notas_maquinista)

                        temp_pdf_name = f"OT_{cliente_dto.referencia_interna}.pdf"
                        pdf.output(temp_pdf_name)

                        # Enviar (Sin globos, con mensaje profesional)
                        email_service = EmailService()
                        if email_service.send_production_order(cliente_dto, prod_dto, temp_pdf_name):
                            st.success(f"✅ ORDEN PROCESADA CORRECTAMENTE. Notificación enviada a Taller y Cliente.", icon="✅")
                            if os.path.exists(temp_pdf_name):
                                os.remove(temp_pdf_name)

if __name__ == "__main__":
    main()
