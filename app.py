import streamlit as st
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime
import os
import base64
import logging
from dataclasses import dataclass

# =============================================================================
# 1. ARQUITECTURA DE DATOS
# =============================================================================
logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="FlexyLabel Terminal v6.2",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
# 2. MOTOR GRÁFICO SVG (NEÓN INDUSTRIAL)
# =============================================================================
def get_winding_svg(position_id: int) -> str:
    is_in = position_id > 4
    # Cyan para Exterior, Magenta/Rojo para Interior
    main_color = "#FF2E63" if is_in else "#08D9D6"
    
    svg = f"""
    <svg width="120" height="140" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
        <rect width="100" height="120" rx="8" fill="#1A1C24" stroke="#333" stroke-width="1"/>
        <circle cx="50" cy="50" r="30" stroke="#444" stroke-width="4" fill="none" />
        <circle cx="50" cy="50" r="8" fill="#444" />
    """
    
    arrow = ""
    if position_id in [1, 5]: arrow = f'<path d="M50 20 L50 5 M40 12 L50 5 L60 12" stroke="{main_color}" stroke-width="5" fill="none"/>'
    elif position_id in [2, 6]: arrow = f'<path d="M50 80 L50 95 M40 88 L50 95 L60 88" stroke="{main_color}" stroke-width="5" fill="none"/>'
    elif position_id in [3, 7]: arrow = f'<path d="M80 50 L95 50 M88 40 L95 50 L88 60" stroke="{main_color}" stroke-width="5" fill="none"/>'
    elif position_id in [4, 8]: arrow = f'<path d="M20 50 L5 50 M12 40 L5 50 L12 60" stroke="{main_color}" stroke-width="5" fill="none"/>'
    
    label_box = f'<rect x="30" y="42" width="40" height="16" rx="3" fill="{main_color}"/><text x="50" y="54" font-family="monospace" font-size="9" fill="black" text-anchor="middle" font-weight="bold">{"INT" if is_in else "EXT"}</text>'
    
    svg += arrow + label_box + f"""
        <text x="50" y="112" font-family="monospace" font-size="14" fill="white" text-anchor="middle" font-weight="bold">P-{position_id}</text>
    </svg>
    """
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"

# =============================================================================
# 3. CSS RADICAL "DARK FACTORY"
# =============================================================================
def inject_radical_css():
    st.markdown("""
        <style>
            .stApp { background-color: #0E1117; }
            h1, h2, h3 { color: #FFFFFF !important; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; }
            
            .industrial-card {
                background: #161B22;
                border: 1px solid #30363D;
                border-left: 6px solid #08D9D6;
                padding: 2rem;
                border-radius: 12px;
                margin-bottom: 25px;
            }

            input, select, textarea, .stNumberInput input {
                background-color: #0D1117 !important;
                border: 1px solid #30363D !important;
                color: #08D9D6 !important;
                font-family: 'JetBrains Mono', monospace !important;
            }

            .stButton > button {
                background: transparent !important;
                color: #08D9D6 !important;
                border: 2px solid #08D9D6 !important;
                height: 4rem;
                font-size: 1.2rem !important;
                font-weight: 800 !important;
                text-transform: uppercase;
                width: 100%;
                transition: 0.3s;
            }
            .stButton > button:hover {
                background: #08D9D6 !important;
                color: #000 !important;
                box-shadow: 0 0 20px rgba(8, 217, 214, 0.4);
            }

            .stat-box {
                background: #1A1C24;
                padding: 1.5rem;
                border-radius: 8px;
                border-bottom: 4px solid #08D9D6;
                text-align: center;
            }
            .stat-val { font-size: 2.2rem; color: #FFF; font-weight: 800; font-family: 'JetBrains Mono'; }
            .stat-lbl { font-size: 0.8rem; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. MOTOR PDF & EMAIL
# =============================================================================
class EnterprisePDF(FPDF):
    def header(self):
        self.set_fill_color(8, 217, 214)
        self.rect(0, 0, 210, 35, 'F')
        self.set_font('Helvetica', 'B', 18)
        self.set_text_color(0, 0, 0)
        self.set_xy(10, 12)
        self.cell(0, 10, 'ORDEN DE TRABAJO TÉCNICA | FLEXYLABEL', 0, 1, 'L')

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def add_section(self, title, data):
        self.ln(10)
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 8, f"  {title}", 0, 1, 'L', True)
        self.set_font('Helvetica', '', 10)
        for k, v in data.items():
            self.cell(50, 7, f"{k}:", 0)
            self.cell(0, 7, f"{v}", 0, 1)

class EmailService:
    @staticmethod
    def send_dual(client: ClienteDTO, prod: ProduccionDTO, pdf_path: str):
        try:
            u = st.secrets["email_usuario"]
            p = st.secrets["email_password"]
            
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # --- CORREO 1: TALLER ---
            m1 = MIMEMultipart()
            m1['From'], m1['To'] = u, "covet@etiquetes.com"
            m1['Subject'] = f"🚀 PROD: {client.razon_social} | {client.referencia_interna}"
            m1.attach(MIMEText(f"Nueva orden generada para {client.razon_social}.", 'plain'))
            
            p1 = MIMEBase('application', 'octet-stream')
            p1.set_payload(pdf_bytes); encoders.encode_base64(p1)
            p1.add_header('Content-Disposition', f'attachment; filename="OT_{client.referencia_interna}.pdf"')
            m1.attach(p1)

            if prod.arte_final:
                af = MIMEBase('application', 'octet-stream')
                af.set_payload(prod.arte_final.getvalue()); encoders.encode_base64(af)
                af.add_header('Content-Disposition', f'attachment; filename="ARTE_FINAL.pdf"')
                m1.attach(af)

            # --- CORREO 2: CLIENTE ---
            m2 = MIMEMultipart()
            m2['From'], m2['To'] = u, client.email_contacto
            m2['Subject'] = f"✅ Pedido Confirmado: {client.referencia_interna}"
            m2.attach(MIMEText(f"Hola {client.razon_social},\n\nHemos recibido su pedido. Adjuntamos ficha técnica.", 'plain'))
            m2.attach(p1) # Reutilizamos la ficha técnica

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(u, p)
                s.send_message(m1)
                s.send_message(m2)
            return True
        except Exception as e:
            st.error(f"Fallo en envío: {str(e)}")
            return False

# =============================================================================
# 5. UI PRINCIPAL
# =============================================================================
def main():
    inject_radical_css()
    if 'winding_pos' not in st.session_state: st.session_state.winding_pos = "3"

    st.markdown("<h1>🎛️ Terminal FlexyLabel v6.2</h1>", unsafe_allow_html=True)
    
    with st.form("form_v6"):
        # SECCIÓN 1
        st.markdown('<div class="industrial-card"><h3>01. REGISTRO DE CLIENTE</h3>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([3, 3, 2])
        cliente = c1.text_input("Razón Social", placeholder="Nombre Empresa")
        email = c2.text_input("Email de Confirmación")
        ref = c3.text_input("Ref. Interna", value="OT-2026-001")
        st.markdown('</div>', unsafe_allow_html=True)

        # SECCIÓN 2
        st.markdown('<div class="industrial-card"><h3>02. PARÁMETROS TÉCNICOS</h3>', unsafe_allow_html=True)
        c4, c5, c6 = st.columns(3)
        ancho = c4.number_input("Ancho (mm)", value=100)
        largo = c5.number_input("Largo (mm)", value=100)
        cantidad = c6.number_input("Cantidad Total", value=5000)
        
        c7, c8, c9 = st.columns(3)
        material = c7.selectbox("Material", ["PP Blanco", "Couché", "Térmico Eco", "Verjurado"])
        mandril = c8.selectbox("Mandril", ["Ø 76 mm", "Ø 40 mm", "Ø 25 mm"])
        u_r = c9.number_input("Uds / Rollo", value=1000)
        st.markdown('</div>', unsafe_allow_html=True)

        # SECCIÓN 3: BOBINADO
        st.markdown('<div class="industrial-card"><h3>03. ORIENTACIÓN DE SALIDA</h3>', unsafe_allow_html=True)
        cols_svg = st.columns(8)
        for i in range(1, 9):
            with cols_svg[i-1]:
                st.image(get_winding_svg(i), use_container_width=True)
                if st.checkbox(f"P{i}", value=(str(i) == st.session_state.winding_pos), key=f"pos_{i}"):
                    st.session_state.winding_pos = str(i)
        st.markdown('</div>', unsafe_allow_html=True)

        # SECCIÓN 4: ARCHIVOS
        st.markdown('<div class="industrial-card"><h3>04. DOCUMENTACIÓN</h3>', unsafe_allow_html=True)
        ca, cb = st.columns([1, 1])
        arte = ca.file_uploader("Subir Arte Final (PDF)", type="pdf")
        obs = cb.text_area("Notas para Producción")
        st.markdown('</div>', unsafe_allow_html=True)

        # MÉTRICAS HUD
        ml = round((cantidad * (largo + 3)) / 1000, 2)
        st.markdown(f"""
            <div style="display: flex; gap: 15px; margin-bottom: 25px;">
                <div class="stat-box" style="flex:1"><div class="stat-lbl">Metros Lineales</div><div class="stat-val">{ml} m</div></div>
                <div class="stat-box" style="flex:1"><div class="stat-lbl">Configuración</div><div class="stat-val">POS {st.session_state.winding_pos}</div></div>
            </div>
        """, unsafe_allow_html=True)

        submit = st.form_submit_button("🚀 EJECUTAR ORDEN DE TRABAJO")

        if submit:
            if not cliente or not arte or not email:
                st.error("❌ ERROR: Faltan campos obligatorios.")
            else:
                with st.spinner("Generando protocolos..."):
                    pdf = EnterprisePDF()
                    pdf.add_page()
                    pdf.add_section("DATOS CLIENTE", {"Empresa": cliente, "Referencia": ref, "Email": email})
                    pdf.add_section("ESPECIFICACIONES", {"Material": material, "Medidas": f"{ancho}x{largo}mm", "Cantidad": cantidad})
                    pdf.add_section("PRODUCCIÓN", {"Bobinado": f"Posición {st.session_state.winding_pos}", "Mandril": mandril, "Metraje": f"{ml} m"})
                    if obs: pdf.add_section("OBSERVACIONES", {"Notas": obs})
                    
                    pdf_path = f"OT_{ref}.pdf"
                    pdf.output(pdf_path)
                    
                    if EmailService.send_dual(ClienteDTO(cliente, email, ref), ProduccionDTO(st.session_state.winding_pos, obs, arte), pdf_path):
                        st.success(f"✅ ORDEN ENVIADA: Taller y Cliente ({email}) notificados.")
                        if os.path.exists(pdf_path): os.remove(pdf_path)

if __name__ == "__main__":
    main()
