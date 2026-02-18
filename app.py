import streamlit as st
import sqlite3
import google.generativeai as genai
from PIL import Image
import pandas as pd

# --- CONFIGURACIÓN DE IA ---
# Nota: En producción, usaremos "st.secrets" por seguridad
API_KEY = "PEGA_AQUI_TU_API_KEY_DE_PASO_1"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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
    if foto:
        img = Image.open(foto)
        with st.spinner("Identificando..."):
            prompt = "Identifica este producto alimenticio. Dame solo el nombre (ej: Tomate, Pasta, Leche). Si es un código de barras, dime el producto."
            res = model.generate_content([prompt, img])
            nombre_detectado = res.text.strip()
            
            st.write(f"Detectado: **{nombre_detectado}**")
            if st.button(f"Confirmar y Guardar {nombre_detectado}"):
                with conectar() as conn:
                    conn.execute("INSERT INTO productos (nombre) VALUES (?)", (nombre_detectado,))
                st.success("¡Guardado!")

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
