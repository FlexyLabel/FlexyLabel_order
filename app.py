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
# 1. CONFIGURACIÓN
# =============================================================================
logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="FlexyLabel Control",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏭"
)

# =============================================================================
# 2. DEFINICIÓN DE DATOS (DTOs)
# =============================================================================
@dataclass
class ClienteDTO:
    razon_social: str
    email_contacto: str
    referencia_interna: str
    fecha_entrega: datetime.date
    tipo_documento: str

@dataclass
class EspecificacionesDTO:
    ancho_mm: float
    largo_mm: float
    cantidad_total: int
    material: str
    mandril: str
    uds_rollo: int
    formato_entrega: str

@dataclass
class ProduccionDTO:
    sentido_bobinado: str
    notas_maquinista: str
    arte_final: any

# =============================================================================
# 3. MOTOR GRÁFICO SVG (Bobinado)
# =============================================================================
def get_winding_svg(position_id: int) -> str:
    # Colores funcionales: Rojo (Interior) / Azul (Exterior)
    # Usamos colores sólidos, no neón, para mejor visibilidad
    is_interior = position_id > 4
    main_color = "#E63946" if is_interior else "#457B9D" 
    label_text = "INT" if is_interior else "EXT"
    
    svg = f"""
    <svg width="100" height="120" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
        <rect width="100" height="120" rx="5" fill="#f0f2f6" stroke="#ccc" stroke-width="1"/>
        <circle cx="50" cy="50" r="30" stroke="#333" stroke-width="3" fill="none" />
        <circle cx="50" cy="50" r="6" fill="#333" />
    """
    
    arrow_path = ""
    if position_id in [1, 5]: arrow_path = f'<path d="M50 20 L50 5 M40 12 L50 5 L60 12" stroke="{main_color}" stroke-width="4" fill="none"/>'
    elif position_id in [2, 6]: arrow_path = f'<path d="M50 80 L50 95 M40 88 L50 95 L60 88" stroke="{main_color}" stroke-width="4" fill="none"/>'
    elif position_id in [3, 7]: arrow_path = f'<path d="M80 50 L95 50 M88 40 L95 50 L88 60" stroke="{main_color}" stroke-width="4" fill="none"/>'
    elif position_id in [4, 8]: arrow_path = f'<path d="M20 50 L5 50 M12 40 L5 50 L12 60" stroke="{main_color}" stroke-width="4" fill="none"/>'
    
    label_box = f'''
        <rect x="30" y="42" width="40" height="16" rx="2" fill="{main_color}"/>
        <text x="50" y="54" font-family="Arial" font-size="9" fill="white" text-anchor="middle" font-weight="bold">{label_text}</text>
    '''
    
    svg += arrow_path + label_box + f"""
        <text x="50" y="110" font-family="Arial" font-size="12" fill="#333" text-anchor="middle" font-weight="bold">Pos {position_id}</text>
    </svg>
    """
    b64_code = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64_code}"

# =============================================================================
# 4. ESTILOS CSS (CLEAN PRO)
# =============================================================================
def inject_clean_css():
    st.markdown("""
        <style>
            /* Reset básico para legibilidad */
            .stApp {
                background-color: #F8F9FA; /* Fondo claro profesional o deja el default del usuario */
            }
            
            h1, h2, h3 {
                color: #1F2937 !important;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            /* Tarjetas contenedoras limpias */
            .clean-card {
                background-color: #FFFFFF;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #E5E7EB;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            
            .clean-card h3 {
                margin-top: 0;
                font-size: 1.1rem;
                border-bottom: 2px solid #3B82F6;
                padding-bottom: 10px;
                margin-bottom: 20px;
                color: #3B82F6 !important;
            }

            /* Inputs */
            .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox {
                color: #111827 !important;
            }

            /* Botón Principal */
            .stButton > button {
                background-color: #2563EB !important;
                color: white !important;
                border: none !important;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                border-radius: 8px;
                width: 100%;
                font-weight: bold;
                transition: background 0.3s;
            }
            .stButton > button:hover {
                background-color: #1D4ED8 !important;
            }

            /* Métricas HUD */
            .metric-box {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            }
            .metric-value {
                font-size: 1.8rem;
                font-weight: bold;
                color: #1F2937;
                font-family: 'Consolas', monospace; /* Solo números en monospace */
            }
            .metric-label {
                font-size: 0.85rem;
                color: #6B7280;
                text-transform: uppercase;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 5. GENERADOR PDF
# =============================================================================
class EnterprisePDF(FPDF):
    def __init__(self, doc_type="ORDEN DE TRABAJO"):
        super().__init__()
        self.doc_type_title = doc_type
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Cabecera Azul Corporativo
        self.set_fill_color(37, 99, 235) # Azul
        self.rect(0, 0, 210, 35, 'F')
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 12)
        self.cell(0, 10, f'{self.doc_type_title} | FLEXYLABEL', 0, 1, 'L')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def add_section(self, title, data_dict):
        self.ln(8)
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(240, 242, 245)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f"  {title}", 0, 1, 'L', True)
        self.set_font('Arial', '', 10)
        self.ln(2)
        for key, value in data_dict.items():
            self.cell(50, 7, f"{key}:", 0)
            self.cell(0, 7, f"{value}", 0, 1)

# =============================================================================
# 6. SERVICIO EMAIL (CATALÁN/ESPAÑOL)
# =============================================================================
class EmailService:
    @staticmethod
    def send_dual(client: ClienteDTO, specs: EspecificacionesDTO, prod: ProduccionDTO, pdf_path: str):
        try:
            user = st.secrets["email_usuario"]
            pwd = st.secrets["email_password"]
            
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # --- EMAIL 1: TALLER (CATALÀ) ---
            tipo_cat = "COMANDA" if client.tipo_documento == "Pedido" else "PRESSUPOST"
            formato_cat = "Bobina" if specs.formato_entrega == "Bobina" else "Fulls/Pla"
            
            m1 = MIMEMultipart()
            m1['From'] = user
            m1['To'] = "covet@etiquetes.com"
            m1['Subject'] = f"🏭 [NOVA {tipo_cat}] - {client.razon_social}"
            
            body_cat = f"""
            Bon dia,

            Nou registre al sistema FlexyLabel.
            
            - Client: {client.razon_social}
            - Data Entrega: {client.fecha_entrega.strftime('%d/%m/%Y')}
            - Material: {specs.material}
            - Format: {formato_cat}
            
            S'adjunta PDF i Art Final.
            """
            m1.attach(MIMEText(body_cat, 'plain'))
            
            att1 = MIMEBase('application', 'octet-stream')
            att1.set_payload(pdf_bytes)
            encoders.encode_base64(att1)
            att1.add_header('Content-Disposition', f'attachment; filename="{client.referencia_interna}.pdf"')
            m1.attach(att1)

            if prod.arte_final:
                af = MIMEBase('application', 'octet-stream')
                af.set_payload(prod.arte_final.getvalue())
                encoders.encode_base64(af)
                af.add_header('Content-Disposition', 'attachment; filename="ARTE_FINAL.pdf"')
                m1.attach(af)

            # --- EMAIL 2: CLIENTE (ESPAÑOL) ---
            m2 = MIMEMultipart()
            m2['From'] = user
            m2['To'] = client.email_contacto
            m2['Subject'] = f"✅ Documentación: {client.referencia_interna}"
            
            body_esp = f"""
            Estimado cliente,

            Adjuntamos la documentación relativa a su {client.tipo_documento.lower()}.
            Fecha de entrega prevista: {client.fecha_entrega.strftime('%d/%m/%Y')}
            
            Saludos cordiales,
            FlexyLabel.
            """
            m2.attach(MIMEText(body_esp, 'plain'))
            
            att2 = MIMEBase('application', 'octet-stream')
            att2.set_payload(pdf_bytes)
            encoders.encode_base64(att2)
            att2.add_header('Content-Disposition', f'attachment; filename="{client.referencia_interna}.pdf"')
            m2.attach(att2)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(user, pwd)
                s.send_message(m1)
                s.send_message(m2)
            return True
        except Exception as e:
            st.error(f"Error envío: {e}")
            return False

# =============================================================================
# 7. UI PRINCIPAL
# =============================================================================
def main():
    inject_clean_css()
    
    if 'winding_pos' not in st.session_state: st.session_state.winding_pos = "3"

    st.title("🎛️ FlexyLabel Control")
    
    with st.form("main_form"):
        
        # Selector de Modo
        st.write("### 📂 Tipo de Operación")
        tipo_doc = st.radio("", ["Pedido", "Presupuesto"], horizontal=True, label_visibility="collapsed")
        
        # BLOQUE 1: DATOS
        st.markdown('<div class="clean-card"><h3>1. Datos del Cliente</h3>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Razón Social")
        email = c2.text_input("Email Cliente")
        c3, c4 = st.columns(2)
        ref = c3.text_input("Referencia Interna", value="REF-2026")
        fecha_entrega = c4.date_input("Fecha Entrega", datetime.date.today() + datetime.timedelta(days=7))
        st.markdown('</div>', unsafe_allow_html=True)

        # BLOQUE 2: TÉCNICA
        st.markdown('<div class="clean-card"><h3>2. Especificaciones</h3>', unsafe_allow_html=True)
        col_f, col_m, col_c = st.columns(3)
        formato = col_f.selectbox("Formato", ["Bobina", "Hojas (Plano)"])
        material = col_m.selectbox("Material", ["PP Blanco", "Couché", "Térmico Eco", "Verjurado"])
        cantidad = col_c.number_input("Cantidad", value=5000, step=100)

        col_w, col_h, col_ex = st.columns(3)
        ancho = col_w.number_input("Ancho (mm)", value=100)
        largo = col_h.number_input("Largo (mm)", value=100)
        
        if formato == "Bobina":
            mandril = col_ex.selectbox("Mandril", ["76 mm", "40 mm", "25 mm"])
            u_r = st.number_input("Etiquetas/Rollo", value=1000)
        else:
            mandril = "N/A"
            col_ex.info("Modo Hojas activado")
            u_r = 0
        st.markdown('</div>', unsafe_allow_html=True)

        # BLOQUE 3: BOBINADO (Solo si aplica visualmente)
        st.markdown(f'<div class="clean-card"><h3>3. Sentido de Salida {"(Bobina)" if formato == "Bobina" else "(N/A)"}</h3>', unsafe_allow_html=True)
        cols = st.columns(8)
        for i in range(1, 9):
            with cols[i-1]:
                # Usar una imagen limpia
                st.image(get_winding_svg(i), use_container_width=True)
                # Deshabilitar si es hoja
                disabled = (formato == "Hojas (Plano)")
                if st.checkbox(f"Pos {i}", value=(str(i)==st.session_state.winding_pos), key=f"p{i}", disabled=disabled):
                    st.session_state.winding_pos = str(i)
        st.markdown('</div>', unsafe_allow_html=True)

        # BLOQUE 4: ARCHIVOS
        st.markdown('<div class="clean-card"><h3>4. Archivos</h3>', unsafe_allow_html=True)
        ca, cb = st.columns(2)
        arte = ca.file_uploader("Arte Final (PDF)", type="pdf")
        obs = cb.text_area("Observaciones")
        st.markdown('</div>', unsafe_allow_html=True)

        # HUD / Resumen
        ml = round((cantidad * (largo + 3)) / 1000, 2)
        st.markdown(f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div class="metric-box">
                    <div class="metric-label">Metros Totales</div>
                    <div class="metric-value">{ml} m</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Entrega</div>
                    <div class="metric-value">{fecha_entrega.strftime('%d/%m')}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Documento</div>
                    <div class="metric-value">{tipo_doc.upper()}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if st.form_submit_button(f"Generar {tipo_doc}"):
            if not cliente or not email:
                st.error("Faltan datos obligatorios.")
            else:
                with st.spinner("Procesando..."):
                    client_dto = ClienteDTO(cliente, email, ref, fecha_entrega, tipo_doc)
                    specs_dto = EspecificacionesDTO(ancho, largo, cantidad, material, mandril, u_r, formato)
                    prod_dto = ProduccionDTO(st.session_state.winding_pos, obs, arte)
                    
                    pdf = EnterprisePDF(doc_type=tipo_doc.upper())
                    pdf.add_page()
                    pdf.add_section("CLIENTE", {"Nombre": cliente, "Ref": ref, "Email": email})
                    pdf.add_section("DETALLES", {"Material": material, "Medidas": f"{ancho}x{largo}", "Cant": cantidad, "Formato": formato})
                    pdf_path = f"temp_{ref}.pdf"
                    pdf.output(pdf_path)
                    
                    if EmailService.send_dual(client_dto, specs_dto, prod_dto, pdf_path):
                        st.success(f"Proceso completado. Correo enviado a {email} y a Taller.")
                        if os.path.exists(pdf_path): os.remove(pdf_path)

if __name__ == "__main__":
    main()
