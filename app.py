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

# --- CONFIGURACIÓN DE LA APP ---
APP_TITLE = "Sistema de Pedidos Técnicos FlexyLabel"
DESTINATARIO_FINAL = "covet@etiquetes.com" # Tu correo de recepción final
LOGO_URL = "https://i.imgur.com/your-flexylabel-logo.png" # <--- ¡CAMBIA ESTO POR TU LOGO REAL!
DEFAULT_MIN_LABEL_SIZE = 1 # mm
DEFAULT_MAX_LABEL_SIZE = 500 # mm
DEFAULT_MIN_QUANTITY = 100 # unidades
DEFAULT_MAX_QUANTITY = 1000000 # unidades

# --- ESTILOS CSS PERSONALIZADOS (PARA UNA PÁGINA MÁS MODERNA) ---
# Hemos incorporado un CSS extenso para dar un look and feel profesional
def inject_custom_css():
    st.markdown("""
        <style>
            /* Fuentes y colores principales */
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
            :root {
                --primary-color: #004085; /* Azul oscuro corporativo de FlexyLabel */
                --secondary-color: #f8f9fa; /* Gris claro */
                --accent-color: #007bff; /* Azul brillante para detalles */
                --text-color: #333;
                --light-text-color: #6c757d;
                --border-color: #dee2e6;
                --success-color: #28a745;
                --error-color: #dc3545;
            }
            body {
                font-family: 'Roboto', sans-serif;
                color: var(--text-color);
                background-color: var(--secondary-color);
            }
            .stApp {
                background-color: var(--secondary-color);
            }

            /* Contenedor principal de la aplicación */
            .main .block-container {
                max-width: 1200px;
                padding-top: 2rem;
                padding-right: 2rem;
                padding-left: 2rem;
                padding-bottom: 2rem;
            }

            /* Títulos y subtítulos */
            h1, h2, h3, h4, h5, h6 {
                color: var(--primary-color);
                font-weight: 700;
                margin-bottom: 1rem;
            }
            h1 {
                font-size: 2.5rem;
                text-align: center;
                border-bottom: 2px solid var(--accent-color);
                padding-bottom: 1rem;
                margin-bottom: 2rem;
            }
            h2 {
                font-size: 1.8rem;
                margin-top: 2rem;
                color: var(--primary-color);
            }
            h3 {
                font-size: 1.4rem;
                color: var(--text-color);
            }

            /* Botones principales */
            .stButton>button {
                background-color: var(--primary-color);
                color: white;
                border-radius: 8px;
                padding: 0.75rem 1.5rem;
                font-size: 1.1rem;
                font-weight: 700;
                border: none;
                transition: background-color 0.3s ease, transform 0.2s ease;
                width: 100%;
                margin-top: 1.5rem;
            }
            .stButton>button:hover {
                background-color: var(--accent-color);
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            .stButton>button:active {
                background-color: var(--primary-color);
                transform: translateY(0);
            }

            /* Campos de entrada de texto, selección y números */
            .stTextInput>div>div>input,
            .stSelectbox>div>div>select,
            .stNumberInput>div>div>input,
            .stTextArea>div>div>textarea,
            .stDateInput>div>div>input {
                border: 1px solid var(--border-color);
                border-radius: 6px;
                padding: 0.75rem 1rem;
                background-color: white;
                transition: border-color 0.3s ease, box-shadow 0.3s ease;
            }
            .stTextInput>div>div>input:focus,
            .stSelectbox>div>div>select:focus,
            .stNumberInput>div>div>input:focus,
            .stTextArea>div>div>textarea:focus,
            .stDateInput>div>div>input:focus {
                border-color: var(--accent-color);
                box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
                outline: none;
            }
            label {
                font-weight: 600;
                color: var(--text-color);
                margin-bottom: 0.5rem;
                display: block;
            }

            /* File Uploader */
            .stFileUploader {
                border: 2px dashed var(--border-color);
                border-radius: 8px;
                padding: 1.5rem;
                text-align: center;
                background-color: white;
                transition: border-color 0.3s ease;
                margin-top: 1rem;
            }
            .stFileUploader:hover {
                border-color: var(--accent-color);
            }
            .stFileUploader > div > button {
                background-color: var(--accent-color);
                color: white;
                border-radius: 6px;
                padding: 0.5rem 1rem;
                font-size: 0.9rem;
            }
            .stFileUploader > div > button:hover {
                background-color: #0056b3;
            }

            /* Radio y Sliders */
            .stRadio > div, .stSelectSlider > div {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }
            .stRadio > div > label, .stSelectSlider > div > label {
                padding: 0.5rem 1rem;
                border: 1px solid var(--border-color);
                border-radius: 50px;
                background-color: white;
                cursor: pointer;
                transition: background-color 0.3s ease, border-color 0.3s ease;
            }
            .stRadio > div > label:hover, .stSelectSlider > div > label:hover {
                background-color: var(--secondary-color);
                border-color: var(--accent-color);
            }
            .stRadio > div > label[data-checked="true"], .stSelectSlider > div > label[data-checked="true"] {
                background-color: var(--primary-color);
                color: white;
                border-color: var(--primary-color);
            }
            .stRadio > div > label[data-checked="true"] > div > input, .stSelectSlider > div > label[data-checked="true"] > div > input {
                background-color: white; /* para ocultar el radio/slider nativo */
            }


            /* Mensajes de feedback (éxito, error, advertencia) */
            .stAlert {
                border-radius: 8px;
                padding: 1rem 1.5rem;
                margin-bottom: 1.5rem;
                font-weight: 500;
            }
            .stAlert.success {
                background-color: #d4edda;
                color: var(--success-color);
                border-left: 5px solid var(--success-color);
            }
            .stAlert.error {
                background-color: #f8d7da;
                color: var(--error-color);
                border-left: 5px solid var(--error-color);
            }
            .stAlert.warning {
                background-color: #fff3cd;
                color: #856404;
                border-left: 5px solid #ffc107;
            }
            .stAlert.info {
                background-color: #d1ecf1;
                color: #0c5460;
                border-left: 5px solid #17a2b8;
            }

            /* Contenedores de secciones (card-like) */
            .stExpander, .stForm {
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                padding: 1.5rem 2rem;
                margin-bottom: 2rem;
            }
            .stExpander > div > div > p {
                font-weight: 600;
                color: var(--primary-color);
                font-size: 1.2rem;
            }
            .stExpander > div > div > svg {
                color: var(--primary-color);
                font-size: 1.5rem;
            }
            .stForm > div:first-child { /* Título del formulario */
                font-size: 1.8rem;
                font-weight: 700;
                color: var(--primary-color);
                margin-bottom: 1.5rem;
                text-align: center;
            }

            /* Columnas */
            .st-bk { /* st.columns inner div */
                padding: 0 10px;
            }
            
            /* Logo */
            .stImage img {
                display: block;
                margin-left: auto;
                margin-right: auto;
                max-width: 250px;
                margin-bottom: 2rem;
            }

            /* Spinners y progreso */
            .stSpinner > div > div {
                color: var(--primary-color);
            }
            .stProgress > div > div:first-child {
                background-color: var(--border-color);
            }
            .stProgress > div > div:first-child > div {
                background-color: var(--accent-color);
            }
            
            /* Animación de carga */
            .loader {
                border: 6px solid #f3f3f3;
                border-top: 6px solid var(--primary-color);
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

        </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN PARA GENERAR EL PDF TÉCNICO ---
def crear_pdf_tecnico(datos):
    pdf = FPDF()
    pdf.add_page()
    
    # Fuentes y colores
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_fill_color(220, 230, 240) # Azul claro para fondos
    pdf.set_text_color(50, 50, 50) # Gris oscuro para texto

    # Logo (si existe) y Encabezado
    if LOGO_URL and LOGO_URL != "https://i.imgur.com/your-flexylabel-logo.png":
        try:
            # Descargar el logo temporalmente
            import requests
            response = requests.get(LOGO_URL)
            if response.status_code == 200:
                with open("logo_temp.png", "wb") as f:
                    f.write(response.content)
                pdf.image("logo_temp.png", 10, 8, 40) # x, y, ancho
                os.remove("logo_temp.png") # Eliminar después de usar
            else:
                st.warning("No se pudo cargar el logo desde la URL.")
        except Exception as e:
            st.warning(f"Error al cargar el logo: {e}")

    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, txt="FLEXSYLABEL IMPRESSORS S.L.", ln=True, align='R')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 7, txt="Hoja de Orden de Producción Técnica", ln=True, align='R')
    pdf.ln(5)
    pdf.set_font("Arial", size=9)
    pdf.cell(0, 5, txt=f"Generado el: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='R')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Línea separadora
    pdf.ln(10)

    # 1. INFORMACIÓN GENERAL
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="1. INFORMACIÓN GENERAL DEL PEDIDO", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 7, txt=f"Cliente: {datos['cliente']}", ln=True)
    pdf.cell(0, 7, txt=f"Contacto Email: {datos['email_cliente']}", ln=True)
    pdf.cell(0, 7, txt=f"Referencia / Diseño: {datos['referencia']}", ln=True)
    pdf.cell(0, 7, txt=f"Fecha de Entrega Deseada: {datos['fecha_entrega'].strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(7)

    # 2. ESPECIFICACIONES TÉCNICAS DE LA ETIQUETA
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="2. ESPECIFICACIONES TÉCNICAS", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    
    # Usar una tabla para mejor formato
    pdf.set_draw_color(180, 180, 180) # Color de borde de tabla
    col_widths = [60, 40, 50, 40] # Ancho de las columnas

    # Fila de encabezados de tabla (opcional)
    # pdf.set_font("Arial", 'B', 10)
    # pdf.cell(col_widths[0], 7, "Parámetro", 1, 0, 'C', 1)
    # pdf.cell(col_widths[1], 7, "Valor", 1, 0, 'C', 1)
    # pdf.cell(col_widths[2], 7, "Parámetro", 1, 0, 'C', 1)
    # pdf.cell(col_widths[3], 7, "Valor", 1, 1, 'C', 1) # Nueva línea

    pdf.set_font("Arial", size=10)
    
    # Fila 1
    pdf.cell(col_widths[0], 7, "Ancho Etiqueta:", 'LRB')
    pdf.cell(col_widths[1], 7, f"{datos['ancho']} mm", 'RB', 0, 'C')
    pdf.cell(col_widths[2], 7, "Largo Etiqueta:", 'LRB')
    pdf.cell(col_widths[3], 7, f"{datos['largo']} mm", 'RB', 1, 'C') # 1 = nueva línea
    
    # Fila 2
    pdf.cell(col_widths[0], 7, "Cantidad Total:", 'LRB')
    pdf.cell(col_widths[1], 7, f"{datos['cantidad']} uds.", 'RB', 0, 'C')
    pdf.cell(col_widths[2], 7, "Material:", 'LRB')
    pdf.cell(col_widths[3], 7, datos['material'], 'RB', 1, 'C')
    
    # Fila 3
    pdf.cell(col_widths[0], 7, "Sistema Impresión:", 'LRB')
    pdf.cell(col_widths[1], 7, datos['sistema'], 'RB', 0, 'C')
    pdf.cell(col_widths[2], 7, "Acabados:", 'LRB')
    pdf.cell(col_widths[3], 7, datos['acabado'], 'RB', 1, 'C')
    
    # Fila 4
    pdf.cell(col_widths[0], 7, "Tipo Salida Bobina:", 'LRB')
    pdf.cell(col_widths[1], 7, datos['salida_tipo'], 'RB', 0, 'C')
    pdf.cell(col_widths[2], 7, "Sentido Bobinado:", 'LRB')
    pdf.cell(col_widths[3], 7, f"Posición {datos['sentido']}", 'RB', 1, 'C')
    
    # Fila 5
    pdf.cell(col_widths[0], 7, "Mandril / Eje:", 'LRB')
    pdf.cell(col_widths[1], 7, datos['mandril'], 'RB', 0, 'C')
    pdf.cell(col_widths[2], 7, "No. Colores:", 'LRB')
    pdf.cell(col_widths[3], 7, datos['colores'], 'RB', 1, 'C')

    pdf.ln(7)

    # 3. OBSERVACIONES ADICIONALES
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="3. OBSERVACIONES / DETALLES ADICIONALES", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, txt=datos['obs'])
    pdf.ln(7)

    # Pie de página (ej. datos de FlexyLabel)
    pdf.set_y(-25) # Posición a 25mm del final
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 5, "FlexyLabel Impressors S.L. - Su socio en impresión de etiquetas", 0, 1, 'C')
    pdf.cell(0, 5, "C/ Ejemplo, 123 - 08000 Barcelona - info@flexylabel.com", 0, 1, 'C')


    filename = f"ORDEN_FLEXYLABEL_{datos['referencia'].replace(' ', '_').upper()}.pdf"
    pdf.output(filename)
    return filename

# --- FUNCIÓN PARA ENVIAR EMAIL CON ADJUNTOS ---
def enviar_email_completo(archivo_orden_pdf_path, archivo_cliente_uploaded, datos_resumen):
    try:
        email_emisor = st.secrets["email_usuario"]
        email_password = st.secrets["email_password"]
    except KeyError:
        st.error("Error de configuración: Las credenciales de email no están configuradas en Streamlit Secrets. Contacte al administrador.")
        return

    msg = MIMEMultipart()
    msg['Subject'] = f"NUEVO PEDIDO DE PRODUCCIÓN: {datos_resumen['referencia']} ({datos_resumen['cliente']})"
    msg['From'] = email_emisor
    msg['To'] = DESTINATARIO_FINAL
    msg['Reply-To'] = datos_resumen['email_cliente'] # Para que puedas responder directamente al cliente

    cuerpo = f"""
    Estimado equipo de FlexyLabel,

    Se ha recibido una nueva solicitud de pedido a través del sistema web.
    A continuación, un resumen de la orden:

    --------------------------------------------------
    Cliente:           {datos_resumen['cliente']}
    Referencia/Diseño: {datos_resumen['referencia']}
    Email Contacto:    {datos_resumen['email_cliente']}
    Fecha Entrega Sol.:{datos_resumen['fecha_entrega'].strftime('%d/%m/%Y')}
    --------------------------------------------------

    Se adjuntan dos documentos importantes:
    1.  La 'Orden de Producción Técnica' generada automáticamente en PDF.
    2.  El archivo de diseño original (PDF) proporcionado por el cliente.

    Por favor, revisen ambos documentos para proceder con la planificación.

    Saludos cordiales,

    Sistema Automático de Pedidos FlexyLabel
    """
    msg.attach(MIMEText(cuerpo, 'plain'))

    # Adjunto 1: Hoja de Pedido PDF GENERADO
    with open(archivo_orden_pdf_path, "rb") as f:
        part1 = MIMEBase('application', 'octet-stream')
        part1.set_payload(f.read())
        encoders.encode_base64(part1)
        part1.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(archivo_orden_pdf_path)}"')
        msg.attach(part1)

    # Adjunto 2: PDF del Cliente SUBIDO
    if archivo_cliente_uploaded is not None:
        part2 = MIMEBase('application', 'octet-stream')
        part2.set_payload(archivo_cliente_uploaded.getvalue())
        encoders.encode_base64(part2)
        part2.add_header('Content-Disposition', f'attachment; filename="DISEÑO_CLIENTE_{archivo_cliente_uploaded.name}"')
        msg.attach(part2)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_emisor, email_password)
    server.send_message(msg)
    server.quit()

# --- INTERFAZ DE USUARIO CON STREAMLIT ---
# Inyectar CSS al inicio
inject_custom_css()

st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="collapsed")

# Header con logo y título
st.image(LOGO_URL, use_column_width=False, output_format="PNG") # Ajusta el use_column_width si el logo es pequeño
st.title(APP_TITLE)
st.markdown("###  Rellene el siguiente formulario para generar una **orden de producción** o solicitar un **presupuesto técnico**.")

st.info("💡 **Importante:** Asegúrese de adjuntar el PDF final del diseño para agilizar el proceso de pre-impresión.", icon="ℹ️")

with st.form("flexylabel_order_form", clear_on_submit=True):
    # --- SECCIÓN 1: DATOS DEL CLIENTE Y GENERALES ---
    st.subheader("📝 1. Información General del Pedido")
    with st.expander("Haz click para expandir/colapsar"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cliente = st.text_input("Nombre de la Empresa Cliente", help="Nombre completo de la empresa que realiza el pedido.")
            referencia = st.text_input("Referencia o Nombre del Diseño", help="Nombre descriptivo del diseño de la etiqueta (ej: 'Etiqueta Vino Reserva', 'Logo Aceite Oliva').")
            
        with col_c2:
            email_cliente = st.text_input("Email de Contacto del Cliente", help="Correo electrónico para cualquier consulta sobre el pedido.")
            fecha_entrega = st.date_input("Fecha de Entrega Deseada", min_value=datetime.date.today(), help="Seleccione la fecha límite para la entrega del pedido.")
        
    st.markdown("---")

    # --- SECCIÓN 2: ESPECIFICACIONES DE LA ETIQUETA ---
    st.subheader("📏 2. Dimensiones y Características de la Etiqueta")
    with st.expander("Haz click para expandir/colapsar"):
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            ancho = st.number_input(f"Ancho de la Etiqueta (mm)", min_value=DEFAULT_MIN_LABEL_SIZE, max_value=DEFAULT_MAX_LABEL_SIZE, value=50, step=1, help="Medida del ancho de la etiqueta en milímetros.")
            largo = st.number_input(f"Largo de la Etiqueta (mm)", min_value=DEFAULT_MIN_LABEL_SIZE, max_value=DEFAULT_MAX_LABEL_SIZE, value=80, step=1, help="Medida del largo o altura de la etiqueta en milímetros.")
        with col_d2:
            cantidad = st.number_input(f"Cantidad Total de Etiquetas (uds)", min_value=DEFAULT_MIN_QUANTITY, max_value=DEFAULT_MAX_QUANTITY, value=1000, step=500, help="Número total de etiquetas requeridas.")
            material = st.selectbox("Material Aproximado", 
                                    ["Papel Couché Adhesivo", "PP Blanco Adhesivo", "PP Transparente Adhesivo", 
                                     "Térmico Directo", "Térmico Protegido", "Papel Texturado/Verjurado", 
                                     "Cartulina (sin adhesivo)", "Otros (Especificar en observaciones)"],
                                    help="Seleccione el tipo de material base.")
        with col_d3:
            sistema = st.selectbox("Sistema de Impresión Preferido",
                                   ["Flexografía", "Offset", "Digital (toner)", "Digital (inkjet)", "Serigrafía", "Tipografía", "No lo sé / Asesoramiento"],
                                   help="Indique el sistema de impresión si lo conoce. Si no, seleccionaremos el más adecuado.")
            acabado = st.text_input("Acabados Adicionales (Barniz, Laminado, Stamping, Relieve...)", value="Ninguno", help="Especifique cualquier acabado especial (ej: 'Barniz Brillo UV', 'Laminado Mate', 'Stamping Oro').")
            colores = st.text_input("Número o Tipo de Colores", value="Cuatricromía (CMYK)", help="Ej: 'Cuatricromía', 'Pantone 286C + Negro', '2 tintas planas'.")

    st.markdown("---")

    # --- SECCIÓN 3: DETALLES DE PRODUCCIÓN Y ADJUNTOS ---
    st.subheader("⚙️ 3. Detalles de Producción y Archivos")
    with st.expander("Haz click para expandir/colapsar"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("### Salida de Etiqueta en Bobina")
            salida_tipo = st.radio("Orientación de la bobina", ["Interior (Etiqueta dentro del rollo)", "Exterior (Etiqueta fuera del rollo)"], horizontal=True, help="Indica si el bobinado va con la cara impresa hacia dentro o hacia fuera.")
            sentido = st.select_slider("Sentido de Bobinado (Posición de Salida)", 
                                       options=["1", "2", "3", "4", "5", "6", "7", "8"], 
                                       value="3", 
                                       help="Seleccione la posición de la etiqueta en la bobina (Ver gráfico de sentido de bobinado).")
            # --- Aquí podrías añadir una imagen para los sentidos ---
            st.markdown("Puedes consultar un gráfico de los [sentidos de bobinado aquí](https://ejemplo.com/grafico-bobinado.png)") # <--- CAMBIA ESTO POR UN ENLACE A TU GRAFICO
            mandril = st.selectbox("Diámetro del Mandril / Eje (mm)", ["25mm", "40mm", "76mm (3 pulgadas)", "152mm (6 pulgadas)", "Otros"], help="Diámetro interior del canuto de la bobina.")

        with col_p2:
            st.markdown("### Archivo de Diseño")
            diseno_pdf = st.file_uploader("Adjuntar PDF del Modelo a Imprimir (¡Obligatorio!)", type=["pdf"], help="Suba el archivo PDF final de su diseño. Asegúrese de que sea una versión de alta resolución y lista para imprenta.")
            
            st.markdown("### Observaciones Adicionales")
            obs = st.text_area("Cualquier otro detalle importante...", height=150, help="Aquí puede añadir cualquier otra información relevante para la producción: tipo de troquel especial, adhesivo particular, pruebas de color, etc.")

    st.markdown("---")

    # --- BOTÓN DE ENVÍO ---
    st.markdown("<br>", unsafe_allow_html=True) # Espacio extra
    enviar = st.form_submit_button("ENVIAR ORDEN A FLEXYLABEL")

    if enviar:
        # Validaciones básicas de campos obligatorios
        if not cliente:
            st.error("El campo 'Nombre de la Empresa Cliente' es obligatorio.")
            st.stop()
        if not referencia:
            st.error("El campo 'Referencia o Nombre del Diseño' es obligatorio.")
            st.stop()
        if not email_cliente:
            st.error("El campo 'Email de Contacto del Cliente' es obligatorio.")
            st.stop()
        if not diseno_pdf:
            st.error("Es obligatorio adjuntar el 'PDF del Modelo a Imprimir'.")
            st.stop()

        # Recopilar todos los datos
        datos = {
            "cliente": cliente,
            "referencia": referencia,
            "email_cliente": email_cliente,
            "fecha_entrega": fecha_entrega,
            "ancho": ancho,
            "largo": largo,
            "cantidad": cantidad,
            "material": material,
            "sistema": sistema,
            "acabado": acabado,
            "colores": colores,
            "salida_tipo": salida_tipo,
            "sentido": sentido,
            "mandril": mandril,
            "obs": obs
        }
        
        # Simulación de progreso
        progress_text = "Enviando solicitud y generando PDF..."
        my_bar = st.progress(0, text=progress_text)

        try:
            for percent_complete in range(100):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text=progress_text)
            
            # --- Lógica de generación y envío ---
            pdf_orden_path = crear_pdf_tecnico(datos)
            enviar_email_completo(pdf_orden_path, diseno_pdf, datos)
            
            my_bar.empty() # Borra la barra de progreso
            st.success(f"🎉 ¡Orden de Producción de **{cliente} - {referencia}** enviada con éxito a {DESTINATARIO_FINAL}!")
            st.balloons() # Animación de globos
            
            # Limpiar el archivo PDF temporal
            if os.path.exists(pdf_orden_path):
                os.remove(pdf_orden_path)

        except Exception as e:
