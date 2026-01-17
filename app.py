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

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO INDUSTRIAL (DARK MODE)
# =============================================================================
st.set_page_config(
    page_title="FLEXYLABEL ORDER v4.5 | Production System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def apply_industrial_design():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono&display=swap');

            /* Fondo Oscuro y Tipografía */
            .stApp {
                background-color: #0d1117;
                color: #ffffff !important;
                font-family: 'Inter', sans-serif;
            }

            /* Títulos y Labels en Blanco */
            h1, h2, h3, label, p, span {
                color: #ffffff !important;
                font-family: 'Inter', sans-serif !important;
            }

            /* RECUADROS BLANCOS CON LETRAS NEGRAS (LEGIILIDAD MÁXIMA) */
            input, select, textarea, div[data-baseweb="input"] input, .stSelectbox div {
                color: #000000 !important;
                background-color: #ffffff !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                border: none !important;
            }

            /* Ajuste para que el texto escrito no sea blanco sobre blanco */
            .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
                color: #000000 !important;
                background-color: #ffffff !important;
            }

            /* Contenedor del Formulario */
            div[data-testid="stForm"] {
                background-color: #161b22 !important;
                border: 1px solid #30363d !important;
                border-radius: 20px !important;
                padding: 3.5rem !important;
                box-shadow: 0 15px 50px rgba(0,0,0,0.7) !important;
            }

            /* Botón de Lanzamiento Industrial */
            .stButton button {
                background: linear-gradient(90deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: #ffffff !important;
                height: 4.5rem !important;
                border-radius: 12px !important;
                font-weight: 800 !important;
                font-size: 1.4rem !important;
                text-transform: uppercase;
                letter-spacing: 2px;
                border: none !important;
                width: 100% !important;
                margin-top: 2rem;
                transition: 0.4s all;
            }
            .stButton button:hover {
                transform: scale(1.02);
                box-shadow: 0 0 40px rgba(88, 166, 255, 0.5) !important;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. MOTOR DE GENERACIÓN DE PDF PROFESIONAL (PDF_Taller)
# =============================================================================
class PDF_Industrial(FPDF):
    def header(self):
        # Cabecera Técnica
        self.set_fill_color(22, 27, 34)
        self.rect(0, 0, 210, 45, 'F')
        self.set_xy(10, 15)
        self.set_font('Arial', 'B', 24)
        self.set_text_color(88, 166, 255)
        self.cell(0, 10, 'FLEXYLABEL // HOJA DE PRODUCCION', ln=True)
        self.set_font('Arial', '', 10)
        self.set_text_color(180, 180, 180)
        fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 8, f'ID Sistema: PRO-2026-V4 | Fecha Generacion: {fecha}', ln=True)
        self.ln(12)

    def seccion_titulo(self, titulo):
        self.set_fill_color(48, 54, 61)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'  {titulo}', ln=True, fill=True)
        self.ln(4)

    def fila_datos(self, label, valor, label2="", valor2=""):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(40, 40, 40)
        self.cell(40, 8, f"{label}:", 0)
        self.set_font('Arial', '', 10)
        self.cell(55, 8, f"{valor}", 0)
        if label2:
            self.set_font('Arial', 'B', 10)
            self.cell(40, 8, f"{label2}:", 0)
            self.set_font('Arial', '', 10)
            self.cell(0, 8, f"{valor2}", 0)
        self.ln(8)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, 'Documento de fabricacion oficial. FlexyLabel Cloud Systems.', 0, 0, 'C')

# =============================================================================
# 3. LÓGICA DE CÁLCULO Y ENVÍO DUAL
# =============================================================================
def enviar_orden_dual(pdf_file, af_file, datos):
    try:
        user = st.secrets["email_usuario"]
        pwd = st.secrets["email_password"]

        # --- EMAIL TALLER ---
        msg_t = MIMEMultipart()
        msg_t['From'] = user
        msg_t['To'] = "covet@etiquetes.com"
        msg_t['Subject'] = f"🟢 NUEVA ORDEN: {datos['cliente']} | REF: {datos['ref']}"
        msg_t.attach(MIMEText(f"Ficha técnica generada para el pedido {datos['ref']}.", 'plain'))

        # --- EMAIL CLIENTE (Cortesía e Imagen de Marca) ---
        msg_c = MIMEMultipart()
        msg_c['From'] = user
        msg_c['To'] = datos['email_c']
        msg_c['Subject'] = f"Confirmacion de Pedido - FlexyLabel Order"
        cuerpo_c = f"""
        Hola {datos['cliente']},

        Hemos recibido correctamente tu pedido de etiquetas. Muchas gracias por confiar en nosotros para la fabricacion de tus etiquetas autoadhesivas.
        
        Nuestro equipo de taller ya tiene la ficha tecnica y el diseño original en cola de produccion.
        
        Referencia registrada: {datos['ref']}
        Material: {datos['material']}
        
        Te avisaremos en cuanto el pedido salga de nuestras instalaciones.
        
        Un cordial saludo,
        El equipo de FlexyLabel.
        """
        msg_c.attach(MIMEText(cuerpo_c, 'plain'))

        # Adjuntar archivos
        with open(pdf_file, "rb") as f:
            data_pdf = f.read()
            for m in [msg_t, msg_c]:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(data_pdf)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="FICHA_TECNICA_{datos["ref"]}.pdf"')
                m.attach(part)

        # Arte Final solo al taller
        part_af = MIMEBase('application', 'octet-stream')
        part_af.set_payload(af_file.getvalue())
        encoders.encode_base64(part_af)
        part_af.add_header('Content-Disposition', f'attachment; filename="ARTE_FINAL_{datos["ref"]}.pdf"')
        msg_t.attach(part_af)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(user, pwd)
        server.send_message(msg_t)
        server.send_message(msg_c)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error en el servidor de correo: {e}")
        return False

# =============================================================================
# 4. APLICACIÓN PRINCIPAL (INTEGRACIÓN TOTAL)
# =============================================================================
apply_industrial_design()

st.markdown("<h1 style='text-align:center; font-size:3.5rem; letter-spacing:-2px;'>FLEXYLABEL ORDER</h1>", unsafe_allow_html=True)

COL_L, COL_M, COL_R = st.columns([1, 4, 1])

# Galería lateral industrial
with COL_L:
    st.image("https://images.unsplash.com/photo-1610473069150-13645396b270?w=400")
    st.image("https://images.unsplash.com/photo-1563089145-599997674d42?w=400")

with COL_R:
    st.image("https://images.unsplash.com/photo-1590402494682-cd3fb53b1f71?w=400")
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400")

with COL_M:
    with st.form("main_form_v4"):
        st.write("### 🏢 DATOS COMERCIALES")
        c1, c2, c3 = st.columns([2, 2, 1])
        cliente = c1.text_input("NOMBRE DEL CLIENTE / EMPRESA")
        email_cliente = c2.text_input("EMAIL DE CONFIRMACIÓN")
        referencia = c3.text_input("REF.", value="ORD-01")

        st.write("### 📐 FICHA TÉCNICA")
        c4, c5, c6 = st.columns(3)
        ancho = c4.number_input("ANCHO (mm)", 10, 500, 100)
        largo = c5.number_input("LARGO (mm)", 10, 500, 100)
        cantidad = c6.number_input("CANTIDAD TOTAL", 100, 1000000, 5000)

        c7, c8, c9 = st.columns(3)
        material = c7.selectbox("SOPORTE", ["PP Blanco", "PP Transparente", "Couché", "Térmico", "Verjurado"])
        mandril = c8.selectbox("MANDRIL", ["76mm", "40mm", "25mm"])
        etq_rollo = c9.number_input("ETIQUETAS / ROLLO", 100, 10000, 1000)

        st.write("---")
        st.write("### ⚙️ SENTIDO DE BOBINADO (POSICIÓN)")
        
        # ESQUEMA DE REFERENCIA PARA EL USUARIO
        st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", caption="Esquema General de Sentidos de Salida")
        

        sentido_val = st.select_slider("DESLIZA PARA SELECCIONAR LA SALIDA (1-8)", options=[str(i) for i in range(1, 9)], value="3")
        
        # VISUALIZACIÓN DINÁMICA: Muestra solo la imagen seleccionada (Confirmación visual)
        st.markdown(f"**Confirmación visual seleccionada: Posición {sentido_val}**")
        st.image(f"https://dummyimage.com/600x250/1f6feb/ffffff.png&text=SENTIDO+DE+SALIDA+{sentido_val}", width=500)

        st.write("### 📂 PRODUCCIÓN Y ARTE FINAL")
        c10, c11 = st.columns([1, 1])
        with c10:
            archivo_pdf = st.file_uploader("SUBIR ARTE FINAL (PDF)", type=["pdf"])
        with c11:
            notas = st.text_area("OBSERVACIONES TÉCNICAS (Tintas, Troquel...)")

        # Cálculo de metros lineales (ml)
        ml_est = (cantidad * (largo + 3)) / 1000
        st.info(f"💡 El sistema estima un consumo de {round(ml_est, 2)} metros lineales de material.")

        # PROCESAMIENTO
        if st.form_submit_button("🚀 LANZAR ORDEN DE PRODUCCIÓN"):
            if not cliente or not archivo_pdf or not email_cliente:
                st.error("Iván, no puedo procesar la orden sin Cliente, Email o PDF del diseño.")
            else:
                # 1. Generar Ficha Técnica PDF
                pdf = PDF_Industrial()
                pdf.add_page()
                pdf.seccion_titulo("DATOS DEL CLIENTE")
                pdf.fila_datos("Cliente", cliente, "Referencia", referencia)
                pdf.fila_datos("Email", email_cliente)
                
                pdf.seccion_titulo("ESPECIFICACIONES DE PRODUCTO")
                pdf.fila_datos("Medida", f"{ancho} x {largo} mm", "Cantidad", f"{cantidad} uds")
                pdf.fila_datos("Material", material, "Etiq/Rollo", etq_rollo)
                
                pdf.seccion_titulo("PARÁMETROS DE TALLER")
                pdf.fila_datos("Sentido Salida", sentido_val, "Mandril", mandril)
                pdf.fila_datos("Metros Lineales", f"{round(ml_est, 2)} m")
                
                if notas:
                    pdf.seccion_titulo("NOTAS DE PRODUCCIÓN")
                    pdf.set_font("Arial", "", 10)
                    pdf.multi_cell(0, 8, notas)

                temp_name = f"Ficha_{referencia}.pdf"
                pdf.output(temp_name)

                # 2. Ejecutar Envíos
                datos_envio = {
                    "cliente": cliente, "email_c": email_cliente, 
                    "material": material, "ref": referencia, "cantidad": cantidad
                }

                with st.spinner("Conectando con el servidor de taller..."):
                    if enviar_orden_dual(temp_name, archivo_pdf, datos_envio):
                        st.success(f"ORDEN ENVIADA: Taller y Cliente ({email_cliente}) notificados.")
                        st.balloons()
                        if os.path.exists(temp_name): os.remove(temp_name)

st.markdown("<p style='text-align:center; color:#30363d; font-size:0.8rem; margin-top:5rem;'>FLEXYLABEL INDUSTRIAL SOFTWARE v4.5 // 2026</p>", unsafe_allow_html=True)
