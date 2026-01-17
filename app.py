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
# 1. CONFIGURACIÓN E INTERFAZ DARK PROFESIONAL (INTER / LETRAS NEGRAS EN INPUTS)
# =============================================================================
st.set_page_config(
    page_title="FLEXYLABEL ORDER | Production System",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def inject_industrial_dark_ui():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

            /* Fondo Oscuro */
            .stApp {
                background-color: #0d1117;
                color: #ffffff !important;
                font-family: 'Inter', sans-serif;
            }

            /* Títulos y Etiquetas en Blanco */
            h1, h2, h3, label, p {
                color: #ffffff !important;
                font-family: 'Inter', sans-serif !important;
            }

            /* RECUADROS BLANCOS CON TEXTO NEGRO (LEGIILIDAD MÁXIMA) */
            input, select, textarea, div[data-baseweb="input"] input, div[data-baseweb="select"] {
                color: #000000 !important;
                background-color: #ffffff !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
                border: none !important;
            }
            
            /* Ajuste específico para el texto que escribes */
            .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea {
                color: #000000 !important;
                background-color: #ffffff !important;
            }

            /* Contenedor del Formulario */
            div[data-testid="stForm"] {
                background-color: #161b22 !important;
                border: 1px solid #30363d !important;
                border-radius: 20px !important;
                padding: 3rem !important;
                box-shadow: 0 10px 40px rgba(0,0,0,0.6) !important;
            }

            /* Botón Industrial */
            .stButton button {
                background: linear-gradient(90deg, #1f6feb 0%, #58a6ff 100%) !important;
                color: #ffffff !important;
                height: 4.5rem !important;
                border-radius: 12px !important;
                font-weight: 700 !important;
                font-size: 1.3rem !important;
                text-transform: uppercase;
                border: none !important;
                margin-top: 2rem !important;
                width: 100% !important;
                transition: 0.3s all;
            }
            .stButton button:hover {
                transform: scale(1.01);
                box-shadow: 0 0 30px rgba(88, 166, 255, 0.4) !important;
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. LÓGICA DE IMÁGENES DE BOBINADO (DINÁMICO)
# =============================================================================
def get_winding_image(sense_number):
    """
    Iván, aquí mapeamos cada número del slider con su imagen técnica.
    He puesto placeholders, pero puedes cambiar las URLs por tus fotos reales.
    """
    winding_images = {
        "1": "https://img.freepik.com/vector-premium/esquema-sentido-bobinado-etiquetas-posicion-1.jpg",
        "2": "https://img.freepik.com/vector-premium/esquema-sentido-bobinado-etiquetas-posicion-2.jpg",
        "3": "https://img.freepik.com/vector-premium/esquema-sentido-bobinado-etiquetas-posicion-3.jpg",
        "4": "https://img.freepik.com/vector-premium/esquema-sentido-bobinado-etiquetas-posicion-4.jpg",
        "5": "https://img.freepik.com/vector-premium/esquema-sentido-bobinado-etiquetas-posicion-5.jpg",
        "6": "https://img.freepik.com/vector-premium/esquema-sentido-bobinado-etiquetas-posicion-6.jpg",
        "7": "https://img.freepik.com/vector-premium/esquema-sentido-bobinado-etiquetas-posicion-7.jpg",
        "8": "https://img.freepik.com/vector-premium/esquema-sentido-bobinado-etiquetas-posicion-8.jpg"
    }
    # Retornamos un placeholder dinámico si no hay URL real
    return f"https://placehold.co/600x300/1f6feb/ffffff?text=SENTIDO+DE+SALIDA+{sense_number}"

# =============================================================================
# 3. MOTOR DE PDF PROFESIONAL (FICHA TÉCNICA)
# =============================================================================
class PDF_Produccion(FPDF):
    def header(self):
        self.set_fill_color(22, 27, 34)
        self.rect(0, 0, 210, 40, 'F')
        self.set_xy(10, 15)
        self.set_font('Arial', 'B', 22)
        self.set_text_color(88, 166, 255)
        self.cell(0, 10, 'FLEXYLABEL // ORDEN DE FABRICACION', ln=True)
        self.set_font('Arial', '', 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f'Fecha de Emisión: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True)
        self.ln(15)

    def crear_seccion(self, titulo):
        self.ln(5)
        self.set_fill_color(48, 54, 61)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f"  {titulo}", ln=True, fill=True)
        self.ln(4)

    def agregar_datos(self, l1, v1, l2="", v2=""):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(50, 50, 50)
        self.cell(40, 8, f"{l1}:", 0)
        self.set_font('Arial', '', 10)
        self.cell(55, 8, f"{v1}", 0)
        if l2:
            self.set_font('Arial', 'B', 10)
            self.cell(40, 8, f"{l2}:", 0)
            self.set_font('Arial', '', 10)
            self.cell(0, 8, f"{v2}", 0)
        self.ln(8)

# =============================================================================
# 4. SISTEMA DE ENVÍO DE EMAIL (NOTIFICACIÓN DUAL)
# =============================================================================
def despachar_pedido(pdf_path, af_file, datos):
    try:
        user = st.secrets["email_usuario"]
        pwd = st.secrets["email_password"]

        # --- A. NOTIFICACIÓN AL TALLER ---
        msg_t = MIMEMultipart()
        msg_t['From'] = user
        msg_t['To'] = "covet@etiquetes.com"
        msg_t['Subject'] = f"🔴 NUEVA ORDEN: {datos['cliente']} | {datos['ref']}"
        
        cuerpo_t = f"Se ha generado una nueva orden de producción.\n\nCliente: {datos['cliente']}\nMaterial: {datos['material']}\nCantidad: {datos['cantidad']} uds."
        msg_t.attach(MIMEText(cuerpo_t, 'plain'))

        # --- B. NOTIFICACIÓN AL CLIENTE (CORTESÍA) ---
        msg_c = MIMEMultipart()
        msg_c['From'] = user
        msg_c['To'] = datos['email_c']
        msg_c['Subject'] = "Confirmación de recepción de pedido - FlexyLabel"

        cuerpo_c = f"""
        Estimado/a {datos['cliente']},

        Gracias por confiar en nosotros. Hemos recibido correctamente su pedido y ya se encuentra en nuestra cola de producción.

        Detalles registrados:
        - Referencia: {datos['ref']}
        - Cantidad: {datos['cantidad']} uds.
        - Material: {datos['material']}

        Nuestro equipo de taller revisará los archivos y se pondrá en marcha lo antes posible.

        Atentamente,
        El equipo de FlexyLabel.
        """
        msg_c.attach(MIMEText(cuerpo_c, 'plain'))

        # Adjuntar Ficha Técnica a ambos
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()
            for m in [msg_t, msg_c]:
                p = MIMEBase('application', 'octet-stream')
                p.set_payload(pdf_content)
                encoders.encode_base64(p)
                p.add_header('Content-Disposition', f'attachment; filename="FICHA_TECNICA_{datos["cliente"]}.pdf"')
                m.attach(p)

        # Adjuntar Arte Final solo al Taller
        p_af = MIMEBase('application', 'octet-stream')
        p_af.set_payload(af_file.getvalue())
        encoders.encode_base64(p_af)
        p_af.add_header('Content-Disposition', f'attachment; filename="ARTE_FINAL_{datos["cliente"]}.pdf"')
        msg_t.attach(p_af)

        # Servidor SMTP
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(user, pwd)
        server.send_message(msg_t)
        server.send_message(msg_c)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Fallo crítico en el envío: {e}")
        return False

# =============================================================================
# 5. ESTRUCTURA DE LA APLICACIÓN (UI + LÓGICA)
# =============================================================================
inject_industrial_dark_ui()

# Header Industrial
st.markdown("<h1 style='text-align:center; font-size:3rem;'>FLEXYLABEL ORDER v4.2</h1>", unsafe_allow_html=True)

L, M, R = st.columns([1, 4, 1])

with L:
    st.image("https://images.unsplash.com/photo-1610473069150-13645396b270?w=400")
    st.image("https://images.unsplash.com/photo-1563089145-599997674d42?w=400")

with R:
    st.image("https://images.unsplash.com/photo-1590402494682-cd3fb53b1f71?w=400")
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400")

with M:
    with st.form("main_production_form"):
        st.write("### 🏢 INFORMACIÓN COMERCIAL")
        c1, c2, c3 = st.columns([2, 2, 1])
        cliente = c1.text_input("CLIENTE / EMPRESA")
        email_c = c2.text_input("EMAIL CONFIRMACIÓN CLIENTE")
        ref_int = c3.text_input("REF. INTERNA", value="FX-2026")

        st.write("### 📐 ESPECIFICACIONES TÉCNICAS")
        c4, c5, c6 = st.columns(3)
        ancho = c4.number_input("ANCHO (mm)", value=100)
        largo = c5.number_input("LARGO (mm)", value=100)
        cantidad = c6.number_input("CANTIDAD TOTAL", value=5000)

        c7, c8, c9 = st.columns(3)
        material = c7.selectbox("SOPORTE", ["PP Blanco", "Couché", "Térmico", "Verjurado Cream"])
        mandril = c8.selectbox("MANDRIL", ["76mm", "40mm", "25mm"])
        etiq_rollo = c9.number_input("ETIQ / ROLLO", value=1000)

        st.write("---")
        st.write("### ⚙️ CONFIGURACIÓN DE TALLER")
        
        # Selector de Sentido de Bobinado
        sentido_bob = st.select_slider(
            "SELECCIONE SENTIDO DE BOBINADO (1-8)",
            options=[str(i) for i in range(1, 9)],
            value="3"
        )
        
        # IMAGEN DINÁMICA: Muestra el esquema según el slider
        st.image(get_winding_image(sentido_bob), width=450)
        

        c10, c11 = st.columns([1, 1])
        with c10:
            archivo_af = st.file_uploader("ARTE FINAL (PDF)", type=["pdf"])
        with c11:
            obs = st.text_area("OBSERVACIONES PARA PRODUCCIÓN")

        # Cálculos de ingeniería rápidos
        ml = (cantidad * (largo + 3)) / 1000
        st.info(f"Consumo estimado de materia prima: {round(ml, 2)} metros lineales.")

        # PROCESO DE ENVÍO
        if st.form_submit_button("🚀 LANZAR ORDEN A TALLER"):
            if not cliente or not archivo_af or not email_c:
                st.error("⚠️ Faltan datos críticos: Cliente, Email o Arte Final.")
            else:
                # 1. Crear PDF Técnico
                pdf = PDF_Produccion()
                pdf.add_page()
                pdf.crear_seccion("DATOS GENERALES")
                pdf.agregar_datos("Cliente", cliente, "Referencia", ref_int)
                pdf.crear_seccion("ESPECIFICACIONES DEL PRODUCTO")
                pdf.agregar_datos("Medidas", f"{ancho} x {largo} mm", "Cantidad", f"{cantidad} uds")
                pdf.agregar_datos("Material", material, "Etiq/Rollo", etiq_rollo)
                pdf.crear_seccion("REQUERIMIENTOS DE TALLER")
                pdf.agregar_datos("Sentido Salida", sentido_bob, "Mandril", mandril)
                pdf.agregar_datos("Metros Estimados", f"{round(ml, 2)} m")
                
                if obs:
                    pdf.crear_seccion("OBSERVACIONES TÉCNICAS")
                    pdf.set_font("Arial", "", 10)
                    pdf.multi_cell(0, 8, obs)

                path_temp = f"ORDEN_{cliente}.pdf"
                pdf.output(path_temp)

                # 2. Enviar correos
                datos_pedido = {
                    "cliente": cliente, "email_c": email_c, "material": material,
                    "cantidad": cantidad, "ref": ref_int
                }

                with st.spinner("Sincronizando con el servidor de correo..."):
                    if despachar_pedido(path_temp, archivo_af, datos_pedido):
                        st.success("✅ ORDEN REGISTRADA. El taller y el cliente han sido notificados.")
                        st.balloons()
                        if os.path.exists(path_temp): os.remove(path_temp)

st.markdown("<p style='text-align:center; color:#30363d; font-size:0.8rem; margin-top:5rem;'>FLEXYLABEL INDUSTRIAL SOFTWARE v4.2 | 2026</p>", unsafe_allow_html=True)
