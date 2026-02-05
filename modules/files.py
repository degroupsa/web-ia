import pandas as pd
from pypdf import PdfReader
import io

def procesar_archivo(uploaded_file):
    """
    Recibe un archivo de Streamlit (UploadedFile) y extrae su texto.
    Soporta: PDF, CSV, TXT, XLSX.
    """
    if uploaded_file is None:
        return ""
    
    nombre = uploaded_file.name.lower()
    texto_extraido = ""

    try:
        # 1. Procesar PDF 📕
        if nombre.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                texto_extraido += page.extract_text() + "\n"
        
        # 2. Procesar Excel (XLSX, XLS) 📊
        elif nombre.endswith(".xlsx") or nombre.endswith(".xls"):
            df = pd.read_excel(uploaded_file)
            # Convertimos a CSV string para que la IA entienda la estructura
            texto_extraido = df.to_csv(index=False)
            
        # 3. Procesar CSV 📋
        elif nombre.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            texto_extraido = df.to_csv(index=False)
            
        # 4. Procesar Texto Plano / Codigo (TXT, PY, MD) 📝
        else:
            # Intentamos leer como utf-8
            stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
            texto_extraido = stringio.read()

        return f"\n\n[CONTENIDO DEL ARCHIVO ADJUNTO '{uploaded_file.name}']:\n{texto_extraido}\n[FIN DEL ARCHIVO]\n"

    except Exception as e:
        return f"\n[ERROR LEYENDO ARCHIVO: {str(e)}]\n"