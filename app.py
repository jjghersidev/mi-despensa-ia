import streamlit as st
import sqlite3
import google.generativeai as genai
from PIL import Image
import pandas as pd

# --- CONFIGURACIÓN DE IA ---
# Nota: En producción, usaremos "st.secrets" por seguridad
API_KEY = "AIzaSyBIrun1rxm_wgHoKMlDcigmn76FM0hl1QY"
genai.configure(api_key=API_KEY)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    # Si falla, usamos la versión pro como respaldo
    model = genai.GenerativeModel('gemini-pro-vision')

# --- LÓGICA DE BASE DE DATOS ---
def conectar():
    return sqlite3.connect('inventario.db', check_same_thread=False)

def init_db():
    with conectar() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS productos 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT)''')

# --- INTERFAZ ---
st.set_page_config(page_title="Chef S22", page_icon="🥘")
st.title("👨‍🍳 Mi Despensa S22 Ultra")

init_db()

# Pestañas para organizar la app en el móvil
tab1, tab2 = st.tabs(["📸 Escanear", "📖 Inventario y Recetas"])

with tab1:
    foto = st.camera_input("Captura un ingrediente")
    iif foto:
    img = Image.open(foto)
    with st.spinner("Leyendo producto..."):
        try:
            # Añadimos un prompt más específico para códigos de barras
            prompt = "Si ves un código de barras, dime el nombre del producto. Si ves comida, identifícala. Solo el nombre, por favor."
            res = model.generate_content([prompt, img])
            nombre_detectado = res.text.strip()
            # ... resto del código igual
        except Exception as e:
            st.error(f"Error de conexión con la IA: {e}")
            st.info("Asegúrate de que tu API Key sea válida y tengas crédito gratuito en AI Studio.")

with tab2:
    with conectar() as conn:
        df = pd.read_sql_query("SELECT * FROM productos", conn)
    
    st.write(f"Tienes {len(df)} ingredientes.")
    st.dataframe(df[['nombre']], use_container_width=True)
    
    if not df.empty and st.button("🪄 Generar Receta"):
        ingredientes = ", ".join(df['nombre'].tolist())
        prompt_receta = f"Con estos ingredientes: {ingredientes}. Dame una receta rápida. Al final pon una lista de los ingredientes usados de mi lista."
        receta = model.generate_content(prompt_receta)
        st.markdown(receta.text)
        
        if st.button("🍽️ Cocinado (Limpiar usados)"):
            # Por ahora limpia todo para simplificar, luego podemos hacerlo selectivo
            with conectar() as conn:
                conn.execute("DELETE FROM productos")
            st.rerun()
