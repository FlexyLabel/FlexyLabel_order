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

# =============================================================================
# 1. CONFIGURACIÓN E INTERFAZ DARK PROFESIONAL
# =============================================================================
st.set_page_config(
    page_title="FlexyLabel Order | Gestión Industrial",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def inject_dark_industrial_ui():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

            /* Fondo Oscuro Principal */
            .stApp {
                background-color: #0d1117;
                color: #ffffff !important;
                font-family: 'Inter', sans-serif;
            }

            /* Forzar etiquetas a blanco */
            label, p, h1, h2, h3, span {
                color: #ffffff !important;
                font-family: 'Inter', sans-serif !important;
                font-weight: 600;
            }

            .main-header {
                text-align: center;
                padding: 3rem;
                background: linear-gradient(180deg, #161b22 0%, transparent 100%);
                border-bottom: 1px solid #30363d;
                margin-bottom: 2rem;
            }

            /* Contenedores de Formulario (Dark Elevation) */
            div[data-testid="stForm"] {
                background-color: #161b22 !important;
                border: 1px solid #30363d !important;
                border-radius: 16px !important;
                padding: 3rem !important;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
                transition: transform 0.3s ease, border-color 0.3s ease;
            }

            div[data-testid="stForm"]:hover {
                border-color: #58a6ff !important;
                transform: translateY(-2px);
            }

            /* CONFIGURACIÓN DE INPUTS: Fondo claro para lectura fácil al escribir */
            input, select, textarea {
                color: #0d1117 !important; /* Texto oscuro al escribir */
                background-color: #f0f6fc !important; /* Fondo claro en el input */
                border-radius: 8px !important;
                border: none !important;
                font-weight: 500 !important;
            }

            /* Botón de Producción */
            .stButton button {
                background: linear-gradient(90deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: #ffffff !important;
                height: 4rem !important;
                border-radius: 12px !important;
                font-weight: 700 !important;
                font-size: 1.2rem !important;
                text-transform: uppercase;
                letter-spacing: 1px;
                border: none !important;
                margin-top: 2rem !important;
                width: 100% !important;
                transition: 0.4s all !important;
            }

            .stButton button:hover {
                box-shadow: 0 0 25px rgba(88, 166, 255, 0.4) !important;
                filter: brightness(1.1);
            }

            /* Paneles Laterales */
            .side-img {
                border-radius: 12px;
                border: 1px solid #30363d;
                margin-bottom: 20px;
                transition: 0.5s;
            }
            .side-img:hover {
                border-color: #58a6ff;
                transform: scale(1.02);
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. MOTOR DE GENERACIÓN DE FICHA TÉCNICA (PDF)
# =============================================================================
class PDF_Taller(FPDF):
    def header(self):
        self.set_fill_color(22, 27, 34)
        self.rect(0, 0, 210, 40, 'F')
        self.set_xy(10, 15)
        self.set_font('Arial', 'B', 22)
        self.set_text_color(88, 166, 255)
        self.cell(0, 10, 'FLEXYLABEL // FICHA DE TALLER', ln=True)
        self.set_font('Arial', '', 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f'Generado: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True)
        self.ln(15)

    def seccion(self, titulo):
        self.ln(5)
        self.set_fill_color(48, 54, 61)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"  {titulo}", ln=True, fill=True)
        self.ln(4)

    def campo(self, label, valor, label2="", valor2=""):
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

# =============================================================================
# 3. LÓGICA DE ENVÍO (DOBLE NOTIFICACIÓN)
# =============================================================================
def enviar_pedidos_duales(archivo_pdf, arte_final, datos):
    try:
        remitente = st.secrets["email_usuario"]
        password = st.secrets["email_password"]

        # --- CORREO AL TALLER ---
        msg_taller = MIMEMultipart()
        msg_taller['From'] = remitente
        msg_taller['To'] = "covet@etiquetes.com"
        msg_taller['Subject'] = f"🚀 PRODUCCIÓN: {datos['cliente']} | {datos['ref']}"
        cuerpo_t = f"Nueva orden registrada.\nCliente: {datos['cliente']}\nMaterial: {datos['material']}"
        msg_taller.attach(MIMEText(cuerpo_t, 'plain'))

        # --- CORREO AL CLIENTE (MENSAJE DE CORTESÍA) ---
        msg_cliente = MIMEMultipart()
        msg_cliente['From'] = remitente
        msg_cliente['To'] = datos['email_c']
        msg_cliente['Subject'] = "Confirmación de Pedido - FlexyLabel Order"
        cuerpo_c = f"""
        Hola {datos['cliente']},

        Hemos recibido correctamente tu pedido de etiquetas en nuestro sistema. 
        Nuestro equipo de taller ya tiene la ficha técnica y el diseño para empezar a trabajar.

        Gracias por confiar en FlexyLabel, estamos encantados de trabajar contigo.
        Referencia del pedido: {datos['ref']}

        Un saludo,
        El equipo de FlexyLabel.
        """
        msg_cliente.attach(MIMEText(cuerpo_c, 'plain'))

        # Adjuntos comunes
        with open(archivo_pdf, "rb") as f:
            contenido_pdf = f.read()
            for m in [msg_taller, msg_cliente]:
                p = MIMEBase('application', 'octet-stream')
                p.set_payload(contenido_pdf)
                encoders.encode_base64(p)
                p.add_header('Content-Disposition', f'attachment; filename="Ficha_Tecnica_{datos["ref"]}.pdf"')
                m.attach(p)

        # Arte Final solo al Taller
        p_af = MIMEBase('application', 'octet-stream')
        p_af.set_payload(arte_final.getvalue())
        encoders.encode_base64(p_af)
        p_af.add_header('Content-Disposition', f'attachment; filename="DISENO_{datos["cliente"]}.pdf"')
        msg_taller.attach(p_af)

        # Envío
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(remitente, password)
        server.send_message(msg_taller)
        server.send_message(msg_cliente)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Fallo en la comunicación: {e}")
        return False

# =============================================================================
# 4. FLUJO DE LA APLICACIÓN
# =============================================================================
inject_dark_industrial_ui()

st.markdown('<div class="main-header"><h1>FLEXYLABEL ORDER</h1></div>', unsafe_allow_html=True)

COL_L, COL_M, COL_R = st.columns([1, 4, 1])

with COL_L:
    st.image("https://images.unsplash.com/photo-1610473069150-13645396b270?w=400")
    st.image("https://images.unsplash.com/photo-1563089145-599997674d42?w=400")

with COL_R:
    st.image("https://images.unsplash.com/photo-1590402494682-cd3fb53b1f71?w=400")
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400")

with COL_M:
    with st.form("form_dark"):
        st.write("### 🏢 DATOS GENERALES")
        c1, c2, c3 = st.columns([2, 2, 1])
        cliente = c1.text_input("RAZÓN SOCIAL / CLIENTE")
        email_c = c2.text_input("EMAIL CONFIRMACIÓN")
        ref_p = c3.text_input("REF. PEDIDO", value="ORD-2026")

        st.write("---")
        st.write("### 📐 ESPECIFICACIONES TÉCNICAS")
        c4, c5, c6 = st.columns(3)
        ancho = c4.number_input("ANCHO (mm)", value=100)
        largo = c5.number_input("LARGO (mm)", value=100)
        cantidad = c6.number_input("CANTIDAD TOTAL", value=5000)

        c7, c8, c9 = st.columns(3)
        material = c7.selectbox("SOPORTE", ["PP Blanco", "Couché", "Térmico", "Verjurado"])
        mandril = c8.selectbox("MANDRIL", ["76mm", "40mm", "25mm"])
        etq_r = c9.number_input("ETIQ / ROLLO", value=1000)

        st.write("---")
        st.write("### ⚙️ PRODUCCIÓN")
        c10, c11 = st.columns([2, 1])
        with c10:
            st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", width=400)
            sentido = st.select_slider("SENTIDO BOBINADO", options=[str(i) for i in range(1, 9)], value="3")
        with c11:
            archivo_af = st.file_uploader("ARTE FINAL (PDF)", type=["pdf"])
            notas = st.text_area("OBSERVACIONES TALLER")

        ml = (cantidad * (largo + 3)) / 1000
        st.info(f"Metros Lineales Estimados: {round(ml, 2)} m.")

        if st.form_submit_button("🚀 ENVIAR ORDEN A PRODUCCIÓN"):
            if not cliente or not archivo_af or not email_c:
                st.error("Iván, faltan datos obligatorios para poder enviar.")
            else:
                # 1. Crear PDF
                pdf = PDF_Taller()
                pdf.add_page()
                pdf.seccion("DATOS DEL PEDIDO")
                pdf.campo("Cliente", cliente, "Referencia", ref_p)
                pdf.seccion("ESPECIFICACIONES")
                pdf.campo("Material", material, "Cantidad", f"{cantidad} uds")
                pdf.campo("Medida", f"{ancho}x{largo} mm", "Metros", f"{round(ml, 2)} m")
                pdf.seccion("TALLER")
                pdf.campo("Sentido", sentido, "Mandril", mandril)
                
                temp_pdf = f"Ficha_{ref_p}.pdf"
                pdf.output(temp_path := temp_pdf)

                # 2. Enviar
                datos = {"cliente": cliente, "email_c": email_c, "material": material, "cantidad": cantidad, "ref": ref_p}
                
                with st.spinner("Procesando envío..."):
                    if enviar_pedidos_duales(temp_path, archivo_af, datos):
                        st.success("✅ ORDEN ENVIADA. El cliente ha recibido su confirmación.")
                        st.balloons()
                        if os.path.exists(temp_path): os.remove(temp_path)

st.markdown("<p style='text-align:center; color:#30363d; font-size:0.8rem; margin-top:4rem;'>FLEXYLABEL CLOUD v4.2.0</p>", unsafe_allow_html=True)
