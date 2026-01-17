import streamlit as st
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# =============================================================================
# 1. ESTILO VISUAL (LETRAS BLANCAS Y HOVER SIN ROMPER TU LÓGICA)
# =============================================================================
st.set_page_config(page_title="FlexyLabel Order", layout="wide")

st.markdown("""
    <style>
        /* Fondo oscuro y letras blancas en toda la app */
        .stApp {
            background-color: #0b0e14;
            color: #ffffff !important;
        }
        
        /* Forzar etiquetas y títulos a blanco */
        label, p, h1, h2, h3, .stMarkdown {
            color: #ffffff !important;
        }

        /* EFECTO HOVER EN LOS CONTENEDORES */
        div[data-testid="stForm"], .st-emotion-cache-1r6slb0 {
            background: rgba(22, 27, 34, 0.9) !important;
            border: 1px solid #30363d !important;
            border-radius: 15px !important;
            transition: all 0.3s ease;
        }

        div[data-testid="stForm"]:hover {
            border-color: #58a6ff !important;
            box-shadow: 0 0 20px rgba(88, 166, 255, 0.2);
        }

        /* Imágenes laterales */
        .side-img {
            width: 100%;
            border-radius: 10px;
            margin-bottom: 15px;
            border: 1px solid #30363d;
        }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. TU LÓGICA ORIGINAL (CORREGIDA PARA EVITAR KEYERROR)
# =============================================================================

# Título
st.markdown("<h1 style='text-align: center;'>FLEXYLABEL ORDER</h1>", unsafe_allow_html=True)

# Columnas laterales con imágenes de flexografía
col_img_l, col_main, col_img_r = st.columns([1, 4, 1])

with col_img_l:
    st.image("https://images.unsplash.com/photo-1610473069150-13645396b270?w=400")
    st.image("https://images.unsplash.com/photo-1563089145-599997674d42?w=400")

with col_img_r:
    st.image("https://images.unsplash.com/photo-1590402494682-cd3fb53b1f71?w=400")
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400")

with col_main:
    with st.form("mi_formulario_original"):
        cliente = st.text_input("CLIENTE")
        email_usuario = st.text_input("TU EMAIL (PARA CONFIRMACIÓN)")
        
        col1, col2, col3 = st.columns(3)
        ancho = col1.number_input("ANCHO (mm)", value=100)
        largo = col2.number_input("LARGO (mm)", value=100)
        cantidad = col3.number_input("CANTIDAD", value=5000)
        
        material = st.selectbox("MATERIAL", ["PP Blanco", "Couché", "Térmico"])
        
        st.write("---")
        st.write("### CONFIGURACIÓN DE TALLER")
        st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", width=300)
        sentido = st.select_slider("SENTIDO DE SALIDA", options=[str(i) for i in range(1, 9)], value="3")
        
        archivo = st.file_uploader("SUBIR ARTE FINAL (PDF)", type=["pdf"])
        
        # EL BOTÓN
        enviado = st.form_submit_button("ENVIAR PEDIDO")

        if enviado:
            if not cliente or not archivo:
                st.error("Faltan datos obligatorios.")
            else:
                try:
                    # USAMOS TUS SECRETS EXACTAMENTE COMO LOS TENÍAS
                    remitente = st.secrets["email_usuario"]
                    password = st.secrets["email_password"]
                    
                    # Crear el mensaje
                    msg = MIMEMultipart()
                    msg['From'] = remitente
                    msg['To'] = f"covet@etiquetes.com, {email_usuario}"
                    msg['Subject'] = f"Nuevo Pedido: {cliente}"
                    
                    cuerpo = f"Pedido de {cliente}\nMaterial: {material}\nCantidad: {cantidad}"
                    msg.attach(MIMEText(cuerpo, 'plain'))
                    
                    # Adjuntar el archivo que subió el usuario
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(archivo.getvalue())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="AF_{cliente}.pdf"')
                    msg.attach(part)
                    
                    # Envío
                    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
                    server.login(remitente, password)
                    server.send_message(msg)
                    server.quit()
                    
                    st.success("¡Pedido enviado correctamente!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error al enviar: {e}")
