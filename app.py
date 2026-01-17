import streamlit as st
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime
import os

# =============================================================================
# 1. DISEÑO DE INTERFAZ PREMIUM (GLASSMORPHISM & INDUSTRIAL DARK)
# =============================================================================
st.set_page_config(
    page_title="FlexyLabel Enterprise | Production Portal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def inject_premium_ui():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

            /* Fondo Base */
            .stApp {
                background: radial-gradient(circle at top right, #1e293b, #0f172a);
                color: #f8fafc !important;
                font-family: 'Inter', sans-serif;
            }

            /* Contenedor Principal Estilo Cristal */
            div[data-testid="stForm"] {
                background: rgba(30, 41, 59, 0.7) !important;
                backdrop-filter: blur(12px) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 24px !important;
                padding: 4rem !important;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
            }

            /* Títulos */
            h1 {
                font-weight: 800 !important;
                letter-spacing: -0.05em !important;
                background: linear-gradient(to right, #60a5fa, #3b82f6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 2rem !important;
            }

            /* INPUTS: Fondo Blanco, Letras Negras (Contraste Máximo) */
            input, select, textarea, div[data-baseweb="input"] {
                background-color: #ffffff !important;
                color: #0f172a !important;
                border-radius: 10px !important;
                border: 2px solid transparent !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }
            
            input:focus {
                border-color: #3b82f6 !important;
                box-shadow: 0 0 15px rgba(59, 130, 246, 0.3) !important;
            }

            /* Labels en Mayúsculas Sutiles */
            label {
                color: #94a3b8 !important;
                font-size: 0.8rem !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.6rem !important;
            }

            /* Botón Pro */
            .stButton button {
                background: #3b82f6 !important;
                border: none !important;
                padding: 1rem 2rem !important;
                border-radius: 12px !important;
                font-weight: 700 !important;
                font-size: 1.1rem !important;
                color: white !important;
                width: 100% !important;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4) !important;
                transition: 0.3s all !important;
            }

            .stButton button:hover {
                background: #2563eb !important;
                transform: translateY(-2px);
                box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.5) !important;
            }

            /* Tarjetas Informativas (M2, ML) */
            .metric-card {
                background: rgba(255, 255, 255, 0.05);
                padding: 1.5rem;
                border-radius: 15px;
                border-left: 4px solid #3b82f6;
                margin: 1rem 0;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. MOTOR PDF INDUSTRIAL
# =============================================================================
class PDF_Flexy(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 40, 'F')
        self.set_xy(15, 15)
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'Ficha Técnica de Producción', ln=True)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(148, 163, 184)
        self.cell(0, 5, f'Generado el: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True)

    def chapter_title(self, label):
        self.ln(10)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(30, 41, 59)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, f"  {label.upper()}", ln=True, fill=True)
        self.ln(4)

    def draw_data(self, key, value, key2="", value2=""):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(71, 85, 105)
        self.cell(40, 8, f"{key}:", 0)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(15, 23, 42)
        self.cell(60, 8, f"{value}", 0)
        if key2:
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(71, 85, 105)
            self.cell(40, 8, f"{key2}:", 0)
            self.set_font('Helvetica', '', 10)
            self.set_text_color(15, 23, 42)
            self.cell(0, 8, f"{value2}", 0)
        self.ln(8)

# =============================================================================
# 3. LÓGICA DE ENVÍO Y CONFIRMACIÓN
# =============================================================================
def enviar_emails(pdf_path, arte_final, datos):
    try:
        remitente = st.secrets["email_usuario"]
        password = st.secrets["email_password"]

        # Correo Taller
        msg_t = MIMEMultipart()
        msg_t['From'] = remitente
        msg_t['To'] = "covet@etiquetes.com"
        msg_t['Subject'] = f"🟢 NUEVA ORDEN: {datos['cliente']} - {datos['ref']}"
        msg_t.attach(MIMEText(f"Se adjunta ficha técnica y diseño para el cliente {datos['cliente']}.", 'plain'))

        # Correo Cliente (Mensaje de Cortesía)
        msg_c = MIMEMultipart()
        msg_c['From'] = remitente
        msg_c['To'] = datos['email_c']
        msg_c['Subject'] = "Confirmación de Pedido | FlexyLabel"
        msg_c.attach(MIMEText(f"""
        Estimado/a {datos['cliente']},
        
        Hemos recibido correctamente su solicitud de pedido con referencia {datos['ref']}. 
        Nuestro equipo de taller ya tiene toda la información necesaria para comenzar con la producción.
        
        Gracias por confiar en FlexyLabel.
        """, 'plain'))

        # Adjuntos
        with open(pdf_path, "rb") as f:
            p_ficha = MIMEBase('application', 'octet-stream')
            p_ficha.set_payload(f.read())
            encoders.encode_base64(p_ficha)
            p_ficha.add_header('Content-Disposition', f'attachment; filename="Ficha_Tecnica_{datos["ref"]}.pdf"')
            msg_t.attach(p_ficha)
            msg_c.attach(p_ficha)

        p_af = MIMEBase('application', 'octet-stream')
        p_af.set_payload(arte_final.getvalue())
        encoders.encode_base64(p_af)
        p_af.add_header('Content-Disposition', f'attachment; filename="Diseno_{datos["cliente"]}.pdf"')
        msg_t.attach(p_af)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(remitente, password)
        server.send_message(msg_t)
        server.send_message(msg_c)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error en el servidor: {e}")
        return False

# =============================================================================
# 4. ESTRUCTURA DE LA APLICACIÓN
# =============================================================================
inject_premium_ui()

# Header Central
st.markdown("<h1 style='text-align:center;'>FLEXYLABEL <span style='color:#f8fafc; font-weight:300;'>ENTERPRISE</span></h1>", unsafe_allow_html=True)

COL_L, COL_M, COL_R = st.columns([1, 5, 1])

with COL_M:
    with st.form("main_form_pro"):
        st.write("### 🏢 IDENTIFICACIÓN COMERCIAL")
        c1, c2, c3 = st.columns([2, 2, 1])
        cliente = c1.text_input("RAZÓN SOCIAL / CLIENTE", placeholder="Nombre de la empresa")
        email_c = c2.text_input("EMAIL DE CONFIRMACIÓN", placeholder="logistica@cliente.com")
        ref = c3.text_input("REF. PEDIDO", value="ORD-2026")

        st.write("### 📐 PARÁMETROS DE FABRICACIÓN")
        c4, c5, c6 = st.columns(3)
        ancho = c4.number_input("ANCHO (mm)", value=100)
        largo = c5.number_input("LARGO (mm)", value=100)
        cantidad = c6.number_input("CANTIDAD TOTAL", value=5000)

        c7, c8, c9 = st.columns(3)
        material = c7.selectbox("SOPORTE", ["PP Blanco", "Couché", "Térmico", "Verjurado"])
        mandril = c8.selectbox("MANDRIL", ["76mm", "40mm", "25mm"])
        etq_r = c9.number_input("ETIQ. POR ROLLO", value=1000)

        st.write("### ⚙️ ESQUEMA TÉCNICO DE SALIDA")
        # Esquema de referencia
        
        st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", width=600)
        
        sentido = st.select_slider("DESLICE PARA SELECCIONAR EL SENTIDO DE BOBINADO (1-8)", options=[str(i) for i in range(1, 9)], value="3")
        
        # Imagen dinámica de confirmación
        st.image(f"https://dummyimage.com/600x200/3b82f6/ffffff.png&text=CONFIRMACION+VISUAL:+POSICION+{sentido}", caption=f"El operario verá el esquema de salida número {sentido}")

        st.write("### 📂 ARCHIVOS Y OBSERVACIONES")
        archivo_af = st.file_uploader("ARTE FINAL (PDF REQUERIDO)", type=["pdf"])
        obs = st.text_area("INSTRUCCIONES ADICIONALES PARA TALLER")

        # Cálculo dinámico en tarjeta estética
        ml = (cantidad * (largo + 3)) / 1000
        st.markdown(f"""
            <div class="metric-card">
                <span style="color:#94a3b8; font-size:0.9rem;">CONSUMO ESTIMADO</span><br>
                <span style="font-size:1.8rem; font-weight:800; color:#60a5fa;">{round(ml, 2)} Metros Lineales</span>
            </div>
        """, unsafe_allow_html=True)

        if st.form_submit_button("Lanzar Orden a Producción"):
            if not cliente or not archivo_af or not email_c:
                st.error("Campos obligatorios incompletos.")
            else:
                # Generación PDF
                pdf = PDF_Flexy()
                pdf.add_page()
                pdf.chapter_title("Detalles del Cliente")
                pdf.draw_data("Cliente", cliente, "Referencia", ref)
                pdf.draw_data("Email", email_c, "Fecha", datetime.date.today().strftime("%d/%m/%Y"))
                
                pdf.chapter_title("Especificaciones Técnicas")
                pdf.draw_data("Material", material, "Cantidad", f"{cantidad} uds")
                pdf.draw_data("Dimensiones", f"{ancho}x{largo} mm", "Etiq/Rollo", etq_r)
                
                pdf.chapter_title("Instrucciones de Taller")
                pdf.draw_data("Bobinado", f"Sentido {sentido}", "Mandril", mandril)
                pdf.draw_data("Metros", f"{round(ml, 2)} ml")
                
                if obs:
                    pdf.chapter_title("Observaciones")
                    pdf.set_font('Helvetica', '', 10)
                    pdf.multi_cell(0, 8, obs)

                path_temp = f"Ficha_{ref}.pdf"
                pdf.output(path_temp)

                if enviar_emails(path_temp, archivo_af, {"cliente": cliente, "email_c": email_c, "ref": ref, "material": material}):
                    st.success("Orden procesada con éxito.")
                    st.balloons()
                    if os.path.exists(path_temp): os.remove(path_temp)

st.markdown("<p style='text-align:center; color:#475569; font-size:0.8rem; margin-top:5rem;'>FlexyLabel Order Management System v4.5 | Industrial Grade</p>", unsafe_allow_html=True)
