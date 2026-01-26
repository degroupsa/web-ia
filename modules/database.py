import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# --- CONEXIÓN SINGLETON ---
def conectar_db():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                key_dict = dict(st.secrets["firebase"])
                key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
            else:
                cred = credentials.Certificate("firebase_key.json")
                firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Error Database: {e}")
            st.stop()
    return firestore.client()

db = conectar_db()

# --- FUNCIONES ---
def login(u, p):
    doc = db.collection("users").document(u).get()
    return doc.exists and doc.to_dict()["password"] == p

def crear_user(u, p):
    if db.collection("users").document(u).get().exists: return False
    db.collection("users").document(u).set({"password": p, "plan": "Gratis"})
    return True

def crear_sesion(user, rol, titulo):
    ref = db.collection("users").document(user).collection("sessions").document()
    ref.set({"titulo": titulo, "rol": rol, "creado": firestore.SERVER_TIMESTAMP})
    return ref.id

def guardar_msg(user, sid, role, content):
    if sid: db.collection("users").document(user).collection("sessions").document(sid).collection("msgs").add({
        "role": role, "content": content, "fecha": firestore.SERVER_TIMESTAMP
    })

def cargar_msgs(user, sid):
    if not sid: return []
    ref = db.collection("users").document(user).collection("sessions").document(sid).collection("msgs")
    return [d.to_dict() for d in ref.order_by("fecha").stream()]

def obtener_sesiones(user):
    ref = db.collection("users").document(user).collection("sessions")
    docs = ref.order_by("creado", direction=firestore.Query.DESCENDING).limit(15).stream()
    return [(d.id, d.to_dict()) for d in docs]