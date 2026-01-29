import os
import shutil
import subprocess
import sys

# Rutas: Origen (Donde Render lo guarda) -> Destino (Donde Streamlit lo busca)
render_secret_path = "/etc/secrets/secrets.toml"
streamlit_secret_dir = ".streamlit"
streamlit_secret_path = os.path.join(streamlit_secret_dir, "secrets.toml")

print("🚀 [KORTEXA BOOT] Iniciando configuración de arranque...")

# 1. Crear carpeta .streamlit si no existe
if not os.path.exists(streamlit_secret_dir):
    os.makedirs(streamlit_secret_dir)
    print(f"✅ Carpeta {streamlit_secret_dir} creada.")

# 2. Mover el archivo secreto
if os.path.exists(render_secret_path):
    shutil.copy(render_secret_path, streamlit_secret_path)
    print("✅ Archivo secrets.toml movido exitosamente a .streamlit/")
    
    # Verificación de seguridad (Opcional, para logs)
    # with open(streamlit_secret_path, "r") as f:
    #     print("🔍 Verificación: El archivo tiene contenido.")
else:
    print(f"⚠️ ADVERTENCIA: No se encontró {render_secret_path}. Verifica el nombre en Render.")

# 3. Arrancar Streamlit
print("🚀 Ejecutando Streamlit App...")
# Pasamos el control al comando de streamlit
subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])