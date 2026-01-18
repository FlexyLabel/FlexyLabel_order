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
# 1. CONFIGURACIÓN Y LOGS
# =============================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FlexyLabel_Core")

st.set_page_config(
    page_title="FlexyLabel Terminal v6.4 | Enterprise",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏭"
)

# =============================================================================
# 2. DEFINICIÓN DE DATOS (DTOs)
# =============================================================================
@dataclass
class ClienteDTO:
    """Datos relativos al cliente y la logística del pedido"""
    razon_social: str
    email_contacto: str
    referencia_interna: str
    fecha_entrega: datetime.date
    tipo_documento: str  # Valores: "Presupuesto" o "Pedido"

@dataclass
class EspecificacionesDTO:
    """Datos técnicos de la etiqueta"""
    ancho_mm: float
    largo_mm: float
    cantidad_total: int
    material: str
    mandril: str
    uds_rollo: int
    formato_entrega: str # Valores: "Bobina" o "Hojas (Plano)"

@dataclass
class ProduccionDTO:
    """Datos para el operario de máquina"""
    sentido_bobinado: str
    notas_maquinista: str
    arte_final: any

# =============================================================================
# 3. MOTOR GRÁFICO SVG (VISUALIZACIÓN BOBINADO)
# =============================================================================
def get_winding_svg(position_id: int) -> str:
    """
    Genera el gráfico vectorial para las posiciones 1-8.
    Usa colores NEÓN para alto contraste sobre fondo oscuro.
    """
    # Determinamos si es bobinado interior o exterior
    is_interior = position_id > 4
    
    # Colores: Cian (#08D9D6) para Exterior, Rojo (#FF2E63) para Interior
    if is_interior:
        main_color = "#FF2E63" 
        label_text = "INT"
    else:
        main_color = "#08D9D6"
        label_text = "EXT"
    
    # Estructura base del SVG (Tarjeta oscura)
    svg = f"""
    <svg width="120" height="140" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg">
        <rect width="100" height="120" rx="8" fill="#1A1C24" stroke="#333" stroke-width="1"/>
        
        <circle cx="50" cy="50" r="30" stroke="#444" stroke-width="4" fill="none" />
        <circle cx="50" cy="50" r="8" fill="#444" />
    """
    
    # Dibujo de la flecha según la posición (Desglosado para claridad)
    arrow_path = ""
    if position_id == 1 or position_id == 5: # TOP
        arrow_path = f'<path d="M50 20 L50 5 M40 12 L50 5 L60 12" stroke="{main_color}" stroke-width="5" fill="none"/>'
    elif position_id == 2 or position_id == 6: # BOTTOM
        arrow_path = f'<path d="M50 80 L50 95 M40 88 L50 95 L60 88" stroke="{main_color}" stroke-width="5" fill="none"/>'
    elif position_id == 3 or position_id == 7: # RIGHT
        arrow_path = f'<path d="M80 50 L95 50 M88 40 L95 50 L88 60" stroke="{main_color}" stroke-width="5" fill="none"/>'
    elif position_id == 4 or position_id == 8: # LEFT
        arrow_path = f'<path d="M20 50 L5 50 M12 40 L5 50 L12 60" stroke="{main_color}" stroke-width="5" fill="none"/>'
    
    # Etiqueta de texto (INT/EXT)
    label_box = f'''
        <rect x="30" y="42" width="40" height="16" rx="3" fill="{main_color}"/>
        <text x="50" y="54" font-family="monospace" font-size="9" fill="black" text-anchor="middle" font-weight="bold">{label_text}</text>
    '''
    
    # Ensamblaje final
    svg += arrow_path + label_box + f"""
        <text x="50" y="112" font-family="monospace" font-size="14" fill="white" text-anchor="middle" font-weight="bold">P-{position_id}</text>
    </svg>
    """
    
    # Codificación Base64 para Streamlit
    b64_code = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64_code}"

# =============================================================================
# 4. ESTILOS CSS (DARK FACTORY THEME)
# =============================================================================
def inject_radical_css():
    st.markdown("""
        <style>
            /* Fondo Global */
            .stApp { 
                background-color: #0E1117; 
            }
            
            /* Tipografías */
            h1, h2, h3 { 
                color: #FFFFFF !important; 
                font-family: 'JetBrains Mono', monospace; 
                text-transform: uppercase; 
                letter-spacing: 1.5px;
            }
            
            /* Radio Button (Presupuesto/Pedido) */
            div[role="radiogroup"] {
                background: #161B22;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #30363D;
                margin-bottom: 25px;
                display: flex;
                justify-content: center;
                gap: 30px;
            }
            div[role="radiogroup"] label {
                font-size: 1.2rem !important;
                font-weight: bold !important;
                color: #08D9D6 !important;
            }

            /* Tarjetas de Contenido */
            .industrial-card {
                background: #161B22;
                border: 1px solid #30363D;
                border-left: 6px solid #08D9D6; /* Borde Cian Neón */
                padding: 2rem;
                border-radius: 12px;
                margin-bottom: 25px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            }

            /* Campos de formulario (Inputs) */
            input, select, textarea, .stNumberInput input, .stDateInput input {
                background-color: #0D1117 !important;
                border: 1px solid #30363D !important;
                color: #08D9D6 !important;
                font-family: 'JetBrains Mono', monospace !important;
                font-size: 1rem !important;
            }
            input:focus {
                border-color: #08D9D6 !important;
                box-shadow: 0 0 10px rgba(8, 217, 214, 0.2) !important;
            }

            /* Botón de Acción Principal */
            .stButton > button {
                background: transparent !important;
                color: #08D9D6 !important;
                border: 2px solid #08D9D6 !important;
                height: 5rem;
                font-size: 1.4rem !important;
                font-weight: 800 !important;
                text-transform: uppercase;
                width: 100%;
                transition: all 0.3s ease;
                letter-spacing: 2px;
            }
            .stButton > button:hover {
                background: #08D9D6 !important;
                color: #000 !important;
                box-shadow: 0 0 25px rgba(8, 217, 214, 0.6);
                transform: translateY(-2px);
            }

            /* HUD Stats (Métricas) */
            .stat-box {
                background: #1A1C24;
                padding: 1.5rem;
                border-radius: 8px;
                border-bottom: 4px solid #08D9D6;
                text-align: center;
                transition: transform 0.2s;
            }
            .stat-box:hover {
                transform: scale(1.02);
            }
            .stat-val { 
                font-size: 2.2rem; 
                color: #FFF; 
                font-weight: 800; 
                font-family: 'JetBrains Mono'; 
            }
            .stat-lbl { 
                font-size: 0.8rem; 
                color: #8B949E; 
                text-transform: uppercase; 
                letter-spacing: 1px;
                margin-bottom: 5px;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 5. GENERADOR DE PDF
# =============================================================================
class EnterprisePDF(FPDF):
    def __init__(self, doc_type="ORDEN DE TRABAJO"):
        super().__init__()
        self.doc_type_title = doc_type
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Cabecera Cyan
        self.set_fill_color(8, 217, 214)
        self.rect(0, 0, 210, 35, 'F')
        
        # Título
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(20, 20, 20)
        self.set_xy(10, 12)
        self.cell(0, 10, f'{self.doc_type_title} | FLEXYLABEL SYSTEM', 0, 1, 'L')
        
        # Subtítulo
        self.set_font('Helvetica', '', 10)
        self.cell(0, 5, 'Documento generado automáticamente v6.4', 0, 1, 'L')

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def add_section(self, title, data_dict):
        """Crea un bloque de datos con título gris"""
        self.ln(10)
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f"  {title}", 0, 1, 'L', True)
        
        self.set_font('Helvetica', '', 11)
        self.ln(2)
        
        for key, value in data_dict.items():
            self.set_text_color(80, 80, 80) # Label gris
            self.cell(60, 7, f"{key}:", 0)
            self.set_text_color(0, 0, 0)    # Valor negro
            self.cell(0, 7, f"{value}", 0, 1)

# =============================================================================
# 6. SERVICIO DE EMAIL (Multilenguaje)
# =============================================================================
class EmailService:
    @staticmethod
    def send_dual(client: ClienteDTO, specs: EspecificacionesDTO, prod: ProduccionDTO, pdf_path: str):
        try:
            # Credenciales desde secrets
            user = st.secrets["email_usuario"]
            pwd = st.secrets["email_password"]
            
            # Leemos el PDF una sola vez
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # -----------------------------------------------------------------
            # EMAIL 1: TALLER / PRODUCCIÓN (CATALÀ)
            # -----------------------------------------------------------------
            
            # Lógica de traducción para el taller
            tipo_cat = "COMANDA" if client.tipo_documento == "Pedido" else "PRESSUPOST"
            formato_cat = "Bobina" if specs.formato_entrega == "Bobina" else "Fulls/Pla"
            
            msg_taller = MIMEMultipart()
            msg_taller['From'] = user
            msg_taller['To'] = "covet@etiquetes.com"
            msg_taller['Subject'] = f"🏭 [NOVA {tipo_cat}]: {client.razon_social} | REF: {client.referencia_interna}"
            
            # Cuerpo del mensaje en Catalán
            body_cat = f"""
            Bon dia equip,

            S'ha registrat una nova operació al sistema FlexyLabel.
            
            DADES PRINCIPALS:
            ------------------------------------------
            Tipus:            {tipo_cat}
            Client:           {client.razon_social}
            Referència:       {client.referencia_interna}
            Data d'entrega:   {client.fecha_entrega.strftime('%d/%m/%Y')}
            
            DETALLS TÈCNICS:
            ------------------------------------------
            Format:           {formato_cat}
            Material:         {specs.material}
            Quantitat:        {specs.cantidad_total} unitats
            
            S'adjunta la fitxa tècnica (PDF) i l'Art Final per a la seva revisió.
            
            Salutacions,
            FlexyLabel Enterprise System.
            """
            msg_taller.attach(MIMEText(body_cat, 'plain'))
            
            # Adjunto PDF Taller
            att_taller = MIMEBase('application', 'octet-stream')
            att_taller.set_payload(pdf_bytes)
            encoders.encode_base64(att_taller)
            att_taller.add_header('Content-Disposition', f'attachment; filename="{client.tipo_documento}_{client.referencia_interna}.pdf"')
            msg_taller.attach(att_taller)

            # Adjunto Arte Final (si existe)
            if prod.arte_final:
                af_att = MIMEBase('application', 'octet-stream')
                af_att.set_payload(prod.arte_final.getvalue())
                encoders.encode_base64(af_att)
                af_att.add_header('Content-Disposition', f'attachment; filename="ART_FINAL_PROD.pdf"')
                msg_taller.attach(af_att)

            # -----------------------------------------------------------------
            # EMAIL 2: CLIENTE (ESPAÑOL)
            # -----------------------------------------------------------------
            msg_cliente = MIMEMultipart()
            msg_cliente['From'] = user
            msg_cliente['To'] = client.email_contacto
            msg_cliente['Subject'] = f"✅ Confirmación de {client.tipo_documento}: {client.referencia_interna}"
            
            body_esp = f"""
            Estimado cliente ({client.razon_social}),

            Confirmamos la recepción de su {client.tipo_documento.lower()}.
            
            Referencia: {client.referencia_interna}
            Fecha de entrega solicitada: {client.fecha_entrega.strftime('%d/%m/%Y')}
            
            Adjuntamos el documento con los detalles técnicos para su validación.
            
            Atentamente,
            El equipo de FlexyLabel.
            """
            msg_cliente.attach(MIMEText(body_esp, 'plain'))
            
            # Reutilizamos el PDF para el cliente
            # (Nota: Hay que crear un nuevo objeto MIMEBase para evitar conflictos de punteros en algunos servidores SMTP, aunque el contenido sea el mismo)
            att_cliente = MIMEBase('application', 'octet-stream')
            att_cliente.set_payload(pdf_bytes)
            encoders.encode_base64(att_cliente)
            att_cliente.add_header('Content-Disposition', f'attachment; filename="Documentacion_{client.referencia_interna}.pdf"')
            msg_cliente.attach(att_cliente)

            # -----------------------------------------------------------------
            # ENVÍO SMTP
            # -----------------------------------------------------------------
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(user, pwd)
                server.send_message(msg_taller)
                server.send_message(msg_cliente)
                
            return True
            
        except Exception as e:
            st.error(f"❌ Error crítico en el envío de correos: {str(e)}")
            logger.error(f"Fallo SMTP: {e}")
            return False

# =============================================================================
# 7. INTERFAZ DE USUARIO (UI)
# =============================================================================
def main():
    inject_radical_css()
    
    # Inicialización de estado
    if 'winding_pos' not in st.session_state: 
        st.session_state.winding_pos = "3"

    # Título Principal
    st.markdown("<h1>🎛️ Terminal FlexyLabel v6.4 | Enterprise</h1>", unsafe_allow_html=True)
    
    with st.form("form_produccion"):
        
        # --- SELECTOR DE MODO (PRESUPUESTO / PEDIDO) ---
        tipo_doc = st.radio("MODO DE OPERACIÓN:", ["Pedido", "Presupuesto"], horizontal=True)

        # ---------------------------------------------------------------------
        # SECCIÓN 1: DATOS ADMINISTRATIVOS
        # ---------------------------------------------------------------------
        st.markdown('<div class="industrial-card"><h3>01. DATOS Y LOGÍSTICA</h3>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Razón Social", placeholder="Nombre Empresa")
        email = c2.text_input("Email de Confirmación", placeholder="cliente@empresa.com")
        
        c3, c4 = st.columns(2)
        ref = c3.text_input("Ref. Interna", value="OT-2026-X")
        # Fecha con valor por defecto +7 días
        fecha_entrega = c4.date_input("Fecha de Entrega Solicitada", datetime.date.today() + datetime.timedelta(days=7))
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # SECCIÓN 2: ESPECIFICACIONES TÉCNICAS
        # ---------------------------------------------------------------------
        st.markdown('<div class="industrial-card"><h3>02. ESPECIFICACIONES TÉCNICAS</h3>', unsafe_allow_html=True)
        
        # Fila 1: Formato y Material
        c_format, c_mat, c_cant = st.columns(3)
        formato = c_format.selectbox("Formato de Entrega", ["Bobina", "Hojas (Plano)"])
        material = c_mat.selectbox("Material", ["PP Blanco", "Couché", "Térmico Eco", "Verjurado", "Cartulina"])
        cantidad = c_cant.number_input("Cantidad Total", value=5000, step=100)

        # Fila 2: Medidas y Mandril
        c_med1, c_med2, c_extra = st.columns(3)
        ancho = c_med1.number_input("Ancho (mm)", value=100)
        largo = c_med2.number_input("Largo (mm)", value=100)
        
        # Lógica condicional: Si es Hojas, el mandril no aplica
        if formato == "Bobina":
            mandril = c_extra.selectbox("Mandril", ["Ø 76 mm", "Ø 40 mm", "Ø 25 mm"])
            u_r_input = st.number_input("Uds / Rollo", value=1000)
        else:
            mandril = "N/A (Plano)"
            c_extra.info("ℹ️ Modo Hojas: Sin mandril")
            u_r_input = 0 # No aplica

        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # SECCIÓN 3: BOBINADO (Visualización SVG)
        # ---------------------------------------------------------------------
        # El título cambia para indicar si esta sección es relevante
        titulo_bobinado = "03. ORIENTACIÓN DE SALIDA"
        if formato != "Bobina":
            titulo_bobinado += " (DESACTIVADO EN MODO HOJAS)"
            
        st.markdown(f'<div class="industrial-card"><h3>{titulo_bobinado}</h3>', unsafe_allow_html=True)
        
        cols_svg = st.columns(8)
        # Renderizamos los 8 SVGs
        for i in range(1, 9):
            with cols_svg[i-1]:
                st.image(get_winding_svg(i), use_container_width=True)
                
                # Checkbox deshabilitado si no es Bobina
                disabled_chk = (formato == "Hojas (Plano)")
                is_checked = (str(i) == st.session_state.winding_pos)
                
                if st.checkbox(f"P{i}", value=is_checked, key=f"pos_{i}", disabled=disabled_chk):
                    st.session_state.winding_pos = str(i)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # SECCIÓN 4: DOCUMENTACIÓN Y NOTAS
        # ---------------------------------------------------------------------
        st.markdown('<div class="industrial-card"><h3>04. DOCUMENTACIÓN ADJUNTA</h3>', unsafe_allow_html=True)
        ca, cb = st.columns([1, 1])
        arte = ca.file_uploader("Subir Arte Final (PDF)", type="pdf")
        obs = cb.text_area("Notas para Producción / Acabados")
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # HUD: MÉTRICAS EN TIEMPO REAL
        # ---------------------------------------------------------------------
        # Cálculo simple de metros lineales
        ml_calc = round((cantidad * (largo + 3)) / 1000, 2)
        
        st.markdown(f"""
            <div style="display: flex; gap: 20px; margin-bottom: 30px;">
                <div class="stat-box" style="flex:1">
                    <div class="stat-lbl">Metros Lineales Est.</div>
                    <div class="stat-val">{ml_calc} m</div>
                </div>
                <div class="stat-box" style="flex:1">
                    <div class="stat-lbl">Fecha Entrega</div>
                    <div class="stat-val" style="color: #FF2E63;">{fecha_entrega.strftime('%d-%m')}</div>
                </div>
                <div class="stat-box" style="flex:1">
                    <div class="stat-lbl">Documento</div>
                    <div class="stat-val" style="color: #08D9D6;">{tipo_doc.upper()}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Botón de envío dinámico
        btn_label = f"🚀 PROCESAR {tipo_doc.upper()}"
        submit = st.form_submit_button(btn_label)

        # ---------------------------------------------------------------------
        # LÓGICA DE PROCESAMIENTO
        # ---------------------------------------------------------------------
        if submit:
            # Validaciones básicas
            if not cliente or not email:
                st.error("❌ ERROR: Faltan campos obligatorios (Cliente o Email).")
            elif tipo_doc == "Pedido" and not arte:
                 st.warning("⚠️ ATENCIÓN: Estás cursando un PEDIDO sin Arte Final. Se procesará, pero recuerda enviarlo.")
            
            else:
                with st.spinner(f"Generando documentación para {tipo_doc}..."):
                    
                    # 1. Crear Objetos de Datos (DTOs)
                    client_dto = ClienteDTO(cliente, email, ref, fecha_entrega, tipo_doc)
                    specs_dto = EspecificacionesDTO(ancho, largo, cantidad, material, mandril, u_r_input, formato)
                    prod_dto = ProduccionDTO(st.session_state.winding_pos, obs, arte)

                    # 2. Generar PDF
                    title_pdf = f"{tipo_doc.upper()} DE PRODUCCIÓN"
                    pdf = EnterprisePDF(doc_type=title_pdf)
                    pdf.add_page()
                    
                    pdf.add_section("DATOS GENERALES", {
                        "Empresa": cliente, 
                        "Tipo Documento": tipo_doc.upper(),
                        "Referencia": ref, 
                        "Fecha Entrega": fecha_entrega.strftime('%d/%m/%Y'),
                        "Email Contacto": email
                    })
                    
                    pdf.add_section("ESPECIFICACIONES TÉCNICAS", {
                        "Formato Entrega": formato,
                        "Material": material, 
                        "Medidas": f"{ancho} x {largo} mm", 
                        "Cantidad Total": cantidad,
                        "Mandril": mandril
                    })
                    
                    # Texto del bobinado condicional
                    if formato == "Bobina":
                        winding_txt = f"Posición {st.session_state.winding_pos}" 
                        extra_info = f"{u_r_input} uds/rollo"
                    else:
                        winding_txt = "N/A (Entrega en Hojas/Plano)"
                        extra_info = "Paquetes estándar"

                    pdf.add_section("DETALLES DE PRODUCCIÓN", {
                        "Bobinado": winding_txt,
                        "Empaquetado": extra_info,
                        "Consumo Aprox.": f"{ml_calc} metros lineales"
                    })
                    
                    if obs: 
                        pdf.add_section("OBSERVACIONES Y ACABADOS", {"Notas": obs})
                    
                    # Guardar PDF temporal
                    pdf_path = f"{tipo_doc}_{ref}.pdf"
                    pdf.output(pdf_path)
                    
                    # 3. Enviar Emails
                    envio_exitoso = EmailService.send_dual(client_dto, specs_dto, prod_dto, pdf_path)
                    
                    if envio_exitoso:
                        st.success(f"✅ ÉXITO: {tipo_doc} procesado correctamente. Notificaciones enviadas.")
                        # Limpieza
                        if os.path.exists(pdf_path): 
                            os.remove(pdf_path)
                    else:
                        st.error("❌ Error al enviar los correos. Revise los logs.")

if __name__ == "__main__":
    main()
