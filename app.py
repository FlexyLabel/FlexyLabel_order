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
# 1. CONFIGURACIÓN TÉCNICA Y ESTILOS NEÓN (Lógica de UI)
# =============================================================================
DESTINATARIO_TALLER = "covet@etiquetes.com"
COLOR_NEON = "#58a6ff"
COLOR_BG = "#0d1117"

def apply_ultra_dark_theme():
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@300;500&display=swap');
            
            .stApp {{ background-color: {COLOR_BG}; color: #c9d1d9; }}
            .neon-text {{ color: {COLOR_NEON}; font-family: 'Orbitron', sans-serif; text-shadow: 0 0 10px rgba(88,166,255,0.4); }}
            
            /* Contenedor de Modelos */
            .model-card {{
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 20px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }}
            
            /* Botones Personalizados */
            .stButton>button {{
                border-radius: 8px;
                font-family: 'Orbitron';
                transition: 0.3s;
                text-transform: uppercase;
            }}
            
            .add-btn button {{ background-color: #238636 !important; color: white !important; border: none; }}
            .send-btn button {{ background: linear-gradient(90deg, #1f6feb, #58a6ff) !important; color: white !important; border: none; width: 100%; height: 3.5rem; }}
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. GESTIÓN DE ESTADO (Para múltiples modelos)
# =============================================================================
if 'modelos' not in st.session_state:
    st.session_state.modelos = [{'id': 0, 'ref': '', 'ancho': 100, 'largo': 100, 'cantidad': 5000, 'etq_rollo': 1000, 'pdf': None}]

def agregar_modelo():
    new_id = len(st.session_state.modelos)
    st.session_state.modelos.append({'id': new_id, 'ref': '', 'ancho': 100, 'largo': 100, 'cantidad': 5000, 'etq_rollo': 1000, 'pdf': None})

# =============================================================================
# 3. MOTOR DE GENERACIÓN PDF (Multimodelo)
# =============================================================================
class MultiModelPDF(FPDF):
    def header(self):
        self.set_fill_color(13, 17, 23)
        self.rect(0, 0, 210, 40, 'F')
        self.set_font("Courier", 'B', 24)
        self.set_text_color(88, 166, 255)
        self.set_xy(10, 12)
        self.cell(0, 10, "FLEXYLABEL // ORDEN DE PRODUCCIÓN", ln=True)
        self.set_font("Arial", 'I', 9)
        self.set_text_color(200, 200, 200)
        self.cell(0, 5, f"Fecha de emisión: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        self.ln(15)

    def add_model_info(self, i, m, sentido, salida, material, mandril):
        self.set_font("Arial", 'B', 12)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, f" MODELO {i+1}: {m['ref'].upper()}", ln=True, fill=True)
        self.set_font("Arial", '', 10)
        
        data = [
            ["Ancho", f"{m['ancho']} mm", "Largo", f"{m['largo']} mm"],
            ["Cantidad", f"{m['cantidad']} uds", "Etq/Rollo", f"{m['etq_rollo']} uds"],
            ["Material", material, "Mandril", mandril],
            ["Sentido", f"Posición {sentido}", "Salida", salida]
        ]
        for row in data:
            self.cell(30, 8, f"{row[0]}:", 0)
            self.cell(60, 8, row[1], 0)
            self.cell(30, 8, f"{row[2]}:", 0)
            self.cell(60, 8, row[3], 0, ln=True)
        self.ln(5)

# =============================================================================
# 4. LÓGICA DE CORREO ELECTRÓNICO (Doble Envío)
# =============================================================================
def enviar_emails(pdf_path, modelos_data, datos_cliente):
    try:
        user = st.secrets["email_usuario"]
        pwd = st.secrets["email_password"]
        
        destinatarios = [DESTINATARIO_TALLER, datos_cliente['email']]
        
        for dest in destinatarios:
            msg = MIMEMultipart()
            msg['From'] = user
            msg['To'] = dest
            es_cliente = (dest == datos_cliente['email'])
            
            msg['Subject'] = f"{'CONFIRMACIÓN' if es_cliente else 'NUEVA ORDEN'}: {datos_cliente['cliente']}"
            
            cuerpo = f"""
            Hola {datos_cliente['cliente']},
            Este es un {'comprobante de tu pedido' if es_cliente else 'nuevo pedido para producción'}.
            
            Resumen de modelos: {len(modelos_data)} diseño(s) adjuntos en la orden técnica.
            """
            msg.attach(MIMEText(cuerpo, 'plain'))

            with open(pdf_path, "rb") as f:
                part = MIMEBase('application', 'pdf')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={pdf_path}')
                msg.attach(part)

            # Para el taller, adjuntamos también los artes finales originales
            if not es_cliente:
                for m in modelos_data:
                    if m['pdf']:
                        part_m = MIMEBase('application', 'octet-stream')
                        part_m.set_payload(m['pdf'].getvalue())
                        encoders.encode_base64(part_m)
                        part_m.add_header('Content-Disposition', f'attachment; filename="AF_{m["ref"]}_{m["pdf"].name}"')
                        msg.attach(part_m)

            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login(user, pwd)
            server.send_message(msg)
            server.quit()
        return True
    except Exception as e:
        st.error(f"Error en el servidor de correo: {e}")
        return False

# =============================================================================
# 5. UI PRINCIPAL
# =============================================================================
def main():
    apply_ultra_dark_theme()
    st.markdown('<h1 class="neon-text">FLEXYLABEL PRODUCTION CONSOLE</h1>', unsafe_allow_html=True)
    
    # Datos Globales del Cliente
    with st.container():
        st.markdown('<div class="model-card">', unsafe_allow_html=True)
        st.subheader("📋 DATOS DE CABECERA")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cliente = st.text_input("EMPRESA / CLIENTE")
        with col_c2:
            email_c = st.text_input("EMAIL PARA CONFIRMACIÓN")
        st.markdown('</div>', unsafe_allow_html=True)

    # Listado de Modelos
    st.markdown('<h2 class="neon-text" style="font-size:1.5rem;">📦 MODELOS A IMPRIMIR</h2>', unsafe_allow_html=True)
    
    for i, m in enumerate(st.session_state.modelos):
        with st.container():
            st.markdown(f'<div class="model-card">', unsafe_allow_html=True)
            st.markdown(f"#### Modelo #{i+1}")
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.session_state.modelos[i]['ref'] = st.text_input(f"Nombre del Diseño / Ref", key=f"ref_{i}")
            with c2:
                st.session_state.modelos[i]['ancho'] = st.number_input(f"Ancho (mm)", 1, 500, 100, key=f"anc_{i}")
            with c3:
                st.session_state.modelos[i]['largo'] = st.number_input(f"Largo (mm)", 1, 500, 100, key=f"lar_{i}")
            
            c4, c5, c6 = st.columns(3)
            with c4:
                st.session_state.modelos[i]['cantidad'] = st.number_input(f"Cantidad Total", 100, 1000000, 5000, key=f"cant_{i}")
            with c5:
                st.session_state.modelos[i]['etq_rollo'] = st.number_input(f"Etiquetas por Rollo", 50, 10000, 1000, key=f"epr_{i}")
            with c6:
                st.session_state.modelos[i]['pdf'] = st.file_uploader(f"Cargar Arte Final (PDF)", type=["pdf"], key=f"pdf_{i}")
            st.markdown('</div>', unsafe_allow_html=True)

    # Botón Añadir Modelo
    st.markdown('<div class="add-btn">', unsafe_allow_html=True)
    st.button("➕ AÑADIR OTRO MODELO / REFERENCIA", on_click=agregar_modelo)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Configuración de Producción Global
    with st.container():
        st.markdown('<div class="model-card">', unsafe_allow_html=True)
        st.subheader("⚙️ CONFIGURACIÓN DE TALLER")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.write("### Sentido de Salida")
            
            sentido = st.select_slider("Posición de bobinado", options=[str(i) for i in range(1, 9)], value="3")
            salida = st.radio("Salida", ["Exterior", "Interior"], horizontal=True)
        with col_t2:
            material = st.selectbox("Material", ["PP Blanco", "Couché", "Térmico", "Verjurado"])
            mandril = st.selectbox("Mandril", ["76mm", "40mm", "25mm"])
            obs = st.text_area("Observaciones Generales")
        st.markdown('</div>', unsafe_allow_html=True)

    # Envío Final
    st.markdown('<div class="send-btn">', unsafe_allow_html=True)
    if st.button("🚀 FINALIZAR Y ENVIAR PEDIDO COMPLETO"):
        if not cliente or not email_c:
            st.error("Iván, faltan los datos del cliente para el envío.")
        else:
            with st.spinner("Procesando Orden Multimodelo..."):
                datos_cliente = {'cliente': cliente, 'email': email_c}
                pdf = MultiModelPDF(datos_cliente)
                pdf.add_page()
                for i, m in enumerate(st.session_state.modelos):
                    pdf.add_model_info(i, m, sentido, salida, material, mandril)
                
                path = f"ORDEN_{cliente}.pdf".replace(" ", "_")
                pdf.output(path)
                
                if enviar_emails(path, st.session_state.modelos, datos_cliente):
                    st.success(f"¡Pedido enviado! Se ha enviado una confirmación a {email_c}")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
