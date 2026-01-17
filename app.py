import streamlit as st
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime

# --- FUNCIÓN PARA GENERAR EL PDF TÉCNICO ---
def crear_pdf(datos):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado corporativo
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="FLEXYLABEL IMPRESSORS S.L.", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Hoja de Planificación de Pedido / Presupuesto", ln=True, align='C')
    pdf.ln(10)

    # Bloque de Información del Cliente
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="1. DATOS DEL CLIENTE", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, txt=f"Empresa: {datos['empresa']}", ln=True)
    pdf.cell(0, 8, txt=f"Contacto: {datos['contacto']} | Email: {datos['email']}", ln=True)
    pdf.ln(5)

    # Bloque de Especificaciones Técnicas
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="2. PARÁMETROS DE LA ETIQUETA", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    
    # Tabla de medidas y sistema
    pdf.cell(95, 8, txt=f"Medidas: {datos['ancho']} x {datos['largo']} mm", border=1)
    pdf.cell(95, 8, txt=f"Sistema: {datos['sistema']}", border=1, ln=True)
    
    # Tabla de material y cantidad
    pdf.cell(95, 8, txt=f"Material: {datos['material']}", border=1)
    pdf.cell(95, 8, txt=f"Cantidad: {datos['cantidad']} uds.", border=1, ln=True)
    
    # Acabado
    pdf.cell(190, 8, txt=f"Acabado: {datos['acabado']}", border=1, ln=True)
    pdf.ln(5)

    # Observaciones
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="3. OBSERVACIONES DE PRODUCCIÓN", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 8, txt=datos['obs'])

    filename = f"Pedido_{datos['empresa'].replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename

# --- FUNCIÓN PARA ENVIAR EMAIL ---
def enviar_email(archivo, datos_cliente):
    # Cogemos los datos de configuración de "Secrets" (Paso 2 de la guía)
    me = st.secrets["email_usuario"]
    password = st.secrets["email_password"]
    receptor = "info@flexylabel.com" # Cambia esto por tu email real

    msg = MIMEMultipart()
    msg['Subject'] = f"NUEVA ORDEN: {datos_cliente}"
    msg['From'] = me
    msg['To'] = receptor

    cuerpo = f"Hola Iván,\n\nSe ha generado una nueva hoja de pedido desde la web.\nAdjunto enviamos el PDF con los parámetros técnicos de {datos_cliente}."
    msg.attach(MIMEText(cuerpo, 'plain'))

    with open(archivo, "rb") as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{archivo}"')
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(me, password)
    server.send_message(msg)
    server.quit()

# --- INTERFAZ WEB (STREAMLIT) ---
st.set_page_config(page_title="FlexyLabel - Pedidos", layout="centered")

st.image("https://via.placeholder.com/150x50?text=FLEXYLABEL", width=200) # Pon aquí tu logo real
st.title("Formulario de Pedido Técnico")

with st.form("form_flexy"):
    col1, col2 = st.columns(2)
    with col1:
        empresa = st.text_input("Nombre de la Empresa", placeholder="Ej: Vinos S.A.")
        email = st.text_input("Tu Email")
    with col2:
        contacto = st.text_input("Persona de contacto")
        sistema = st.selectbox("Sistema de Impresión", ["Flexografía", "Tipografía", "Offset", "Digital"])
    
    st.markdown("---")
    st.subheader("Especificaciones de la Etiqueta")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        ancho = st.number_input("Ancho (mm)", min_value=1)
    with c2:
        largo = st.number_input("Largo (mm)", min_value=1)
    with c3:
        cantidad = st.number_input("Cantidad total", min_value=100, step=100)
        
    material = st.selectbox("Tipo de Material", ["Papel Couché", "PP Blanco", "PP Transparente", "Térmico", "Papel Crema", "Especial"])
    acabado = st.text_input("Acabados (Barniz, Plastificado, Estampación...)", value="Ninguno")
    obs = st.text_area("Notas adicionales (Sentido de salida, diámetro mandril, etc.)")

    submit = st.form_submit_button("ENVIAR PEDIDO A PRODUCCIÓN")

    if submit:
        if not email or not empresa:
            st.warning("Por favor, rellena los campos de contacto.")
        else:
            datos = {
                "empresa": empresa, "email": email, "contacto": contacto,
                "sistema": sistema, "ancho": ancho, "largo": largo,
                "cantidad": cantidad, "material": material, "acabado": acabado, "obs": obs
            }
            try:
                archivo_pdf = crear_pdf(datos)
                enviar_email(archivo_pdf, empresa)
                st.success(f"¡Pedido de {empresa} enviado con éxito! El PDF ya está en tu bandeja de entrada, Iván.")
                st.balloons()
            except Exception as e:
                st.error(f"Hubo un error con el envío: {e}")
