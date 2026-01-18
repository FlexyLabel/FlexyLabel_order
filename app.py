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
            .stApp { background-color: #0b1121; font-family: 'Inter', sans-serif; }
            .section-header { display: flex; align-items: center; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); padding-bottom: 0.5rem; }
            .section-number { background: linear-gradient(135deg, #0ea5e9, #2563eb); color: white; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; margin-right: 12px; font-family: 'JetBrains Mono', monospace; }
            .section-title { font-size: 1.1rem; font-weight: 700; color: #e2e8f0; letter-spacing: 0.05em; }
            div[data-testid="stForm"] { background: rgba(30, 41, 59, 0.4); backdrop-filter: blur(12px); border-radius: 20px; padding: 3rem; border: 1px solid rgba(255, 255, 255, 0.08); }
            .hud-card { background: #1e293b; border-radius: 12px; padding: 20px; border-top: 3px solid #0ea5e9; }
            .hud-value { font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; color: #38bdf8; }
            .hud-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 4. MOTOR DE PDF
# =============================================================================
class EnterprisePDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 45, 'F')
        self.set_xy(10, 12)
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'FLEXYLABEL PRODUCTION', ln=True)

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
    
    # Encabezado
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
            <h1 style="font-weight: 800; color: #38bdf8;">FLEXYLABEL <span style="color:white; font-size: 1rem;">V6.0</span></h1>
        </div>
    """, unsafe_allow_html=True)

    with st.form("production_form"):
        # SECCIÓN 1: CLIENTE
        st.markdown('<div class="section-header"><div class="section-number">1</div><div class="section-title">DATOS DEL CLIENTE</div></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        razon_social = col1.text_input("Razón Social")
        email_contacto = col2.text_input("Email para Ficha Técnica")
        ref_interna = col3.text_input("Referencia / Pedido")

        # SECCIÓN 2: ESPECIFICACIONES
        st.markdown('<div class="section-header"><div class="section-number">2</div><div class="section-title">ESPECIFICACIONES TÉCNICAS</div></div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        ancho = c1.number_input("Ancho Etiqueta (mm)", value=100.0)
        largo = c2.number_input("Largo Etiqueta (mm)", value=100.0)
        cantidad = c3.number_input("Cantidad Total", value=1000, step=100)
        material = c4.selectbox("Material", ["Couché Brillo", "Térmico Protegido", "PP Blanco", "Papel Kraft"])

        # SECCIÓN 3: BOBINADO (Visual)
        st.markdown('<div class="section-header"><div class="section-number">3</div><div class="section-title">SENTIDO DE BOBINADO</div></div>', unsafe_allow_html=True)
        
        # Mostrar los 8 iconos SVG
        cols_svg = st.columns(8)
        for i in range(1, 9):
            cols_svg[i-1].image(get_winding_svg(i))
        
        sentido_opt = ["POS 1", "POS 2", "POS 3", "POS 4", "POS 5 (INT)", "POS 6 (INT)", "POS 7 (INT)", "POS 8 (INT)"]
        sentido_sel = st.select_slider("Selecciona la posición de salida", options=sentido_opt)

        # SECCIÓN 4: PRODUCCIÓN Y ARTE
        st.markdown('<div class="section-header"><div class="section-number">4</div><div class="section-title">ARCHIVOS Y NOTAS</div></div>', unsafe_allow_html=True)
        arte_final = st.file_uploader("Adjuntar Arte Final (PDF)", type=["pdf"])
        notas = st.text_area("Instrucciones para taller")

        # CÁLCULOS EN TIEMPO REAL (Simulados en UI)
        ml, m2 = CalculadoraProduccion.calcular_consumos(EspecificacionesDTO(ancho, largo, cantidad, material, "", 0))
        
        st.markdown(f"""
            <div style="display: flex; gap: 20px; margin-top: 20px;">
                <div class="hud-card"><div class="hud-label">Metros Lineales</div><div class="hud-value">{ml} m</div></div>
                <div class="hud-card"><div class="hud-label">Superficie Total</div><div class="hud-value">{m2} m²</div></div>
            </div>
        """, unsafe_allow_html=True)

        submit = st.form_submit_button("🚀 GENERAR Y ENVIAR ORDEN")

        if submit:
            if not razon_social or not email_contacto:
                st.error("Por favor, completa los datos del cliente.")
            else:
                st.success(f"Orden para {razon_social} procesada correctamente.")

if __name__ == "__main__":
    main()
