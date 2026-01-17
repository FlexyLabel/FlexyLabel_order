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

# --- FUNCIÓN PARA GENERAR EL PDF TÉCNICO ---
def crear_pdf_tecnico(datos):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="FLEXYLABEL IMPRESSORS S.L. - ORDEN DE PRODUCCIÓN", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 7, txt=f"Generado el: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)

    # 1. DATOS DEL CLIENTE Y DISEÑO
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="1. INFORMACIÓN GENERAL", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, txt=f"Cliente: {datos['cliente']}", ln=True)
    pdf.cell(0, 8, txt=f"Referencia / Diseño: {datos['referencia']}", ln=True)
    pdf.cell(0, 8, txt=f"Fecha de entrega solicitada: {datos['fecha_entrega']}", ln=True)
    pdf.ln(5)

    # 2. ESPECIFICACIONES TÉCNICAS
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="2. PARÁMETROS TÉCNICOS", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    
    col_width = 95
    pdf.cell(col_width, 8, txt=f"Tamaño: {datos['ancho']} x {datos['largo']} mm", border=1)
    pdf.cell(col_width, 8, txt=f"Material: {datos['material']}", border=1, ln=True)
    
    pdf.cell(col_width, 8, txt=f"Salida: {datos['salida_tipo']}", border=1)
    pdf.cell(col_width, 8, txt=f"Sentido Bobinado: {datos['sentido']}", border=1, ln=True)
    
    pdf.cell(col_width, 8, txt=f"Mandril / Eje: {datos['mandril']}", border=1)
    pdf.cell(col_width, 8, txt=f"Cantidad: {datos['cantidad']} uds.", border=1, ln=True)
    pdf.ln(5)

    # 3. OBSERVACIONES
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="3. OBSERVACIONES ADICIONALES", ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 8, txt=datos['obs'])

    filename = f"Orden_{datos['referencia'].replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename

# --- FUNCIÓN PARA ENVIAR EMAIL CON ADJUNTOS ---
def enviar_email_completo(archivo_orden, archivo_cliente, datos_resumen):
    me = st.secrets["email_usuario"]
    password = st.secrets["email_password"]

    msg = MIMEMultipart()
    msg['Subject'] = f"Nuevo Pedido: {datos_resumen['referencia']} - {datos_resumen['cliente']}"
    msg['From'] = me
    msg['To'] = DESTINATARIO_FINAL

    cuerpo = f"""
    Nueva solicitud de trabajo para FlexyLabel:
    - Cliente: {datos_resumen['cliente']}
    - Referencia: {datos_resumen['referencia']}
    - Fecha Entrega: {datos_resumen['fecha_entrega']}
    
    Se adjunta la Hoja de Pedido Técnica y el archivo original del cliente.
    """
    msg.attach(MIMEText(cuerpo, 'plain'))

    # Adjunto 1: Hoja de Pedido PDF
    with open(archivo_orden, "rb") as f:
        part1 = MIMEBase('application', 'octet-stream')
        part1.set_payload(f.read())
        encoders.encode_base64(part1)
        part1.add_header('Content-Disposition', f'attachment; filename="{archivo_orden}"')
        msg.attach(part1)

    # Adjunto 2: PDF del Cliente
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

# --- INTERFAZ DE USUARIO ---
st.set_page_config(page_title="FlexyLabel Order System", layout="wide")

st.title("🏷️ Sistema de Pedidos FlexyLabel")
st.markdown("Complete los datos para generar la orden de producción.")

with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1:
        cliente = st.text_input("Nombre del Cliente")
        referencia = st.text_input("Referencia (Nombre del diseño)")
        material = st.text_input("Material aproximado (ej: PP Blanco, Couché...)")
        fecha_entrega = st.date_input("Fecha de entrega deseada", min_value=datetime.date.today())
        
    with c2:
        ancho = st.number_input("Ancho etiqueta (mm)", min_value=1)
        largo = st.number_input("Largo etiqueta (mm)", min_value=1)
        cantidad = st.number_input("Cantidad total de etiquetas", min_value=1, step=100)
        mandril = st.selectbox("Diámetro del Mandril / Eje", ["40mm", "76mm", "25mm", "Otros"])

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        salida_tipo = st.radio("Salida de impresión", ["Interior", "Exterior"], horizontal=True)
        sentido = st.select_slider("Sentido de salida (Posición bobinado)", options=["1", "2", "3", "4", "5", "6", "7", "8"])
        st.info("Sentido 1-4: Salida por pie. Sentido 5-8: Salida por cabeza/lateral.")
        
    with col_b:
        diseno_pdf = st.file_uploader("Adjuntar PDF del modelo", type=["pdf"])
        obs = st.text_area("Observaciones (Acabados, Barniz, Troquel...)")

    enviar = st.form_submit_button("ENVIAR PEDIDO A COVET@ETIQUETES.COM")

    if enviar:
        if not cliente or not referencia or not diseno_pdf:
            st.error("Iván, faltan datos críticos (Cliente, Referencia o el archivo PDF).")
        else:
            datos = {
                "cliente": cliente, "referencia": referencia, "material": material,
                "fecha_entrega": fecha_entrega, "ancho": ancho, "largo": largo,
                "cantidad": cantidad, "mandril": mandril, "salida_tipo": salida_tipo,
                "sentido": sentido, "obs": obs
            }
            
            with st.spinner("Procesando pedido técnico..."):
                try:
                    pdf_orden = crear_pdf_tecnico(datos)
                    enviar_email_completo(pdf_orden, diseno_pdf, datos)
                    st.success(f"¡Pedido de {cliente} enviado correctamente a covet@etiquetes.com!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error técnico: {e}")    pdf.cell(95, 8, txt=f"Medidas: {datos['ancho']} x {datos['largo']} mm", border=1)
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
