import sys
import os
import re
import time
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

import stripe
import mercadopago

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Importamos módulos propios
from modules import cerebro, database as db

# --- INICIALIZACIÓN PASARELAS PAGO ---
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
mp_access_token = os.environ.get("MERCADOPAGO_ACCESS_TOKEN")
mp_sdk = mercadopago.SDK(mp_access_token) if mp_access_token else None

# --- INICIALIZACIÓN DE LA APP ---
app = FastAPI(title="Kortexa Enterprise API v5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DATOS ---
class AuthRequest(BaseModel):
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    email: str

class RecoveryRequest(BaseModel):
    email: str

class ChatRequest(BaseModel):
    user_id: str
    message: str
    role: str = "Asistente General (Multimodal)"
    image_mode: bool = False
    internet_mode: bool = True
    chat_id: Optional[str] = None
    file_data: Optional[str] = None 
    file_mime: Optional[str] = None

class CheckoutRequest(BaseModel):
    email: str
    plan: str
    provider: str

# --- EVENTO DE INICIO ---
@app.on_event("startup")
async def startup_event():
    print("🚀 [SISTEMA] Iniciando Servidor Kortexa v5.0...")
    if db.init_db():
        if not db.existe_usuario("admin@kortexa.com.ar"):
            db.crear_user("admin@kortexa.com.ar", "admin123")
            db.actualizar_plan_usuario("admin@kortexa.com.ar", "pro")
        print("✅ [SISTEMA] Base de datos conectada.")
    else:
        print("❌ [CRÍTICO] No se pudo conectar a Firebase.")

# --- ENDPOINTS DE AUTENTICACIÓN ---
@app.post("/api/register")
async def register_user(req: AuthRequest):
    try:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", req.email): raise HTTPException(status_code=400, detail="Formato inválido.")
        if db.existe_usuario(req.email): raise HTTPException(status_code=400, detail="El usuario ya existe.")
        if db.crear_user(req.email, req.password): return {"status": "ok", "message": "Usuario registrado exitosamente."}
        else: raise HTTPException(status_code=500, detail="Error DB.")
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/login")
async def login_user(req: AuthRequest):
    try:
        if not db.existe_usuario(req.email): raise HTTPException(status_code=404, detail="El usuario no existe.")
        res = db.verificar_credenciales(req.email, req.password)
        if res: return {"status": "ok", "email": res["username"], "plan": res["plan"]}
        else:
            time.sleep(0.5)
            raise HTTPException(status_code=401, detail="Contraseña incorrecta.")
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/google")
async def auth_google(req: GoogleAuthRequest):
    try:
        resultado = db.login_con_google(req.email)
        if resultado: return {"status": "ok", "email": req.email, "plan": resultado['plan']}
        else: raise HTTPException(status_code=500, detail="Error sync Google.")
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/recover")
async def recover_password(req: RecoveryRequest):
    if not db.existe_usuario(req.email): raise HTTPException(status_code=404, detail="Correo no registrado.")
    return {"status": "ok"}

# ==========================================
# 🔥 ENDPOINT DEL CHAT CON LIMITES ACTIVOS 🔥
# ==========================================
@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        if not db.existe_usuario(req.user_id): 
            return {"response": "🚫 Acceso Denegado.", "chat_id": None}

        plan_actual = db.obtener_plan_usuario(req.user_id)
        
        # 1. VERIFICAMOS SI TIENE CUOTA DISPONIBLE ANTES DE LLAMAR A LA IA
        puede_usar, mensaje_limite = db.verificar_y_consumir_cuota(req.user_id, plan_actual, req.image_mode)
        
        # Aseguramos un chat_id para poder mostrar el mensaje de límite en pantalla
        chat_id = req.chat_id
        if not chat_id: chat_id = db.crear_sesion(req.user_id, req.role, req.message)

        # Si llegó al límite, bloqueamos la petición y le decimos que mejore su plan
        if not puede_usar:
            db.guardar_msg(req.user_id, chat_id, "user", req.message)
            db.guardar_msg(req.user_id, chat_id, "assistant", mensaje_limite)
            return {"response": mensaje_limite, "chat_id": chat_id, "plan": plan_actual}

        # 2. SI TIENE CUOTA, PROCEDEMOS NORMALMENTE
        db.guardar_msg(req.user_id, chat_id, "user", req.message)
        historial = db.cargar_msgs(req.user_id, chat_id)

        respuesta_completa = ""
        generador = cerebro.chat_con_gemini(
            mensaje_usuario=req.message, 
            mensaje_con_contexto=req.message, 
            historial_previo=historial, 
            nombre_rol_actual=req.role, 
            plan=plan_actual, 
            token=None, 
            usar_img_toggle=req.image_mode,
            usar_internet_toggle=req.internet_mode,
            archivo_base64=req.file_data,
            mime_type=req.file_mime
        )
        
        for chunk in generador: respuesta_completa += chunk

        if "⚠️" not in respuesta_completa:
            db.guardar_msg(req.user_id, chat_id, "assistant", respuesta_completa)

        return {"response": respuesta_completa, "chat_id": chat_id, "plan": plan_actual}
    except Exception as e:
        print(f"❌ Error en chat: {e}")
        return {"response": "⚠️ Error del Sistema Neuronal.", "chat_id": req.chat_id}

# --- ENDPOINTS DE HISTORIAL ---
@app.get("/api/history")
def get_history(user_id: str):
    try: return [{"id": s[0], "title": s[1]['titulo'], "date": str(s[1]['timestamp'])[:10]} for s in db.obtener_sesiones(user_id)]
    except: return []

@app.get("/api/history/{chat_id}")
def get_chat_details(chat_id: str, user_id: str):
    try: return db.cargar_msgs(user_id, chat_id)
    except: return []

@app.delete("/api/history/clear")
async def clear_all_history(user_id: str):
    try:
        if db.eliminar_todos_chats(user_id): return {"status": "ok", "message": "Historial purgado."}
        raise HTTPException(status_code=500, detail="Error BD.")
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history/{chat_id}")
def delete_chat(chat_id: str):
    try:
        if db.eliminar_chat(chat_id): return {"status": "ok"}
        raise HTTPException(status_code=500, detail="Fallo borrado.")
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 🔥 ENDPOINT DE PAGOS (CHECKOUT) 🔥
# ==========================================
@app.post("/api/checkout")
async def create_checkout(request: CheckoutRequest):
    email = request.email
    plan = request.plan
    provider = request.provider

    domain_url = os.environ.get("DOMINIO_FRONTEND", "http://localhost:3010")

    precios_usd = {"pro": 1500, "business": 4900} # 🔥 PRO ACTUALIZADO A $15
    precios_ars = {"pro": 18000, "business": 58000} # Ajusta en ARS según cotización

    # --- LÓGICA STRIPE ---
    if provider == "stripe":
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="Falta configurar la Key de Stripe")
        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=email,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': f'Kortexa AI - Plan {plan.capitalize()}'},
                        'unit_amount': precios_usd.get(plan, 1500),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{domain_url}/?success=true",
                cancel_url=f"{domain_url}/?canceled=true",
                metadata={"email": email, "plan": plan}
            )
            return {"url": checkout_session.url}
        except Exception as e:
            print(f"❌ ERROR EXACTO DE STRIPE: {e}") 
            raise HTTPException(status_code=400, detail=str(e))

    # --- LÓGICA MERCADO PAGO ---
    elif provider == "mercadopago":
        if not mp_sdk:
            raise HTTPException(status_code=500, detail="Falta configurar la Key de Mercado Pago")
        try:
            preference_data = {
                "items": [{
                    "title": f"Kortexa AI - Plan {plan.capitalize()}",
                    "quantity": 1,
                    "unit_price": float(precios_ars.get(plan, 18000)),
                    "currency_id": "ARS"
                }],
                "payer": {"email": email},
                "metadata": {"email": email, "plan": plan}
            }
            
            preference_response = mp_sdk.preference().create(preference_data)
            
            if "response" in preference_response and "init_point" in preference_response["response"]:
                return {"url": preference_response["response"]["init_point"]}
            else:
                print(f"❌ ERROR RESPUESTA MERCADO PAGO: {preference_response}")
                raise HTTPException(status_code=400, detail=str(preference_response))
                
        except Exception as e:
            print(f"❌ ERROR EXACTO DE MERCADO PAGO: {e}") 
            raise HTTPException(status_code=400, detail=str(e))

    raise HTTPException(status_code=400, detail="Proveedor de pago no válido")

# ==========================================
# 🔥 WEBHOOKS: ACTUALIZACIÓN AUTOMÁTICA DE PLANES 🔥
# ==========================================
@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET") 

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e: return HTTPException(status_code=400, detail="Payload inválido")
    except stripe.error.SignatureVerificationError as e: return HTTPException(status_code=400, detail="Firma inválida")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session.get('metadata', {}).get('email')
        plan = session.get('metadata', {}).get('plan')
        
        if email and plan:
            print(f"💰 [STRIPE] ¡Pago recibido! Actualizando a {email} al plan {plan.upper()}")
            db.actualizar_plan_usuario(email, plan)

    return {"status": "success"}

@app.post("/api/webhook/mercadopago")
async def mercadopago_webhook(request: Request):
    body = await request.json()
    
    if body.get("type") == "payment" or body.get("topic") == "payment":
        payment_id = body.get("data", {}).get("id") or request.query_params.get("id")
        
        if payment_id and mp_sdk:
            try:
                payment_info = mp_sdk.payment().get(payment_id)
                payment = payment_info.get("response", {})
                
                if payment.get("status") == "approved":
                    metadata = payment.get("metadata", {})
                    email = metadata.get("email")
                    plan = metadata.get("plan")
                    
                    if email and plan:
                        print(f"💰 [MERCADO PAGO] ¡Pago recibido! Actualizando a {email} al plan {plan.upper()}")
                        db.actualizar_plan_usuario(email, plan)
            except Exception as e:
                print(f"❌ Error verificando pago en MP: {e}")
                
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)