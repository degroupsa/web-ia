import urllib.parse
import random

def generar_imagen(prompt):
    """
    Genera una URL válida para el modelo Flux (Nano Banana).
    Codifica el texto para evitar enlaces rotos en Streamlit.
    """
    # 1. Limpieza y semilla
    prompt_limpio = prompt.strip()
    seed = random.randint(0, 999999)
    
    # 2. Codificación de URL (ESTO ARREGLA EL ICONO ROTO)
    # Convierte "un gato" en "un%20gato"
    prompt_encoded = urllib.parse.quote(prompt_limpio)
    
    # 3. Construcción de la URL
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?model=flux&width=1024&height=1024&seed={seed}&nologo=true"
    
    return url