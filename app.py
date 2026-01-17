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

# --- CONFIGURACIÓN TÉCNICA ---
DESTINATARIO_FINAL = "covet@etiquetes.com"
LOGO_URL = "https://flexylabel.com/wp-content/uploads/2022/03/logo-flexylabel.png" # URL de ejemplo

# --- ESTILOS VISUALES AVANZADOS ---
def aplicar_diseno_moderno():
    st.markdown("""
        <style>
            .main { background-color: #f4f7f9; }
            .stButton>button {
                width: 100%;
                border-radius: 20px;
                height: 3em;
                background-color: #004a99;
                color: white;
                font-weight: bold;
                border: none;
                transition: 0.3s;
            }
            .stButton>button:hover {
                background-color: #002d5d;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select {
                border-radius: 10px;
            }
            .section-card {
                background-color: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                margin-bottom: 20px;
            }
            h1 { color: #004a99; font-family: 'Helvetica Neue', sans-serif; }
            h3 { color: #333; border-bottom: 2px solid #004a99; padding-bottom: 5px; }
        </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE GENERACIÓN DE PDF ---
class OrdenProduccionPDF(FPDF):
    def header(self):
        # Fondo decorativo en el encabezado
        self.set_fill_color(0, 74, 153)
        self.rect(0, 0, 210, 40, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", 'B', 22)
        self.cell(0, 20, "FLEXYLABEL IMPRESSORS", ln=True, align='C')
        self.set_font("Arial", 'I', 10)
        self.cell(0, 5, "ORDEN TÉCNICA DE PRODUCCIÓN AUTOMATIZADA", ln=True, align='C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Hoja de producción - FlexyLabel S.L. - Página {self.page_no()}", align='C')

def generar_documento_tecnico(datos):
    pdf = OrdenProduccionPDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # Bloque 1: Cliente
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, " 1. IDENTIFICACIÓN DEL PROYECTO", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.ln(2)
    pdf.cell(100, 8, f"CLIENTE: {datos['cliente']}")
    pdf.cell(0, 8, f"FECHA ENTREGA: {datos['fecha_entrega']}", ln=True)
    pdf.cell(100, 8, f"REF. DISEÑO: {datos['referencia']}")
    pdf.cell(0, 8, f"CONTACTO: {datos['email_cliente']}", ln=True)
    pdf.ln(5)

    # Bloque 2: Datos Técnicos
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, " 2. ESPECIFICACIONES DE FABRICACIÓN", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    
    # Tabla de medidas
    pdf.ln(2)
    data_tecnica = [
        ["MEDIDAS (An x Lar)", f"{datos['ancho']} x {datos['largo']} mm", "SISTEMA", datos['sistema']],
        ["CANTIDAD", f"{datos['cantidad']} uds", "MATERIAL", datos['material']],
        ["SENTIDO SALIDA", f"Posición {datos['sentido']}", "MANDRIL", datos['mandril']],
        ["SALIDA", datos['salida_tipo'], "ACABADO", datos['acabado']]
    ]
    
    for row in data_tecnica:
        pdf.cell(45, 8, row[0], 1)
        pdf.cell(50, 8, row[1], 1)
        pdf.cell(45, 8, row[2], 1)
        pdf.cell(50, 8, row[3], 1, ln=True)

    # Bloque 3: Observaciones
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, " 3. OBSERVACIONES TÉCNICAS", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 8, datos['obs'])

    filename = f"Orden_{datos['cliente']}_{datos['referencia']}.pdf".replace(" ", "_")
    pdf.output(filename)
    return filename

# --- LÓGICA DE ENVÍO SEGURO ---
def enviar_por_correo(pdf_ruta, archivo_cliente, datos):
    try:
        user = st.secrets["email_usuario"]
        pwd = st.secrets["email_password"]
        
        msg = MIMEMultipart()
        msg['Subject'] = f"🟢 NUEVA ORDEN: {datos['cliente']} - {datos['referencia']}"
        msg['From'] = user
        msg['To'] = DESTINATARIO_FINAL
        
        cuerpo = f"Se ha generado una nueva orden técnica.\nCliente: {datos['cliente']}\nRef: {datos['referencia']}"
        msg.attach(MIMEText(cuerpo, 'plain'))

        # Adjuntar PDF generado
        with open(pdf_ruta, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{pdf_ruta}"')
            msg.attach(part)

        # Adjuntar PDF del cliente
        if archivo_cliente:
            part_c = MIMEBase('application', 'octet-stream')
            part_c.set_payload(archivo_cliente.getvalue())
            encoders.encode_base64(part_c)
            part_c.add_header('Content-Disposition', f'attachment; filename="DISENO_{archivo_cliente.name}"')
            msg.attach(part_c)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error crítico en el servidor de correo: {e}")
        return False

# --- INTERFAZ DE USUARIO (STREMLIT) ---
aplicar_diseno_moderno()

st.title("🚀 FlexyLabel: Gestión de Pedidos")
st.markdown("Plataforma técnica para la planificación de impresión de etiquetas.")

with st.form("form_avanzado"):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📁 Identificación del Trabajo")
    c1, c2 = st.columns(2)
    with c1:
        cliente = st.text_input("Nombre del Cliente", placeholder="Ej: Vinos del Sur S.A.")
        email_cliente = st.text_input("Email de contacto")
    with c2:
        referencia = st.text_input("Referencia / Nombre del Diseño", placeholder="Ej: Etiqueta Frontal v2")
        fecha_entrega = st.date_input("Fecha de entrega solicitada")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📐 Especificaciones Técnicas")
    c3, c4, c5 = st.columns(3)
    with c3:
        ancho = st.number_input("Ancho (mm)", min_value=1, value=100)
        largo = st.number_input("Largo (mm)", min_value=1, value=100)
    with c4:
        cantidad = st.number_input("Cantidad Total", min_value=1, value=5000, step=500)
        material = st.selectbox("Material", ["Couché", "PP Blanco", "PP Transparente", "Térmico", "Verjurado"])
    with c5:
        sistema = st.selectbox("Sistema", ["Flexografía", "Digital", "Offset", "Tipografía"])
        acabado = st.text_input("Acabado (Barniz, Oro, etc.)", value="Barniz Brillo")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🌀 Configuración de Bobinado")
    c6, c7 = st.columns(2)
    with c6:
        salida_tipo = st.radio("Salida", ["Exterior", "Interior"], horizontal=True)
        sentido = st.select_slider("Sentido de salida", options=[str(i) for i in range(1, 9)])
    with c7:
        mandril = st.selectbox("Diámetro Mandril", ["40mm", "76mm", "25mm"])
        archivo_pdf = st.file_uploader("Subir PDF del modelo", type=["pdf"])
    st.markdown('</div>', unsafe_allow_html=True)

    obs = st.text_area("Observaciones de producción")
    
    boton_enviar = st.form_submit_button("VALIDAR Y ENVIAR PEDIDO")

    if boton_enviar:
        if not cliente or not referencia or not archivo_pdf:
            st.warning("⚠️ Iván, rellena los campos obligatorios y adjunta el PDF.")
        else:
            with st.spinner("Generando documentación técnica y enviando..."):
                datos = {
                    "cliente": cliente, "referencia": referencia, "email_cliente": email_cliente,
                    "fecha_entrega": fecha_entrega, "ancho": ancho, "largo": largo,
                    "cantidad": cantidad, "material": material, "sistema": sistema,
                    "acabado": acabado, "salida_tipo": salida_tipo, "sentido": sentido,
                    "mandril": mandril, "obs": obs
                }
                
                pdf_generado = generar_documento_tecnico(datos)
                exito = enviar_por_correo(pdf_generado, archivo_pdf, datos)
                
                if exito:
                    st.success(f"✅ ¡Pedido enviado correctamente a {DESTINATARIO_FINAL}!")
                    st.balloons()
                    if os.path.exists(pdf_generado):
                        os.remove(pdf_generado)
