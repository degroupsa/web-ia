import streamlit as st
import requests
import urllib.parse

# Configuración
try:
    CLIENT_ID = st.secrets["google"]["client_id"]
    CLIENT_SECRET = st.secrets["google"]["client_secret"]
    REDIRECT_URI = st.secrets["google"]["redirect_uri"]
except:
    # Valores dummy para que no rompa si no hay secretos aun
    CLIENT_ID = ""
    CLIENT_SECRET = ""
    REDIRECT_URI = ""

# URLs de Google
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

def get_login_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    return f"{AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}"

def get_user_info(auth_code):
    try:
        token_data = {
            "code": auth_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token_r = requests.post(TOKEN_URL, data=token_data)
        token_r.raise_for_status()
        token_json = token_r.json()
        access_token = token_json.get("access_token")

        headers = {"Authorization": f"Bearer {access_token}"}
        user_r = requests.get(USER_INFO_URL, headers=headers)
        user_r.raise_for_status()
        return user_r.json()
    except Exception as e:
        return None