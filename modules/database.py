import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import uuid
import os

# --- 1. CONEXIÓN ROBUSTA A FIREBASE ---
if not firebase_admin._apps:
    try:
        if os.path.exists("firebase_key.json"):
            cred = credentials.Certificate("firebase_key.json")
            firebase_admin.initialize_app(cred)
        else:
            st.error("⚠️ Error Crítico: No se encuentra el archivo 'firebase_key.json'.")
            st.stop()
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Firebase: {e}")
        st.stop()

db = firestore.client()

# --- 2. GESTIÓN DE USUARIOS ---

def login(usuario, password):
    """Verifica si el usuario y contraseña existen en la colección 'usuarios'."""
    try:
        doc_ref = db.collection("usuarios").document(usuario)
        doc = doc_ref.get()
        
        if doc.exists:
            datos = doc.to_dict()
            if datos.get("password") == password:
                return True
        return False
    except Exception as e:
        st.error(f"Error Login: {e}")
        return False

def crear_user(usuario, password):
    """Crea un nuevo usuario si no existe."""
    try:
        doc_ref = db.collection("usuarios").document(usuario)
        if doc_ref.get().exists:
            return False 
        
        doc_ref.set({
            "usuario": usuario,
            "password": password,
            "creado": datetime.datetime.now()
        })
        return True
    except Exception as e:
        return False

# --- 3. GESTIÓN DE SESIONES (CHATS) ---

def crear_sesion(usuario, rol, titulo):
    """Crea un nuevo documento de chat y devuelve su ID."""
    try:
        chat_id = str(uuid.uuid4())
        
        db.collection("chats").document(chat_id).set({
            "usuario": usuario,
            "rol": rol,
            "titulo": titulo,
            "fecha": datetime.datetime.now(),
            "mensajes": [] 
        })
        return chat_id
    except:
        return None

def obtener_sesiones(usuario):
    """Devuelve una lista de chats (ID, Datos) del usuario."""
    try:
        # CORRECCIÓN IMPORTANTE:
        # Quitamos el .order_by("fecha") de la consulta a Firebase para evitar 
        # errores de "Falta Índice Compuesto". Ordenamos en Python.
        docs = db.collection("chats").where("usuario", "==", usuario).stream()
        
        chats = [(doc.id, doc.to_dict()) for doc in docs]
        
        # Ordenamos aquí por fecha (de más nuevo a más viejo)
        chats.sort(key=lambda x: x[1].get("fecha", ""), reverse=True)
        
        return chats
    except Exception as e:
        print(f"Error obteniendo sesiones: {e}")
        return []

# --- 4. GESTIÓN DE MENSAJES ---

def guardar_msg(usuario, chat_id, rol, contenido):
    """Guarda un mensaje dentro del documento del chat."""
    try:
        if not chat_id: return
        
        nuevo_mensaje = {
            "role": rol,
            "content": contenido,
            "timestamp": datetime.datetime.now()
        }
        
        doc_ref = db.collection("chats").document(chat_id)
        doc_ref.update({
            "mensajes": firestore.ArrayUnion([nuevo_mensaje])
        })
    except Exception as e:
        print(f"Error guardando msg: {e}")

def cargar_msgs(usuario, chat_id):
    """Carga los mensajes de un chat específico."""
    try:
        if not chat_id: return []
        
        doc = db.collection("chats").document(chat_id).get()
        if doc.exists:
            datos = doc.to_dict()
            return datos.get("mensajes", [])
        return []
    except:
        return []
    
def login_google(email, nombre):
    """Permite el ingreso con Google."""
    return True