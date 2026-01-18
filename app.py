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
import uuid
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# =============================================================================
# 1. CONFIGURACIÓN DE NÚCLEO Y LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("production.log"), logging.StreamHandler()]
)
logger = logging.getLogger("FlexyLabel_Enterprise")

# Configuración de página
st.set_page_config(
    page_title="FlexyLabel Enterprise | Order Management System",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# 2. MODELOS DE DATOS (DTOs)
# =============================================================================

@dataclass
class ClienteDTO:
    razon_social: str
    cif: str
    email_contacto: str
    telefono: str
    direccion: str
    referencia_interna: str

@dataclass
class EspecificacionesDTO:
    ancho_mm: float
    largo_mm: float
    gap_mm: float = 3.0
    cantidad_total: int = 0
    material: str = ""
    acabado: str = "Ninguno"
    formato: str = "Bobina"  # Bobina o Hojas
    mandril: str = "Ø 76 mm"
    uds_rollo: int = 1000

@dataclass
class ProduccionDTO:
    tipo_bobinado: str  # Interior / Exterior
    posicion_salida: str # 1, 2, 3, 4 o 1A, 2A, 3A, 4A
    notas_maquinista: str
    fecha_entrega_deseada: datetime.date
    arte_final: Any = None
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())

# =============================================================================
# 3. CONSTANTES Y DICCIONARIOS DE CONFIGURACIÓN
# =============================================================================

MATERIALES_CATALOGO = {
    "PAPELES": [
        "Couché Brillo Adhesivo", "Couché Mate Adhesivo", "Papel Kraft Natural",
        "Verjurado Cream (Vino)", "Verjurado Blanco Extra", "Estructural Anti-grasa"
    ],
    "PLÁSTICOS (PP/PE)": [
        "PP Blanco Brillo", "PP Blanco Mate", "PP Transparente", "PP Metalizado Plata",
        "PP Metalizado Oro", "PE Blanco (Flexible)"
    ],
    "TÉRMICOS": [
        "Térmico Eco (Sin protección)", "Térmico Top (Protección total)", "Térmico Color"
    ],
    "ESPECIALES": [
        "Papel Flúor Amarillo", "Papel Flúor Naranja", "Papel Flúor Verde",
        "Papel Flúor Rosa", "Papel Holográfico Premium", "Papel Seguridad (Void)"
    ]
}

MANDRILES_DISPONIBLES = ["Ø 76 mm", "Ø 40 mm", "Ø 25 mm", "Ø 19 mm", "Sin Mandril"]

# =============================================================================
# 4. MOTOR ESTÉTICO (CSS CUSTOM)
# =============================================================================

def inject_enterprise_styles():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');

            :root {
                --primary: #0ea5e9;
                --secondary: #6366f1;
                --bg-dark: #0f172a;
                --card-bg: rgba(30, 41, 59, 0.7);
            }

            .stApp {
                background-color: var(--bg-dark);
                font-family: 'Plus Jakarta Sans', sans-serif;
            }

            /* Contenedores */
            .main-container {
                padding: 2rem;
                max-width: 1200px;
                margin: auto;
            }

            .glass-card {
                background: var(--card-bg);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 2.5rem;
                margin-bottom: 2rem;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
            }

            /* Títulos */
            .title-gradient {
                background: linear-gradient(90deg, #38bdf8, #818cf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
                font-size: 3rem;
                margin-bottom: 0.5rem;
            }

            .section-header {
                display: flex;
                align-items: center;
                gap: 15px;
                margin: 2rem 0 1.5rem 0;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid rgba(56, 189, 248, 0.3);
            }

            .badge-number {
                background: var(--primary);
                color: white;
                width: 35px;
                height: 35px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-family: 'JetBrains Mono';
            }

            /* Inputs */
            div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
                border-radius: 10px !important;
                background-color: rgba(15, 23, 42, 0.8) !important;
            }

            /* Botones */
            .stButton > button {
                background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                color: white !important;
                border: none !important;
                padding: 1rem 2rem !important;
                font-weight: 700 !important;
                border-radius: 12px !important;
                transition: all 0.3s ease !important;
                text-transform: uppercase;
                letter-spacing: 1px;
                width: 100%;
            }

            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(37, 99, 235, 0.4);
            }

            /* HUD Metrics */
            .metric-box {
                background: rgba(15, 23, 42, 0.5);
                border-left: 4px solid var(--primary);
                padding: 15px;
                border-radius: 8px;
            }
            
            .metric-label { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; }
            .metric-value { font-family: 'JetBrains Mono'; font-size: 1.4rem; color: #f8fafc; font-weight: 700; }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 5. UTILIDADES Y LÓGICA DE NEGOCIO
# =============================================================================

class ProductionCalculator:
    """Clase para cálculos técnicos de impresión y conversión."""
    
    @staticmethod
    def calculate_meters(specs: EspecificacionesDTO) -> Dict[str, float]:
        gap = specs.gap_mm
        total_mm = specs.cantidad_total * (specs.largo_mm + gap)
        metros_lineales = total_mm / 1000
        
        # Cálculo de m2
        metros_cuadrados = (specs.ancho_mm / 1000) * metros_lineales
        
        # Estimación de bobinas necesarias
        num_bobinas = 0
        if specs.uds_rollo > 0:
            num_bobinas = math.ceil(specs.cantidad_total / specs.uds_rollo)
            
        return {
            "ml": round(metros_lineales, 2),
            "m2": round(metros_cuadrados, 2),
            "bobinas": num_bobinas
        }

class ValidationService:
    """Validación de datos de entrada."""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        pattern = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        return bool(re.match(pattern, email.lower()))

# =============================================================================
# 6. GENERADOR DE PDF PROFESIONAL
# =============================================================================

class EnterprisePDFGenerator(FPDF):
    def __init__(self, cliente: ClienteDTO, specs: EspecificacionesDTO, prod: ProduccionDTO):
        super().__init__()
        self.cliente = cliente
        self.specs = specs
        self.prod = prod
        self.accent_color = (14, 165, 233) # Sky Blue

    def header(self):
        # Fondo encabezado
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 40, 'F')
        
        self.set_xy(10, 10)
        self.set_font('Arial', 'B', 22)
        self.set_text_color(255, 255, 255)
        self.cell(100, 10, 'FLEXYLABEL', 0, 0, 'L')
        
        self.set_font('Arial', 'B', 10)
        self.set_xy(150, 10)
        self.cell(50, 10, f'ORDEN ID: {self.prod.order_id}', 0, 0, 'R')
        
        self.set_xy(10, 22)
        self.set_font('Arial', '', 8)
        self.set_text_color(148, 163, 184)
        self.cell(100, 5, 'SISTEMA AUTOMATIZADO DE PRODUCCIÓN V6.0', 0, 0, 'L')
        self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'FlexyLabel S.A. | Página {self.page_no()} | Confidencial', 0, 0, 'C')

    def draw_section_header(self, title: str):
        self.ln(5)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(15, 23, 42)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, f"  {title.upper()}", 0, 1, 'L', True)
        self.ln(3)

    def add_data_row(self, label: str, value: str, label2: str = "", value2: str = ""):
        self.set_font('Arial', 'B', 9)
        self.set_text_color(71, 85, 105)
        self.cell(35, 8, f"{label}:", 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(15, 23, 42)
        self.cell(60, 8, f"{value}", 0)
        
        if label2:
            self.set_font('Arial', 'B', 9)
            self.set_text_color(71, 85, 105)
            self.cell(35, 8, f"{label2}:", 0)
            self.set_font('Arial', '', 9)
            self.set_text_color(15, 23, 42)
            self.cell(0, 8, f"{value2}", 0)
        self.ln(7)

    def generate(self, output_path: str):
        self.add_page()
        
        # SECCIÓN CLIENTE
        self.draw_section_header("Información del Cliente")
        self.add_data_row("Razón Social", self.cliente.razon_social, "CIF/NIF", self.cliente.cif)
        self.add_data_row("Contacto", self.cliente.email_contacto, "Teléfono", self.cliente.telefono)
        self.add_data_row("Referencia", self.cliente.referencia_interna, "Fecha Pedido", datetime.date.today().strftime("%d/%m/%Y"))
        
        # SECCIÓN ESPECIFICACIONES
        self.draw_section_header("Especificaciones del Producto")
        self.add_data_row("Material", self.specs.material, "Formato", self.specs.formato)
        self.add_data_row("Medidas (AxL)", f"{self.specs.ancho_mm} x {self.specs.largo_mm} mm", "Cantidad Total", f"{self.specs.cantidad_total} uds")
        
        if self.specs.formato == "Bobina":
            self.draw_section_header("Detalles Técnicos de Bobinado")
            self.add_data_row("Mandril", self.specs.mandril, "Uds por Bobina", f"{self.specs.uds_rollo}")
            self.add_data_row("Cara de Salida", self.prod.tipo_bobinado, "Posición (Imagen)", self.prod.posicion_salida)
            
        # SECCIÓN NOTAS
        if self.prod.notas_maquinista:
            self.draw_section_header("Observaciones de Producción")
            self.set_font('Arial', '', 9)
            self.multi_cell(0, 5, self.prod.notas_maquinista)
            
        self.output(output_path)

# =============================================================================
# 7. SERVICIO DE COMUNICACIONES (SMTP)
# =============================================================================

class EmailDispatcher:
    @staticmethod
    def send_order(cliente: ClienteDTO, prod: ProduccionDTO, pdf_path: str):
        try:
            # Validación de credenciales en secrets
            if "email_usuario" not in st.secrets:
                logger.error("Credenciales SMTP no configuradas.")
                return False

            user = st.secrets["email_usuario"]
            pwd = st.secrets["email_password"]
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = user
            msg['To'] = "produccion@flexylabel.com" # Dirección de taller
            msg['Subject'] = f"🚀 NUEVA OT: {prod.order_id} | {cliente.razon_social}"
            
            body = f"""
            Se ha generado una nueva orden de trabajo.
            ID: {prod.order_id}
            Cliente: {cliente.razon_social}
            Referencia: {cliente.referencia_interna}
            
            Se adjunta ficha técnica y arte final.
            """
            msg.attach(MIMEText(body, 'plain'))

            # Adjuntar PDF de la orden
            with open(pdf_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="OT_{prod.order_id}.pdf"')
                msg.attach(part)

            # Adjuntar Arte Final si existe
            if prod.arte_final:
                af_part = MIMEBase('application', 'octet-stream')
                af_part.set_payload(prod.arte_final.getvalue())
                encoders.encode_base64(af_part)
                af_part.add_header('Content-Disposition', f'attachment; filename="ARTE_FINAL_{prod.order_id}.pdf"')
                msg.attach(af_part)

            # Envío
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(user, pwd)
                server.send_message(msg)
            
            logger.info(f"Orden {prod.order_id} enviada con éxito.")
            return True
        except Exception as e:
            logger.error(f"Fallo en envío de email: {str(e)}")
            return False

# =============================================================================
# 8. COMPONENTES DE INTERFAZ (UI COMPONENTS)
# =============================================================================

def render_sidebar():
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=FLEXYLABEL+LOGO", use_container_width=True)
        st.markdown("---")
        st.markdown("### 🛠 Soporte Técnico")
        st.info("Para incidencias con el portal: \nsoporte@flexylabel.com")
        st.markdown("### 📊 Estado del Sistema")
        st.success("Producción: OPERATIVA")
        st.success("Servidor PDF: ONLINE")

def render_header():
    st.markdown('<div class="title-gradient">FLEXYLABEL ORDER PORTAL</div>', unsafe_allow_html=True)
    st.markdown('<p style="color: #94a3b8; font-size: 1.2rem;">Portal profesional para la gestión de artes gráficas y etiquetas autoadhesivas.</p>', unsafe_allow_html=True)

# =============================================================================
# 9. FLUJO PRINCIPAL (APP MAIN LOOP)
# =============================================================================

def main():
    inject_enterprise_styles()
    render_sidebar()
    render_header()
    
    # Inicialización de estado de bobinado
    if 'winding_selection' not in st.session_state:
        st.session_state.winding_selection = {"cara": "Exterior", "pos": "1A"}

    # --- FORMULARIO PRINCIPAL ---
    with st.form("flexy_order_v6", clear_on_submit=False):
        
        # SECCIÓN 1: CLIENTE
        st.markdown('<div class="section-header"><div class="badge-number">1</div><div class="section-title">Información Corporativa</div></div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        razon_social = c1.text_input("Razón Social / Empresa *")
        cif_cliente = c2.text_input("CIF / NIF *")
        
        c3, c4, c5 = st.columns([2, 1, 2])
        email_cliente = c3.text_input("Correo Electrónico de Contacto *")
        tel_cliente = c4.text_input("Teléfono")
        ref_cliente = c5.text_input("Su Referencia de Pedido (PO)", placeholder="Ej: VERANO-2026-01")

        # SECCIÓN 2: TÉCNICA
        st.markdown('<div class="section-header"><div class="badge-number">2</div><div class="section-title">Especificaciones de Fabricación</div></div>', unsafe_allow_html=True)
        
        c6, c7 = st.columns([1, 1])
        with c6:
            # Flatten dict for selectbox
            all_mats = []
            for cat, items in MATERIALES_CATALOGO.items():
                all_mats.extend(items)
            mat_seleccionado = st.selectbox("Seleccione Material de la Base", all_mats)
            
        with c7:
            formato_entrega = st.radio("Formato de Entrega Final", ["Bobina", "Hojas"], horizontal=True)

        st.markdown("#### Dimensiones y Cantidades")
        c8, c9, c10, c11 = st.columns(4)
        ancho = c8.number_input("Ancho Etiqueta (mm)", min_value=5, value=100)
        largo = c9.number_input("Largo Etiqueta (mm)", min_value=5, value=100)
        gap = c10.number_input("Separación / Gap (mm)", min_value=0.0, value=3.0, step=0.5)
        cantidad = c11.number_input("Cantidad Total a Fabricar", min_value=1, value=5000, step=500)

        # SECCIÓN 3: LOGÍSTICA DE BOBINADO (CONDICIONAL)
        if formato_entrega == "Bobina":
            st.markdown('<div class="section-header"><div class="badge-number">3</div><div class="section-title">Configuración de Bobinado</div></div>', unsafe_allow_html=True)
            
            col_b1, col_b2 = st.columns([1, 2])
            with col_b1:
                mandril = st.selectbox("Núcleo / Mandril", MANDRILES_DISPONIBLES)
                uds_bobina = st.number_input("Etiquetas por Rollo", min_value=10, value=1000)
                cara_bobina = st.radio("Cara del Material", ["Exterior", "Interior"])
            
            with col_b2:
                st.write("📌 **Sentido de Salida (Según su esquema técnico)**")
                # 
                
                if cara_bobina == "Interior":
                    posiciones_img = ["1", "2", "3", "4"]
                    labels_desc = ["1. Cabeza Fuera", "2. Pie Fuera", "3. Derecha Fuera", "4. Izquierda Fuera"]
                else:
                    posiciones_img = ["1A", "2A", "3A", "4A"]
                    labels_desc = ["1A. Cabeza Fuera", "2A. Pie Fuera", "3A. Derecha Fuera", "4A. Izquierda Fuera"]
                
                pos_seleccionada = st.select_slider("Posición de la Etiqueta en Bobina", options=posiciones_img)
                
                # Feedback visual de selección
                idx = posiciones_img.index(pos_seleccionada)
                st.info(f"Seleccionado: **{labels_desc[idx]}**")
        else:
            mandril = "N/A"
            uds_bobina = 0
            cara_bobina = "N/A"
            pos_seleccionada = "Hojas"

        # SECCIÓN 4: ARTE Y MÉTRICAS
        st.markdown('<div class="section-header"><div class="badge-number">4</div><div class="section-title">Arte Final y Métricas de Orden</div></div>', unsafe_allow_html=True)
        
        col_m1, col_m2 = st.columns([1, 1])
        
        with col_m1:
            st.markdown("#### Carga de Archivos")
            arte_final = st.file_uploader("Subir Arte Final (PDF Alta Resolución)", type=["pdf", "ai", "zip"])
            notas = st.text_area("Instrucciones Técnicas Especiales (Barniz, Troquel, etc.)", height=150)
            fecha_entrega = st.date_input("Fecha de entrega deseada", datetime.date.today() + datetime.timedelta(days=7))

        with col_m2:
            st.markdown("#### Resumen Estimado de Producción")
            calc = ProductionCalculator()
            temp_specs = EspecificacionesDTO(ancho, largo, gap, cantidad, mat_seleccionado, "Ninguno", formato_entrega, mandril, uds_bobina)
            res = calc.calculate_meters(temp_specs)
            
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">Metros Lineales (Estimado)</div>
                <div class="metric-value">{res['ml']} m</div>
            </div>
            <div class="metric-box" style="margin-top:10px;">
                <div class="metric-label">Superficie Total</div>
                <div class="metric-value">{res['m2']} m²</div>
            </div>
            <div class="metric-box" style="margin-top:10px; border-left-color: #818cf8;">
                <div class="metric-label">Total Unidades Logísticas</div>
                <div class="metric-value">{res['bobinas'] if formato_entrega == "Bobina" else 1} {formato_entrega if formato_entrega == "Bobina" else "Paquete"}</div>
            </div>
            """, unsafe_allow_html=True)

        # --- BOTÓN DE PROCESAMIENTO ---
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("🚀 GENERAR Y ENVIAR ORDEN DE TRABAJO")

        if submit:
            # Validaciones de Seguridad
            if not razon_social or not email_cliente or not cif_cliente:
                st.error("❌ Los campos marcados con asterisco (*) son obligatorios.")
            elif not ValidationService.is_valid_email(email_cliente):
                st.error("❌ El formato del correo electrónico no es válido.")
            elif not arte_final:
                st.warning("⚠️ No se ha adjuntado Arte Final. La orden quedará pendiente de recepción de archivos.")
                # Permitimos continuar bajo responsabilidad del cliente
            else:
                try:
                    with st.spinner("🛠 Generando documentación técnica..."):
                        # Construcción de Objetos
                        client_obj = ClienteDTO(razon_social, cif_cliente, email_cliente, tel_cliente, "Dirección Fiscal", ref_cliente)
                        specs_obj = temp_specs
                        prod_obj = ProduccionDTO(cara_bobina, pos_seleccionada, notas, fecha_entrega, arte_final)
                        
                        # Generación PDF
                        pdf_name = f"OT_{prod_obj.order_id}.pdf"
                        generator = EnterprisePDFGenerator(client_obj, specs_obj, prod_obj)
                        generator.generate(pdf_name)
                        
                        # Envío por correo
                        dispatcher = EmailDispatcher()
                        if dispatcher.send_order(client_obj, prod_obj, pdf_name):
                            st.success(f"✅ ORDEN {prod_obj.order_id} PROCESADA CON ÉXITO")
                            st.balloons()
                            st.info("Se ha enviado una copia de la ficha técnica al correo de producción.")
                            
                            # Limpieza
                            if os.path.exists(pdf_name):
                                os.remove(pdf_name)
                        else:
                            st.error("Fallo al enviar el correo. Por favor, descargue la orden manualmente y envíela a taller.")
                            with open(pdf_name, "rb") as f:
                                st.download_button("Descargar Orden de Trabajo", f, file_name=pdf_name)
                
                except Exception as e:
                    st.error(f"Error crítico en el motor de órdenes: {str(e)}")
                    logger.critical(f"CRASH: {str(e)}")

# =============================================================================
# 10. INICIO DE APLICACIÓN
# =============================================================================

if __name__ == "__main__":
    main()
