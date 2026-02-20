import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import uuid
import datetime
import os

# Variable global
db = None

def init_db():
    global db
    try:
        if not firebase_admin._apps:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(current_dir)
            cred_path = os.path.join(backend_dir, "firebase_key.json")
            
            if not os.path.exists(cred_path):
                print(f"❌ [DB] Faltan credenciales en: {cred_path}")
                return False
            
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("🔥 [DB] Firebase Conectado.")
        
        db = firestore.client()
        return True
    except Exception as e:
        print(f"❌ [DB] Error init: {e}")
        return False

# --- USUARIOS ---

def existe_usuario(email):
    if db is None: init_db()
    try:
        return db.collection('usuarios').document(email).get().exists
    except: return False

def crear_user(email, password):
    if db is None: init_db()
    try:
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        user_data = {
            'username': email,
            'password_hash': pwd_hash,
            'plan': 'starter',
            'auth_method': 'email',
            'created_at': datetime.datetime.now(),
            'usage': {
                'daily_text': 0,
                'daily_images': 0,
                'lifetime_images': 0,
                'last_reset': datetime.datetime.now().strftime("%Y-%m-%d")
            }
        }
        db.collection('usuarios').document(email).set(user_data)
        return True
    except Exception as e:
        print(f"Error crear: {e}")
        return False

def login_con_google(email):
    if db is None: init_db()
    try:
        doc_ref = db.collection('usuarios').document(email)
        doc = doc_ref.get()
        
        if doc.exists:
            plan = doc.to_dict().get('plan', 'starter')
            # 🔥 AUTO-MIGRACIÓN: Si es viejo, lo actualizamos a starter
            if plan == 'free':
                doc_ref.update({'plan': 'starter'})
                plan = 'starter'
            return {"status": "ok", "plan": plan}
        else:
            user_data = {
                'username': email,
                'plan': 'starter',
                'auth_method': 'google',
                'created_at': datetime.datetime.now(),
                'usage': {
                    'daily_text': 0,
                    'daily_images': 0,
                    'lifetime_images': 0,
                    'last_reset': datetime.datetime.now().strftime("%Y-%m-%d")
                }
            }
            doc_ref.set(user_data)
            return {"status": "ok", "plan": "starter"}
    except Exception as e:
        print(f"Error Google: {e}")
        return None

def verificar_credenciales(email, password):
    if db is None: init_db()
    try:
        doc_ref = db.collection('usuarios').document(email)
        doc = doc_ref.get()
        if not doc.exists: return None
        
        data = doc.to_dict()
        if data.get('auth_method') == 'google': return None

        pwd_hash_input = hashlib.sha256(password.encode()).hexdigest()
        if data.get('password_hash') == pwd_hash_input:
            plan = data.get('plan', 'starter')
            # 🔥 AUTO-MIGRACIÓN: Si es viejo, lo actualizamos a starter
            if plan == 'free':
                doc_ref.update({'plan': 'starter'})
                plan = 'starter'
            return {"plan": plan, "username": email}
        return None
    except: return None

# --- CHATS ---

def obtener_plan_usuario(email):
    if db is None: init_db()
    try:
        doc_ref = db.collection('usuarios').document(email)
        doc = doc_ref.get()
        if doc.exists:
            plan = doc.to_dict().get('plan', 'starter')
            # 🔥 AUTO-MIGRACIÓN: Actualización silenciosa de fondo
            if plan == 'free':
                doc_ref.update({'plan': 'starter'})
                plan = 'starter'
            return plan
        return 'starter'
    except: return 'starter'

def actualizar_plan_usuario(email, plan):
    if db is None: init_db()
    try: db.collection('usuarios').document(email).update({'plan': plan})
    except: pass

def crear_sesion(email, rol, mensaje):
    if db is None: init_db()
    try:
        chat_id = str(uuid.uuid4())
        db.collection('chats').document(chat_id).set({
            'id': chat_id, 'username': email, 'rol': rol,
            'titulo': mensaje[:30]+"...", 'timestamp': datetime.datetime.now()
        })
        return chat_id
    except: return None

def guardar_msg(email, chat_id, role, content):
    if db is None: init_db()
    try:
        db.collection('chats').document(chat_id).collection('mensajes').add({
            'role': role, 'content': content, 'timestamp': datetime.datetime.now()
        })
    except: pass

def cargar_msgs(email, chat_id):
    if db is None: init_db()
    try:
        docs = db.collection('chats').document(chat_id).collection('mensajes').order_by('timestamp').stream()
        return [{'role': d.to_dict()['role'], 'content': d.to_dict()['content']} for d in docs]
    except: return []

def obtener_sesiones(email):
    if db is None: init_db()
    try:
        docs = db.collection('chats').where('username', '==', email).stream()
        sesiones = [(d.id, d.to_dict()) for d in docs]
        sesiones.sort(key=lambda x: x[1].get('timestamp', ''), reverse=True)
        return sesiones
    except: return []

def eliminar_chat(chat_id):
    if db is None: init_db()
    try:
        msgs = db.collection('chats').document(chat_id).collection('mensajes').stream()
        for m in msgs: m.reference.delete()
        db.collection('chats').document(chat_id).delete()
        return True
    except: return False

def eliminar_todos_chats(email):
    if db is None: init_db()
    try:
        docs = db.collection('chats').where('username', '==', email).stream()
        count = 0
        for doc in docs:
            msgs = doc.reference.collection('mensajes').stream()
            for m in msgs:
                m.reference.delete()
            doc.reference.delete()
            count += 1
        return True
    except Exception as e:
        print(f"Error borrando todo: {e}")
        return False

# ==========================================
# 🔥 CEREBRO FINANCIERO: CONTROL DE LÍMITES 🔥
# ==========================================

def verificar_y_consumir_cuota(email: str, plan: str, is_image: bool) -> tuple[bool, str]:
    if db is None: init_db()
    
    try:
        user_ref = db.collection('usuarios').document(email)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return False, "Usuario no encontrado."

        data = user_doc.to_dict()
        hoy = datetime.datetime.now().strftime("%Y-%m-%d") 
        
        usage_data = data.get('usage', {})
        last_reset = usage_data.get('last_reset', "")
        
        if last_reset != hoy:
            usage_data['daily_text'] = 0
            usage_data['daily_images'] = 0
            usage_data['last_reset'] = hoy

        daily_text = usage_data.get('daily_text', 0)
        daily_images = usage_data.get('daily_images', 0)
        lifetime_images = usage_data.get('lifetime_images', 0)

        limites = {
            "starter": {"text": 20, "daily_img": 0, "lifetime_img": 5},
            "pro": {"text": 200, "daily_img": 30, "lifetime_img": 999999},
            "business": {"text": 1000, "daily_img": 150, "lifetime_img": 999999}
        }
        
        plan_actual = plan.lower()
        if plan_actual not in limites: plan_actual = "starter"

        l_texto = limites[plan_actual]["text"]
        l_img_diaria = limites[plan_actual]["daily_img"]
        l_img_vida = limites[plan_actual]["lifetime_img"]

        if is_image:
            if plan_actual == "starter":
                if lifetime_images >= l_img_vida:
                    return False, "🖼️ **Límite alcanzado:** Has usado tus 5 imágenes HD de prueba. ¡Actualiza al **Plan Pro** para desbloquear Kortexa Studio! ✨"
                usage_data['lifetime_images'] = lifetime_images + 1
            else:
                if daily_images >= l_img_diaria:
                    return False, f"⏳ **Límite de Uso Justo:** Has alcanzado tu máximo de {l_img_diaria} imágenes por hoy. Vuelve mañana para seguir creando."
                usage_data['daily_images'] = daily_images + 1

        else:
            if daily_text >= l_texto:
                if plan_actual == "starter":
                    return False, "⚡ **Límite alcanzado:** Has agotado tus 20 mensajes diarios de prueba. ¡Pásate al **Plan Pro** para potenciar tu flujo de trabajo sin interrupciones!"
                else:
                    return False, "🛡️ **Protección de red:** Has alcanzado el límite de seguridad de alto rendimiento por hoy. Tu cuota se reiniciará a la medianoche."
            usage_data['daily_text'] = daily_text + 1

        user_ref.update({'usage': usage_data})
        return True, ""

    except Exception as e:
        print(f"❌ Error interno validando cuota: {e}")
        return True, ""