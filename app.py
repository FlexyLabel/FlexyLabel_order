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
import math

# =============================================================================
# 1. CONFIGURACIÓN DE NÚCLEO Y CONSTANTES
# =============================================================================
st.set_page_config(
    page_title="FlexyLabel Order Management",
    layout="wide",
    page_icon="🏭"
)

# Configuración de Servidor y Taller
DESTINATARIO_TALLER = "covet@etiquetes.com"
VERSION_SOFTWARE = "4.2.0-PRO"

# =============================================================================
# 2. DISEÑO UI PROFESIONAL (INTER / SOBRIO)
# =============================================================================
def apply_corporate_ui():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

            /* Configuración Global */
            .stApp {
                background-color: #f8fafc;
                color: #1e293b;
                font-family: 'Inter', sans-serif;
            }

            /* Forzar textos legibles en recuadros */
            .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
                color: #0f172a !important; /* Texto oscuro para máxima legibilidad */
                background-color: #ffffff !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 6px !important;
            }

            /* Etiquetas de campo */
            label {
                color: #475569 !important;
                font-weight: 600 !important;
                font-size: 0.85rem !important;
                margin-bottom: 0.5rem !important;
            }

            /* Títulos */
            h1, h2, h3 {
                color: #0f172a !important;
                font-weight: 700 !important;
            }

            .main-header {
                background-color: #ffffff;
                padding: 2.5rem;
                border-bottom: 2px solid #e2e8f0;
                text-align: center;
                margin-bottom: 2rem;
            }

            /* Contenedores de Formulario */
            div[data-testid="stForm"] {
                background-color: #ffffff !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 12px !important;
                padding: 3rem !important;
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1) !important;
            }

            /* Botón Corporativo Azul */
            .stButton button {
                background-color: #2563eb !important;
                color: #ffffff !important;
                padding: 0.75rem 2rem !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                border: none !important;
                width: 100% !important;
                transition: background 0.2s ease !important;
            }

            .stButton button:hover {
                background-color: #1d4ed8 !important;
            }

            /* Imágenes Laterales */
            .side-panel img {
                border-radius: 10px;
                margin-bottom: 1.5rem;
                border: 1px solid #e2e8f0;
                box-shadow: 0 2px 4px rgb(0 0 0 / 0.05);
            }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 3. MOTOR DE GENERACIÓN DE PDF TÉCNICO (PROFESIONAL)
# =============================================================================
class FichaTecnica(FPDF):
    def header(self):
        # Logo o Franja Superior
        self.set_fill_color(37, 99, 235) # Azul Corporativo
        self.rect(0, 0, 210, 35, 'F')
        
        self.set_xy(10, 12)
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'ORDEN DE PRODUCCION - FLEXYLABEL', ln=True)
        
        self.set_font('Helvetica', '', 9)
        self.cell(0, 5, f'Ref. Sistema: {VERSION_SOFTWARE} | Fecha: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True)
        self.ln(15)

    def seccion_box(self, titulo):
        self.ln(5)
        self.set_fill_color(241, 245, 249)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(30, 41, 59)
        self.cell(0, 8, f"  {titulo}", ln=True, fill=True)
        self.ln(3)

    def campo_doble(self, label1, valor1, label2, valor2):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(71, 85, 105)
        self.cell(40, 7, f"{label1}:", 0)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(15, 23, 42)
        self.cell(55, 7, f"{valor1}", 0)
        
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(71, 85, 105)
        self.cell(40, 7, f"{label2}:", 0)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(15, 23, 42)
        self.cell(0, 7, f"{valor2}", 0)
        self.ln(7)

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Documento técnico generado por el portal de pedidos FlexyLabel - Página {self.page_no()}', 0, 0, 'C')

# =============================================================================
# 4. LÓGICA DE ENVÍO Y COMUNICACIÓN (DOBLE CANAL)
# =============================================================================
def ejecutar_envio(pdf_path, arte_final, datos):
    try:
        user = st.secrets["email_usuario"]
        pwd = st.secrets["email_password"]

        # --- A. EMAIL PARA EL TALLER ---
        msg_taller = MIMEMultipart()
        msg_taller['From'] = user
        msg_taller['To'] = DESTINATARIO_TALLER
        msg_taller['Subject'] = f"🔴 NUEVA ORDEN: {datos['cliente']} | {datos['referencia']}"
        
        cuerpo_taller = f"Se ha registrado una nueva orden de producción.\nCliente: {datos['cliente']}\nMaterial: {datos['material']}"
        msg_taller.attach(MIMEText(cuerpo_taller, 'plain'))

        # --- B. EMAIL PARA EL CLIENTE ---
        msg_cliente = MIMEMultipart()
        msg_cliente['From'] = user
        msg_cliente['To'] = datos['email_c']
        msg_cliente['Subject'] = "Confirmación de recepción de pedido - FlexyLabel"

        cuerpo_cliente = f"""
        Estimado/a {datos['cliente']},

        Hemos recibido correctamente su pedido en nuestra plataforma. 
        Nuestro equipo de producción ya dispone de la ficha técnica y los archivos necesarios para iniciar la fabricación.

        Detalles de la recepción:
        - Referencia: {datos['referencia']}
        - Producto: Etiquetas {datos['material']}
        - Cantidad: {datos['cantidad']} unidades

        Gracias por confiar en nosotros para sus proyectos de etiquetado. Recibirá una notificación cuando el pedido esté listo para expedición.

        Atentamente,
        El equipo de FlexyLabel.
        """
        msg_cliente.attach(MIMEText(cuerpo_cliente, 'plain'))

        # Adjuntar Ficha Técnica a ambos
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            for m in [msg_taller, msg_cliente]:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(pdf_data)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="FICHA_TECNICA_{datos["referencia"]}.pdf"')
                m.attach(part)

        # Adjuntar Arte Final solo al taller
        part_af = MIMEBase('application', 'octet-stream')
        part_af.set_payload(arte_final.getvalue())
        encoders.encode_base64(part_af)
        part_af.add_header('Content-Disposition', f'attachment; filename="DISENO_{datos["referencia"]}.pdf"')
        msg_taller.attach(part_af)

        # Envío Real
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(user, pwd)
        server.send_message(msg_taller)
        server.send_message(msg_cliente)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error de comunicación SMTP: {e}")
        return False

# =============================================================================
# 5. APLICACIÓN PRINCIPAL
# =============================================================================
def main():
    apply_corporate_ui()
    
    # Header Corporativo
    st.markdown('<div class="main-header"><h1>Portal de Gestión de Pedidos</h1><p>Versión Industrial 4.2.0</p></div>', unsafe_allow_html=True)

    L, M, R = st.columns([1, 4, 1])

    with L:
        st.markdown('<div class="side-panel">', unsafe_allow_html=True)
        st.image("https://images.unsplash.com/photo-1610473069150-13645396b270?w=400")
        st.image("https://images.unsplash.com/photo-1563089145-599997674d42?w=400")
        st.markdown('</div>', unsafe_allow_html=True)

    with R:
        st.markdown('<div class="side-panel">', unsafe_allow_html=True)
        st.image("https://images.unsplash.com/photo-1590402494682-cd3fb53b1f71?w=400")
        st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=400")
        st.markdown('</div>', unsafe_allow_html=True)

    with M:
        with st.form("orden_produccion"):
            st.write("### 1. DATOS DEL CLIENTE")
            c1, c2, c3 = st.columns([2, 2, 1])
            cliente = c1.text_input("NOMBRE / EMPRESA", placeholder="Ej: Industrias Alimenticias S.A.")
            email_c = c2.text_input("CORREO ELECTRÓNICO", placeholder="logistica@cliente.com")
            ref_int = c3.text_input("REF. INTERNA", value=f"FX-{datetime.date.today().year}")

            st.write("---")
            st.write("### 2. ESPECIFICACIONES TÉCNICAS")
            c4, c5, c6 = st.columns(3)
            ancho = c4.number_input("ANCHO ETIQUETA (mm)", 10, 500, 100)
            largo = c5.number_input("LARGO ETIQUETA (mm)", 10, 500, 100)
            cantidad = c6.number_input("CANTIDAD TOTAL (uds)", 100, 2000000, 5000)

            c7, c8, c9 = st.columns(3)
            material = c7.selectbox("MATERIAL BASE", ["PP Blanco", "Couché", "Térmico", "Verjurado Cream"])
            mandril = c8.selectbox("DIÁMETRO MANDRIL", ["76 mm", "40 mm", "25 mm"])
            etiq_rollo = c9.number_input("ETIQ / ROLLO", 100, 10000, 1000)

            st.write("---")
            st.write("### 3. CONFIGURACIÓN DE TALLER")
            c10, c11 = st.columns([2, 1])
            with c10:
                st.image("https://www.etiquetas-autoadhesivas.es/wp-content/uploads/2018/10/sentido-salida-etiquetas.jpg", width=380)
                sentido = st.select_slider("POSICIÓN DE BOBINADO", options=[str(i) for i in range(1, 9)], value="3")
            with c11:
                archivo_af = st.file_uploader("ADJUNTAR ARTE FINAL (PDF)", type=["pdf"])
                notas = st.text_area("NOTAS PARA EL MAQUINISTA", height=120)

            # Cálculos rápidos
            ml = (cantidad * (largo + 3)) / 1000
            st.info(f"Cálculo estimado de consumo: {round(ml, 2)} metros lineales.")

            if st.form_submit_button("VALIDAR Y ENVIAR ORDEN"):
                if not cliente or not archivo_af or not email_c:
                    st.warning("⚠️ Faltan datos críticos para la producción.")
                else:
                    # Crear Ficha Técnica
                    pdf = FichaTecnica()
                    pdf.add_page()
                    pdf.seccion_box("DATOS COMERCIALES")
                    pdf.campo_doble("Cliente", cliente, "Referencia", ref_int)
                    pdf.campo_doble("Email Cliente", email_c, "Fecha Pedido", datetime.date.today().strftime("%d/%m/%Y"))
                    
                    pdf.seccion_box("ESPECIFICACIONES DEL PRODUCTO")
                    pdf.campo_doble("Ancho x Largo", f"{ancho} x {largo} mm", "Cantidad Total", f"{cantidad} uds")
                    pdf.campo_doble("Material Soporte", material, "Unidades/Rollo", etiq_rollo)
                    
                    pdf.seccion_box("REQUERIMIENTOS DE MAQUINARIA")
                    pdf.campo_doble("Sentido Salida", sentido, "Mandril", mandril)
                    pdf.campo_doble("Metros Lineales", f"{round(ml, 2)} m", "Tipo Troquel", "Estándar / Recto")
                    
                    if notas:
                        pdf.seccion_box("OBSERVACIONES TÉCNICAS")
                        pdf.set_font("Helvetica", "", 10)
                        pdf.multi_cell(0, 7, notas)

                    temp_file = f"ORDEN_{ref_int}.pdf"
                    pdf.output(temp_file)

                    datos_p = {
                        "cliente": cliente, "email_c": email_c, "referencia": ref_int,
                        "material": material, "cantidad": cantidad
                    }

                    with st.spinner("Sincronizando con taller..."):
                        if ejecutar_envio(temp_file, archivo_af, datos_p):
                            st.success("✅ ORDEN REGISTRADA. Se han enviado los correos de confirmación.")
                            st.balloons()
                            if os.path.exists(temp_file): os.remove(temp_file)

    st.markdown("<p style='text-align:center; color:#94a3b8; font-size:0.75rem; margin-top:4rem;'>FlexyLabel Order Management System v4.2.0 | Desarrollado para Iván</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
