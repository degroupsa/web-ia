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
    try:
        doc_ref = db.collection("usuarios").document(usuario)
        doc = doc_ref.get()
        if doc.exists:
            datos = doc.to_dict()
            if datos.get("password") == password:
                return True
        return False
    except:
        return False

def crear_user(usuario, password):
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
    except:
        return False

# --- 3. GESTIÓN DE SESIONES (CHATS) ---
def crear_sesion(usuario, rol, titulo):
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
    try:
        docs = db.collection("chats").where("usuario", "==", usuario).stream()
        chats = [(doc.id, doc.to_dict()) for doc in docs]
        chats.sort(key=lambda x: x[1].get("fecha", ""), reverse=True)
        return chats
    except:
        return []

# --- NUEVAS FUNCIONES DE BORRADO ---
def eliminar_chat(chat_id):
    """Elimina un chat específico por ID."""
    try:
        db.collection("chats").document(chat_id).delete()
        return True
    except:
        return False

def eliminar_todo(usuario):
    """Elimina TODOS los chats de un usuario."""
    try:
        docs = db.collection("chats").where("usuario", "==", usuario).stream()
        batch = db.batch()
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            if count >= 400: # Límite por batch
                batch.commit()
                batch = db.batch()
                count = 0
        if count > 0:
            batch.commit()
        return True
    except:
        return False

# --- 4. GESTIÓN DE MENSAJES ---
def guardar_msg(usuario, chat_id, rol, contenido):
    try:
        if not chat_id: return
        nuevo_mensaje = {
            "role": rol,
            "content": contenido,
            "timestamp": datetime.datetime.now()
        }
        db.collection("chats").document(chat_id).update({
            "mensajes": firestore.ArrayUnion([nuevo_mensaje])
        })
    except:
        pass

def cargar_msgs(usuario, chat_id):
    try:
        if not chat_id: return []
        doc = db.collection("chats").document(chat_id).get()
        if doc.exists:
            return doc.to_dict().get("mensajes", [])
        return []
    except:
        return []
    
def login_google(email, nombre):
    return True