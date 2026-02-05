import pandas as pd
import PyPDF2
import io

def procesar_archivo(uploaded_file):
    """
    Detecta el tipo de archivo (PDF, CSV, Excel, TXT) y extrae su texto
    para que Kortexa pueda analizarlo.
    """
    if uploaded_file is None:
        return ""

    try:
        # Obtener extensión y nombre
        nombre = uploaded_file.name.lower()
        texto_extraido = ""

        # CASO 1: PDF
        if nombre.endswith(".pdf"):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                texto_page = page.extract_text()
                if texto_page:
                    texto_extraido += texto_page + "\n"
            
            return f"\n\n[SISTEMA: Contenido del archivo PDF '{uploaded_file.name}']:\n{texto_extraido}\n[FIN ARCHIVO]\n"

        # CASO 2: EXCEL (.xlsx)
        elif nombre.endswith(".xlsx") or nombre.endswith(".xls"):
            # Leemos el Excel
            df = pd.read_excel(uploaded_file)
            # Convertimos a formato CSV (texto) para que la IA lo entienda mejor
            texto_datos = df.to_string(index=False)
            
            # Limitamos por seguridad (si es gigante, cortamos para no saturar)
            if len(texto_datos) > 50000:
                texto_datos = texto_datos[:50000] + "\n... [Datos truncados por longitud] ..."
                
            return f"\n\n[SISTEMA: Contenido del archivo Excel '{uploaded_file.name}']:\n{texto_datos}\n[FIN ARCHIVO]\n"

        # CASO 3: CSV
        elif nombre.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            texto_datos = df.to_string(index=False)
            
            if len(texto_datos) > 50000:
                texto_datos = texto_datos[:50000] + "\n... [Datos truncados] ..."
                
            return f"\n\n[SISTEMA: Contenido del archivo CSV '{uploaded_file.name}']:\n{texto_datos}\n[FIN ARCHIVO]\n"

        # CASO 4: TXT / MD / PY
        elif nombre.endswith(".txt") or nombre.endswith(".md") or nombre.endswith(".py"):
            stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
            texto_extraido = stringio.read()
            return f"\n\n[SISTEMA: Contenido del archivo de texto '{uploaded_file.name}']:\n{texto_extraido}\n[FIN ARCHIVO]\n"

        else:
            return f"\n[SISTEMA: Archivo '{uploaded_file.name}' cargado, pero el formato no es texto legible directo.]"

    except Exception as e:
        return f"\n[ERROR LEYENDO ARCHIVO: {str(e)}]"