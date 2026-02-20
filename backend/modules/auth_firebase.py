import requests
import streamlit as st

# URL de la API de Identidad de Google (No tocar)
URL_AUTH = "https://identitytoolkit.googleapis.com/v1/accounts"

def obtener_key():
    """Intenta obtener la clave web desde secrets o variable de entorno"""
    try:
        return st.secrets["FIREBASE_WEB_KEY"]
    except:
        return None

def sign_in(email, password):
    """
    Inicia sesión con email y contraseña.
    Retorna: Diccionario con 'idToken', 'localId', 'email' o Error.
    """
    api_key = obtener_key()
    if not api_key: return {"error": "Falta configurar FIREBASE_WEB_KEY en secrets.toml"}

    # Endpoint oficial de Firebase para Login
    url = f"{URL_AUTH}:signInWithPassword?key={api_key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    
    try:
        resp = requests.post(url, json=payload)
        datos = resp.json()
        
        if "error" in datos:
            msg = datos["error"]["message"]
            if "INVALID_PASSWORD" in msg: return {"error": "Contraseña incorrecta."}
            if "EMAIL_NOT_FOUND" in msg: return {"error": "Este email no está registrado."}
            return {"error": f"Error Login: {msg}"}
            
        return datos # Éxito: contiene idToken y localId
        
    except Exception as e:
        return {"error": str(e)}

def sign_up(email, password):
    """
    Registra un NUEVO usuario.
    """
    api_key = obtener_key()
    if not api_key: return {"error": "Falta API Key"}

    # Endpoint oficial de Firebase para Registro
    url = f"{URL_AUTH}:signUp?key={api_key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    
    try:
        resp = requests.post(url, json=payload)
        datos = resp.json()
        
        if "error" in datos:
            msg = datos["error"]["message"]
            if "EMAIL_EXISTS" in msg: return {"error": "Este email ya está en uso."}
            if "WEAK_PASSWORD" in msg: return {"error": "La contraseña es muy débil (mínimo 6 caracteres)."}
            return {"error": f"Error Registro: {msg}"}
            
        return datos
        
    except Exception as e:
        return {"error": str(e)}