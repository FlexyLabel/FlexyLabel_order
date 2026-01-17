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
# 1. CONFIGURACIÓN DE INTERFAZ PREMIUM (DARK INDUSTRIAL)
# =============================================================================
st.set_page_config(
    page_title="FlexyLabel Order Management | Enterprise v4.5",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def inject_full_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

            /* Fondo y Textos Generales */
            .stApp {
                background: radial-gradient(circle at top right, #1e293b, #0f172a);
                color: #ffffff !important;
                font-family: 'Inter', sans-serif;
            }

            /* RECUADROS DE ENTRADA: Fondo Blanco, Letras Negras (Contraste Iván) */
            input, select, textarea, div[data-baseweb="input"] input {
                color: #000000 !important;
                background-color: #ffffff !important;
                border-radius: 8px !important;
                font-weight: 700 !important;
                border: 2px solid #3b82f6 !important;
            }
            
            /* Etiquetas (Labels) */
            label {
                color: #94a3b8 !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            /* Contenedor del Formulario */
            div[data-testid="stForm"] {
                background: rgba(30, 41, 59, 0.7) !important;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1) !important;
                border-radius: 20px !important;
                padding: 3rem !important;
                box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            }

            /* Botón de Envío */
            .stButton button {
                background: linear-gradient(90deg, #2563eb, #3b82f6) !important;
                color: white !important;
                height: 4.5rem !important;
                border-radius: 12px !important;
                font-weight: 800 !important;
                font-size: 1.3rem !important;
                text-transform: uppercase;
                border: none !important;
                width: 100% !important;
                transition: 0.3s all ease;
            }
            .stButton button:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 25px rgba(59, 130, 246, 0.5) !important;
            }

            /* Métricas de Ingeniería */
            .metric-box {
                background: rgba(255,255,255,0.05);
                padding: 1.5rem;
                border-radius: 12px;
                border-left: 5px solid #3b82f6;
                margin-top: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. MOTOR DE GENERACIÓN DE FICHA TÉCNICA (PDF PROFESIONAL)
# =============================================================================
class PDF_Industrial(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 40, 'F')
        self.set_xy(10, 15)
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'FLEXYLABEL // ORDEN DE PRODUCCION', ln=True)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f'Generado: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True)
        self.ln(15)

    def seccion(self, titulo):
        self.ln(5)
        self.set_fill_color(241, 245, 249)
        self.set_text_color(30, 41, 59)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, f"  {titulo}", ln=True, fill=True)
        self.ln(4)

    def fila(self, l1, v1, l2="", v2=""):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(50, 50, 50)
        self.cell(40, 8, f"{l1}:", 0)
        self.set_font('Helvetica', '', 10)
        self.cell(60, 8, f"{v1}", 0)
        if l2:
            self.set_font('Helvetica', 'B', 10)
            self.cell(40, 8, f"{l2}:", 0)
            self.set_font('Helvetica', '', 10)
            self.cell(0, 8, f"{v2}", 0)
        self.ln(8)

# =============================================================================
# 3. LÓGICA DE CORREO DUAL
# =============================================================================
def ejecutar_envio_total(pdf_path, af_file, datos):
    try:
        user = st.secrets["email_usuario"]
        pwd = st.secrets["email_password"]

        # --- CORREO TALLER ---
        msg_t = MIMEMultipart()
        msg_t['From'] = user
        msg_t['To'] = "covet@etiquetes.com"
        msg_t['Subject'] = f"🚀 PRODUCCION: {datos['cliente']} | REF: {datos['ref']}"
        msg_t.attach(MIMEText(f"Ficha técnica y arte final adjuntos para {datos['cliente']}.", 'plain'))

        # --- CORREO CLIENTE ---
        msg_c = MIMEMultipart()
        msg_c['From'] = user
        msg_c['To'] = datos['email_c']
        msg_c['Subject'] = "Confirmación de Pedido - FlexyLabel"
        msg_c.attach(MIMEText(f"Estimado/a {datos['cliente']},\nHemos recibido su pedido correctamente. Gracias por confiar en nosotros.", 'plain'))

        # Adjuntar PDF a ambos
        with open(pdf_path, "rb") as f:
            file_data = f.read()
            for m in [msg_t, msg_c]:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file_data)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="Ficha_{datos["ref"]}.pdf"')
                m.attach(part)

        # Arte Final solo al Taller
        af_part = MIMEBase('application', 'octet-stream')
        af_part.set_payload(af_file.getvalue())
        encoders.encode_base64(af_part)
        af_part.add_header('Content-Disposition', f'attachment; filename="ARTE_FINAL_{datos["ref"]}.pdf"')
        msg_t.attach(af_part)

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(user, pwd)
        server.send_message(msg_t)
        server.send_message(msg_c)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Fallo en envío: {e}")
        return False

# =============================================================================
# 4. APLICACIÓN PRINCIPAL
# =============================================================================
inject_full_css()

st.markdown("<h1 style='text-align:center;'>FLEXYLABEL <span style='font-weight:300;'>ORDER SYSTEM</span></h1>", unsafe_allow_html=True)

L, M, R = st.columns([1, 4, 1])

with M:
    with st.form("industrial_form_v4"):
        st.write("### 🏢 DATOS DEL PROYECTO")
        c1, c2, c3 = st.columns([2, 2, 1])
        cliente = c1.text_input("RAZÓN SOCIAL / CLIENTE")
        email_c = c2.text_input("EMAIL DE CONFIRMACIÓN")
        ref_p = c3.text_input("REF. INTERNA", value="ORD-2026")

        st.write("### 📐 ESPECIFICACIONES TÉCNICAS")
        c4, c5, c6 = st.columns(3)
        ancho = c4.number_input("ANCHO (mm)", value=100)
        largo = c5.number_input("LARGO (mm)", value=100)
        cantidad = c6.number_input("CANTIDAD TOTAL (uds)", value=5000)

        c7, c8, c9 = st.columns(3)
        material = c7.selectbox("SOPORTE", ["PP Blanco", "PP Transparente", "Couché", "Térmico", "Verjurado"])
        mandril = c8.selectbox("MANDRIL", ["76mm", "40mm", "25mm"])
        etq_r = c9.number_input("ETIQUETAS / ROLLO", value=1000)

        st.write("---")
        st.write("### ⚙️ CONFIGURACIÓN DE BOBINADO")
        
        # Referencia visual de los 8 sentidos
        
        st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", caption="Esquema Universal de Sentidos de Salida")
        
        sentido_sel = st.select_slider("DESLICE PARA MARCAR EL SENTIDO (1-8)", options=[str(i) for i in range(1, 9)], value="3")
        
        # Imagen dinámica de confirmación
        st.markdown(f"""
            <div style="background:#1e3a8a; padding:15px; border-radius:10px; text-align:center; border:2px solid #3b82f6;">
                <h3 style="margin:0; color:white;">SENTIDO SELECCIONADO: {sentido_sel}</h3>
                <p style="color:#93c5fd; margin:0; font-size:0.9rem;">Confirme que este número coincide con el mapa superior.</p>
            </div>
        """, unsafe_allow_html=True)

        st.write("### 📂 ARCHIVOS Y ACABADOS")
        c10, c11 = st.columns([1, 1])
        with c10:
            archivo_af = st.file_uploader("SUBIR DISEÑO (PDF)", type=["pdf"])
        with c11:
            obs = st.text_area("NOTAS PARA EL MAQUINISTA")

        # Cálculos de ingeniería
        ml = (cantidad * (largo + 3)) / 1000
        m2 = (ancho * largo * cantidad) / 1000000
        st.markdown(f"""
            <div class="metric-box">
                <p style="margin:0; color:#94a3b8; font-size:0.8rem;">CÁLCULO DE CONSUMO ESTIMADO</p>
                <h3 style="margin:0; color:#60a5fa;">{round(ml, 2)} Metros Lineales | {round(m2, 2)} m² de material</h3>
            </div>
        """, unsafe_allow_html=True)

        if st.form_submit_button("🚀 ENVIAR ORDEN DE TRABAJO"):
            if not cliente or not archivo_af or not email_c:
                st.error("Campos críticos faltantes.")
            else:
                # 1. Crear PDF
                pdf = PDF_Industrial()
                pdf.add_page()
                pdf.seccion("DATOS DEL PEDIDO")
                pdf.fila("Cliente", cliente, "Referencia", ref_p)
                pdf.seccion("FICHA TÉCNICA")
                pdf.fila("Medidas", f"{ancho} x {largo} mm", "Cantidad", f"{cantidad} uds")
                pdf.fila("Material", material, "Etiq/Rollo", etq_r)
                pdf.seccion("TALLER")
                pdf.fila("Sentido Salida", sentido_sel, "Mandril", mandril)
                pdf.fila("Metros Lineales", f"{round(ml, 2)} m", "M2 Totales", f"{round(m2, 2)} m2")
                
                if obs:
                    pdf.seccion("OBSERVACIONES")
                    pdf.set_font("Helvetica", "", 10)
                    pdf.multi_cell(0, 8, obs)

                path_pdf = f"Ficha_{ref_p}.pdf"
                pdf.output(path_pdf)

                # 2. Enviar
                with st.spinner("Sincronizando..."):
                    if ejecutar_envio_total(path_pdf, archivo_af, {"cliente": cliente, "email_c": email_c, "ref": ref_p}):
                        st.success("✅ ORDEN REGISTRADA.")
                        st.balloons()
                        if os.path.exists(path_pdf): os.remove(path_pdf)

st.markdown("<p style='text-align:center; color:#475569; font-size:0.8rem; margin-top:5rem;'>FlexyLabel v4.5 Enterprise</p>", unsafe_allow_html=True)
