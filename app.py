import streamlit as st
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime

# --- CONFIGURACIÓN ---
DESTINATARIO_FINAL = "covet@etiquetes.com"

def crear_pdf_tecnico(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="FLEXYLABEL IMPRESSORS S.L. - ORDEN DE PRODUCCIÓN", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 7, txt=f"Generado el: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)

    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="1. INFORMACIÓN GENERAL", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, txt=f"Cliente: {datos['cliente']}", ln=True)
    pdf.cell(0, 8, txt=f"Referencia / Diseño: {datos['referencia']}", ln=True)
    pdf.cell(0, 8, txt=f"Fecha de entrega solicitada: {datos['fecha_entrega']}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="2. PARÁMETROS TÉCNICOS", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(95, 8, txt=f"Tamaño: {datos['ancho']} x {datos['largo']} mm", border=1)
    pdf.cell(95, 8, txt=f"Material: {datos['material']}", border=1, ln=True)
    pdf.cell(95, 8, txt=f"Salida: {datos['salida_tipo']}", border=1)
    pdf.cell(95, 8, txt=f"Sentido Bobinado: {datos['sentido']}", border=1, ln=True)
    pdf.cell(95, 8, txt=f"Mandril / Eje: {datos['mandril']}", border=1)
    pdf.cell(95, 8, txt=f"Cantidad: {datos['cantidad']} uds.", border=1, ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="3. OBSERVACIONES ADICIONALES", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 8, txt=datos['obs'])

    filename = f"Orden_{datos['referencia'].replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename

def enviar_email_completo(archivo_orden, archivo_cliente, datos_resumen):
    me = st.secrets["email_usuario"]
    password = st.secrets["email_password"]
    msg = MIMEMultipart()
    msg['Subject'] = f"Nuevo Pedido: {datos_resumen['referencia']} - {datos_resumen['cliente']}"
    msg['From'] = me
    msg['To'] = DESTINATARIO_FINAL
    cuerpo = f"Nueva solicitud para FlexyLabel.\nCliente: {datos_resumen['cliente']}\nReferencia: {datos_resumen['referencia']}"
    msg.attach(MIMEText(cuerpo, 'plain'))

    with open(archivo_orden, "rb") as f:
        part1 = MIMEBase('application', 'octet-stream')
        part1.set_payload(f.read())
        encoders.encode_base64(part1)
        part1.add_header('Content-Disposition', f'attachment; filename="{archivo_orden}"')
        msg.attach(part1)

    if archivo_cliente is not None:
        part2 = MIMEBase('application', 'octet-stream')
        part2.set_payload(archivo_cliente.getvalue())
        encoders.encode_base64(part2)
        part2.add_header('Content-Disposition', f'attachment; filename="DISENO_{archivo_cliente.name}"')
        msg.attach(part2)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(me, password)
    server.send_message(msg)
    server.quit()

st.title("🏷️ Pedidos FlexyLabel")
with st.form("main_form"):
    col1, col2 = st.columns(2)
    with col1:
        cliente = st.text_input("Nombre del Cliente")
        referencia = st.text_input("Referencia (Diseño)")
        material = st.text_input("Material aproximado")
        fecha_entrega = st.date_input("Fecha de entrega", min_value=datetime.date.today())
    with col2:
        ancho = st.number_input("Ancho (mm)", min_value=1)
        largo = st.number_input("Largo (mm)", min_value=1)
        cantidad = st.number_input("Cantidad total", min_value=1, step=100)
        mandril = st.selectbox("Mandril", ["40mm", "76mm", "25mm"])
    
    salida_tipo = st.radio("Salida", ["Interior", "Exterior"], horizontal=True)
    sentido = st.select_slider("Sentido salida", options=["1", "2", "3", "4", "5", "6", "7", "8"])
    diseno_pdf = st.file_uploader("Adjuntar PDF", type=["pdf"])
    obs = st.text_area("Observaciones")
    enviar = st.form_submit_button("ENVIAR PEDIDO")

    if enviar:
        if not cliente or not diseno_pdf:
            st.error("Faltan datos obligatorios.")
        else:
            datos = {"cliente": cliente, "referencia": referencia, "material": material, "fecha_entrega": fecha_entrega, "ancho": ancho, "largo": largo, "cantidad": cantidad, "mandril": mandril, "salida_tipo": salida_tipo, "sentido": sentido, "obs": obs}
            try:
                pdf_orden = crear_pdf_tecnico(datos)
                enviar_email_completo(pdf_orden, diseno_pdf, datos)
                st.success("¡Enviado!")
            except Exception as e:
                st.error(f"Error técnico: {e}")
