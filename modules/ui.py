import streamlit as st
from modules import database as db
from modules import roles
from modules import styles
import os
import base64
import time

# ==========================================
# 🛠️ UTILIDADES
# ==========================================
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return None

def spacer(height="20px"):
    st.markdown(f"<div style='height: {height};'></div>", unsafe_allow_html=True)

def simular_pago(nuevo_plan):
    with st.spinner(f"Procesando mejora a {nuevo_plan.upper()}..."):
        time.sleep(1.5)
        db.actualizar_plan_usuario(st.session_state.usuario, nuevo_plan)
        st.session_state.plan_actual = nuevo_plan
        st.toast(f"¡Plan {nuevo_plan.upper()} activado!", icon="🚀")
        time.sleep(1)
        st.rerun()

# ==========================================
# 🎨 COMPONENTES VISUALES
# ==========================================
def divider_gradiente():
    st.markdown("""
        <hr style="height: 1px; border: none; margin: 0px 0; 
        background: linear-gradient(90deg, transparent, #FF5F1F, #FFAA00, transparent); opacity: 0.5;">
    """, unsafe_allow_html=True)

def cargar_estilos_extra():
    st.markdown("""
        <style>
            /* 1. Botones Primarios (Degradado Naranja Kortexa) */
            section[data-testid="stSidebar"] button[kind="primary"] {
                background: linear-gradient(90deg, #FF5F1F 0%, #FFAA00 100%);
                border: none; color: white; font-weight: 600;
                transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(255, 95, 31, 0.2);
            }
            section[data-testid="stSidebar"] button[kind="primary"]:hover {
                transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255, 95, 31, 0.4);
            }

            /* 2. Badges y Textos */
            .plan-text { font-size: 0.9rem; color: #DDD; margin-bottom: 5px; }
            .plan-badge { font-weight: bold; color: #FFF; margin-left: 5px; }
            
            /* 3. Botón Popover (Papelera con Borde Degradado) */
            section[data-testid="stSidebar"] div[data-testid="stPopover"] > button {
                background: linear-gradient(#262730, #262730) padding-box, linear-gradient(90deg, #FF5F1F, #FFAA00) border-box;
                border: 2px solid transparent !important;
                border-radius: 50% !important;
                color: #FF5F1F !important;
                font-size: 14px !important; padding: 0px !important;
                width: 32px !important; height: 32px !important;
                min-height: 32px !important; /* Fix para evitar deformación */
                display: flex; align-items: center; justify-content: center;
                transition: all 0.3s ease;
            }
            section[data-testid="stSidebar"] div[data-testid="stPopover"] > button:hover {
                box-shadow: 0 0 10px rgba(255, 95, 31, 0.5);
                transform: scale(1.05); color: #FFAA00 !important;
            }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 💰 MODAL DE PRECIOS
# ==========================================
@st.dialog("Elige tu nivel de Inteligencia", width="large")
def mostrar_modal_precios():
    st.markdown("""
    <style>
        .price-card { background-color: #1E1E1E; border: 1px solid #333; border-radius: 15px; padding: 20px; text-align: center; height: 100%; transition: transform 0.2s; }
        .price-card:hover { transform: scale(1.03); border-color: #FF5F1F; }
        .p-title { font-size: 1.2rem; font-weight: bold; color: #FFF; margin-bottom: 10px; }
        .p-price { font-size: 2rem; font-weight: 800; color: #FF5F1F; }
        .p-feat { font-size: 0.9rem; color: #AAA; list-style: none; padding: 0; text-align: left; margin-top: 15px;}
        .p-feat li { margin-bottom: 8px; padding-left: 20px; position: relative; }
        .p-feat li::before { content: "✓"; color: #FF5F1F; position: absolute; left: 0; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="price-card"><div class="p-title">STARTER</div><div class="p-price">$0</div><ul class="p-feat"><li>IA Básica</li><li>Texto</li><li>Historial</li></ul></div>""", unsafe_allow_html=True)
        st.button("Tu Plan Actual", disabled=True, use_container_width=True, key="btn_free")
    with c2:
        st.markdown("""<div class="price-card" style="border-color: #FF5F1F;"><div class="p-title">PRO</div><div class="p-price">$9<small>/mo</small></div><ul class="p-feat"><li>IA Avanzada</li><li>Imágenes</li><li>Velocidad</li></ul></div>""", unsafe_allow_html=True)
        if st.button("🚀 Activar PRO", type="primary", use_container_width=True, key="btn_pro"): simular_pago("pro")
    with c3:
        st.markdown("""<div class="price-card" style="border-color: #FFD700;"><div class="p-title" style="color:#FFD700">BUSINESS</div><div class="p-price" style="color:#FFD700">$49<small>/mo</small></div><ul class="p-feat"><li>Modelo Ultra</li><li>Dashboard</li><li>Soporte VIP</li></ul></div>""", unsafe_allow_html=True)
        if st.button("🏢 Activar BIZ", use_container_width=True, key="btn_biz"): simular_pago("enterprise")

# ==========================================
# 🖥️ RENDERIZADO PRINCIPAL (SIDEBAR / LOGIN)
# ==========================================
def render_sidebar():
    styles.cargar_css()
    cargar_estilos_extra()

    # Ajuste fino del padding del sidebar
    st.markdown("""<style>section[data-testid="stSidebar"] div.block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; } div[data-testid="stSidebarUserContent"] { padding-top: 0rem !important; }</style>""", unsafe_allow_html=True)

    # ------------------------------------------
    # ESCENARIO A: NO LOGUEADO (LANDING PAGE)
    # ------------------------------------------
    if not st.session_state.usuario:
        # Usamos columnas [1, 2, 1] para centrar el contenido perfectamente en el medio
        col_izq, col_centro, col_der = st.columns([1, 2, 1]) 
        
        with col_centro:
            # 1. LOGO CENTRADO (Usamos flexbox container para asegurar centrado)
            if os.path.exists("logo.png"): 
                st.markdown('<div style="display: flex; justify-content: center; margin-bottom: 10px;">', unsafe_allow_html=True)
                st.image("logo.png", width=300)
                st.markdown('</div>', unsafe_allow_html=True)
            else: 
                st.markdown('<div class="brand-title" style="text-align: center;">KORTEXA AI</div>', unsafe_allow_html=True)
            
            # 2. TEXTOS CENTRADOS
            st.markdown('<div class="hero-subtitle" style="text-align: center; margin-top: -10px;">Ecosistema de Inteligencia Neuronal</div>', unsafe_allow_html=True)
            st.markdown("""
                <div style="text-align: center; color: #aaa; margin-bottom: 2rem; font-size: 0.95rem; line-height: 1.5;">
                    Bienvenido al núcleo Kortexa. Plataforma multimodal para análisis de datos, 
                    visión artificial y generación de contenido. Diseñado por DE Group para ofrecer 
                    <b>precisión profesional</b> con seguridad garantizada.
                </div>
            """, unsafe_allow_html=True)
            
            # 3. FORMULARIO DE ACCESO
            with st.container(border=True):
                t_login, t_crear = st.tabs(["Ingresar", "Registro"])
                
                with t_login:
                    with st.form("f_login"):
                        u = st.text_input("Usuario", key="u_log", placeholder="Ej: admin@kortexa.com")
                        p = st.text_input("Clave", type="password", key="p_log")
                        if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                            if db.login(u, p):
                                st.session_state.usuario = u
                                st.query_params["user_token"] = u 
                                st.rerun()
                            else: 
                                st.error("Usuario no encontrado.")
                
                with t_crear:
                    st.caption("Crea una cuenta nueva para acceder.")
                    with st.form("f_reg"):
                        nu = st.text_input("Usuario", key="u_new")
                        np = st.text_input("Clave", type="password", key="p_new")
                        if st.form_submit_button("Crear Cuenta", type="primary", use_container_width=True):
                            if db.crear_user(nu, np): 
                                st.session_state.usuario = nu
                                st.query_params["user_token"] = nu 
                                st.rerun()
                            else: st.error("Este usuario ya existe.")
                            
        return None, None, None, None, None

    # ------------------------------------------
    # ESCENARIO B: LOGUEADO (APP SIDEBAR)
    # ------------------------------------------
    else:
        try: plan_real = db.obtener_plan_usuario(st.session_state.usuario)
        except: plan_real = "free"
        st.session_state.plan_actual = plan_real

        with st.sidebar:
            # HEADER SIDEBAR
            c_logo, c_title = st.columns([0.6, 2.2])
            with c_logo: 
                if os.path.exists("icon.png"): st.image("icon.png", width=50)
                else: st.write("⚡")
            with c_title:
                st.markdown("""<div style='line-height: 1.1; margin-top: 5px;'><span style='font-weight: 800; font-size: 1.2rem; background: linear-gradient(90deg, #FF5F1F, #FFAA00); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>KORTEXA AI</span><br><span style='font-size: 0.75rem; color: #888;'>Inteligencia Neuronal</span></div>""", unsafe_allow_html=True)
            
            spacer("15px"); divider_gradiente(); spacer("15px")

            # INFO PLAN
            label_plan = "🌱 FREE" if plan_real == "free" else ("💎 PRO" if plan_real == "pro" else "⭐ BIZ")
            st.markdown(f"<div class='plan-text'>Plan actual: <span class='plan-badge'>{label_plan}</span></div>", unsafe_allow_html=True)
            if plan_real != "enterprise":
                if st.button("💎 Mejorar a Pro", type="primary", use_container_width=True): mostrar_modal_precios()
            
            spacer("15px"); divider_gradiente(); spacer("15px")

            # BOTÓN NUEVO CHAT
            if st.button("➕ Nuevo Chat", type="secondary", use_container_width=True):
                st.session_state.chat_id = None; st.rerun()

            spacer("15px"); divider_gradiente(); spacer("15px")

            # PANEL DE CONTROL
            st.caption("PANEL DE CONTROL")
            tareas = roles.obtener_tareas()
            try: idx = list(tareas.keys()).index(st.session_state.get("rol_actual", ""))
            except: idx = 0
            rol = st.selectbox("Rol:", list(tareas.keys()), index=idx, label_visibility="collapsed")

            with st.expander("Configuración", expanded=False):
                web = st.toggle("Internet", value=True)
                can_img = plan_real in ["pro", "enterprise"]
                img = st.toggle("Imágenes", value=False, disabled=not can_img)
                if not can_img: st.caption("🔒 Solo Pro")
                if plan_real == "enterprise":
                    st.caption("---")
                    st.checkbox("📊 CRM Live", value=True, disabled=True)
                up = st.file_uploader("Docs", label_visibility="collapsed")

            spacer("15px"); divider_gradiente(); spacer("15px")

            # HISTORIAL DE CHATS
            c_hist_title, c_spacer, c_hist_del = st.columns([2, 1, 1])
            with c_hist_title: st.caption("TUS CHATS")
            with c_spacer: st.empty()
            with c_hist_del:
                # Papelera con Popover
                with st.popover("🗑️", use_container_width=False, help="Gestionar historial"):
                    st.caption("Gestionar")
                    if st.button("Eliminar Chat Actual", type="primary", use_container_width=True):
                        if st.session_state.chat_id:
                            db.eliminar_chat(st.session_state.chat_id)
                            st.session_state.chat_id = None; st.rerun()
                        else: st.warning("No hay chat activo.")
                    st.markdown("""<hr style="height: 1px; border: none; margin: 5px 0 8px 0; background: linear-gradient(90deg, transparent, #FF5F1F, #FFAA00, transparent); opacity: 0.5;">""", unsafe_allow_html=True)
                    if st.button("Eliminar Todo", type="secondary", use_container_width=True):
                        db.eliminar_todo(st.session_state.usuario); st.session_state.chat_id = None; st.rerun()

            sesiones = db.obtener_sesiones(st.session_state.usuario)
            with st.container(height=200, border=False):
                if not sesiones: st.caption("Sin historial.")
                for sid, dat in sesiones:
                    bg_button = "secondary" 
                    label_btn = f"➤ {dat.get('titulo','Chat')[:18]}.." if sid == st.session_state.chat_id else f"{dat.get('titulo','Chat')[:18]}.."
                    if st.button(label_btn, key=sid, type=bg_button, use_container_width=True):
                        st.session_state.chat_id = sid; st.rerun()

            st.divider()
            with st.expander(f"👤 {st.session_state.usuario}", expanded=False):
                if st.button("🚪 Cerrar Sesión", use_container_width=True):
                    st.session_state.usuario = None; st.query_params.clear(); st.rerun()

        return rol, web, img, up, tareas

# ==========================================
# 🧩 FUNCIONES AUXILIARES
# ==========================================
def render_chat_msgs(msgs):
    if not msgs: return
    for m in msgs:
        avatar = "icon.png" if m["role"] == "assistant" and os.path.exists("icon.png") else ("👤" if m["role"] == "user" else None)
        with st.chat_message(m["role"], avatar=avatar):
            if m["content"].startswith("http") and " " not in m["content"]: st.image(m["content"], width=400)
            else: st.markdown(m["content"])

def render_welcome_screen(rol_desc):
    styles.render_welcome_html()
    c1, c2, c3 = st.columns(3)
    with c1: st.info("📊 **Análisis**\n\nSube excels o PDFs.")
    with c2: st.warning("❓ **Ayuda**\n\nPregúntame lo que sea.")
    with c3: st.success("🎨 **Arte**\n\nGenera imágenes (Pro).")

def render_mini_header(): st.caption("Kortexa AI System v3.0")