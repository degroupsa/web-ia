import google.generativeai as genai

# --- PEGA TU API KEY AQUÍ PARA PROBAR ---
API_KEY = "AIzaSyCi0nXWreFloqaqB_QSt3iQeVgDmHwofmM"

genai.configure(api_key=API_KEY)

print("🔍 Escaneando modelos disponibles para tu API Key...\n")

try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Disponible: {m.name}")
            available_models.append(m.name)
            
    print(f"\nTotal modelos encontrados: {len(available_models)}")
    
except Exception as e:
    print(f"❌ Error de conexión: {e}")