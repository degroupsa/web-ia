import streamlit as st

def cargar_css():
    st.markdown("""
        <style>
            /* =========================================
               1. LÍNEA SUPERIOR CON DEGRADADO (ACCENT)
               ========================================= */
            header::before {
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px; /* Grosor de la línea */
                background: linear-gradient(90deg, #FF5F1F, #FF0000, #FFAA00);
                z-index: 9999;
            }
            
            header {
                border-top: none !important;
            }

            /* =========================================
               2. CORRECCIONES DE ESPACIO (ZONAS ROJAS)
               ========================================= */
                
            section[data-testid="stSidebar"] > div {
                padding-top: 0rem !important; 
            }
            
            /* A. QUITAR ESPACIO DE ARRIBA (El que marcaste en negro) */
            section[data-testid="stSidebar"] .block-container {
                padding-top: 1rem !important; /* Dejamos 1rem mínimo para no chocar con la línea naranja */
                margin-top: -20px !important; /* Truco final: Subirlo a la fuerza si el padding falla */
            }

            /* 3. Ajuste del separador */
            [data-testid="stSidebar"] hr {
                margin-top: 0px !important;
                margin-bottom: 15px !important;
            }

            /* =========================================
               3. AJUSTES GENERALES
               ========================================= */
            .block-container { padding-top: 3rem; padding-bottom: 5rem; }
            #MainMenu { visibility: hidden; }
            footer { visibility: hidden; }
            
            /* =========================================
               4. SIDEBAR (FONDO Y TEXTOS)
               ========================================= */
            section[data-testid="stSidebar"] {
                background-color: #050505 !important;
                border-right: 1px solid #333 !important;
            }
            
            [data-testid="stSidebar"] * {
                color: #FFFFFF !important;
            }

            /* --- ALINEACIÓN DEL LOGO (FIX) --- */
            [data-testid="stSidebar"] [data-testid="stImage"] {
                padding-top: 0px !important;   
                margin-top: -13px !important;
                margin-left: 0px !important;   
                transform: scale(1.0);         
            }
            
            .logo-text-container {
                display: flex;
                flex-direction: column;
                justify-content: center;
                margin-top: -5px !important;
                padding-top: 0px; 
                margin-left: -15px !important;
            }

            .sidebar-brand {
                font-family: 'Inter', sans-serif;
                font-size: 20px; 
                font-weight: 800;
                background: linear-gradient(90deg, #FF5F1F, #FFAA00);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                line-height: 1.1;
                margin: 0; padding: 0;
            }
            
            .sidebar-caption {
                font-size: 10px !important;
                color: #BBBBBB !important;
                margin: 0; padding: 0;
                letter-spacing: 0.5px;
            }

            /* =========================================
               5. DROPDOWN (SELECTOR DE ROLES)
               ========================================= */
            div[data-baseweb="select"] > div {
                background-color: #1A1A1A !important;
                border: 1px solid #444 !important;
                color: #FFFFFF !important;
                border-radius: 8px !important;
            }
            div[data-baseweb="select"] span { color: #FFFFFF !important; }
            div[data-baseweb="select"] svg { fill: #FF5F1F !important; }

            ul[data-baseweb="menu"] {
                background-color: #111111 !important;
                border: 1px solid #FF5F1F !important;
                padding: 0px !important;
            }
            li[data-baseweb="option"] {
                color: #CCCCCC !important;
                padding: 10px !important;
            }
            li[data-baseweb="option"]:hover, 
            li[data-baseweb="option"][aria-selected="true"] {
                background-color: #FF5F1F !important;
                color: #FFFFFF !important;
                font-weight: bold !important;
            }

            /* =========================================
               6. BOTONES (SIN TOCAR INPUTS DE CHAT)
               ========================================= */
            button[kind="primary"], a[kind="primary"] {
                background-color: #FF5F1F !important;
                border: none !important;
                color: white !important;
                font-weight: 700 !important;
            }
            button[kind="primary"]:hover, a[kind="primary"]:hover {
                background-color: #FF884D !important;
            }

            /* =========================================
               7. PERFIL DE USUARIO
               ========================================= */
            .user-profile-compact {
                display: flex;
                align-items: center;
                padding: 10px;
                background: #111;
                border: 1px solid #333;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .user-avatar {
                width: 35px; height: 35px;
                background: #FF5F1F;
                border-radius: 50%;
                display: flex; justify-content: center; align-items: center;
                font-weight: bold; color: white;
                margin-right: 10px;
            }
            .user-info span { display: block; line-height: 1.2; }
            .user-name { font-size: 14px; font-weight: 600; color: white; }
            .user-role { font-size: 11px; color: #888; }
            
            /* TÍTULOS PANTALLA BIENVENIDA */
            .brand-title {
                font-family: 'Inter', sans-serif;
                font-weight: 800;
                font-size: 50px;
                text-align: center;
                background: linear-gradient(135deg, #FFFFFF 0%, #B0B0B0 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 10px;
                letter-spacing: -1.5px;
            }
            .hero-subtitle {
                font-family: 'Inter', sans-serif;
                font-weight: 500;
                font-size: 22px;
                text-align: center;
                color: #FF5F1F;
                margin-bottom: 20px;
            }
            .hero-text {
                font-family: 'Source Sans Pro', sans-serif;
                font-size: 17px;
                text-align: center;
                color: #999999;
                max-width: 800px;
                margin: 0 auto 40px auto;
                line-height: 1.6;
            }
            
            .info-grid {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-bottom: 50px;
                flex-wrap: wrap;
            }
            .info-box {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 15px 20px;
                text-align: center;
                min-width: 140px;
                display: flex;
                flex-direction: column;
                align-items: center;
                transition: transform 0.3s ease;
            }
            .info-box:hover {
                background: rgba(255, 255, 255, 0.06);
                transform: translateY(-5px);
                border-color: #FF5F1F;
            }
            .info-icon { font-size: 26px; margin-bottom: 8px; }
            .info-value { font-size: 15px; font-weight: 700; color: #E0E0E0; display: block; }
            .info-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
            .ig-link { text-decoration: none; color: #E0E0E0; }
            .ig-link:hover { color: #FF5F1F; }
            
            .separator {
                display: flex; align-items: center; text-align: center;
                color: #AAA; font-size: 12px; margin: 15px 0;
            }
            .separator::before, .separator::after {
                content: ''; flex: 1; border-bottom: 1px solid #444;
            }
            .separator::before { margin-right: 10px; }
            .separator::after { margin-left: 10px; }

        </style>
    """, unsafe_allow_html=True)

def render_welcome_html():
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 40px; margin-top: 20px;">
        <h1 style="background: linear-gradient(to right, #FF5F1F, #FF8C00); font-family: 'Roboto', sans-serif; -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 55px;">Hola! Soy Kortexa</h1>
        <h3 style="color: #E0E0E0; font-weight: 400; font-size: 20px;">Estoy aquí para potenciar tus proyectos. ¿En qué puedo ayudarte hoy?</h3>
        <p style="color: #999; font-size: 16px; margin-top: 10px;">Si eres nuevo en la app, <b>Puedo enseñarte a utilizarme!</b> Solo tiene que preguntarme, "Como funcionas?" o "Como te utilizo?"</p>
    </div>
    """, unsafe_allow_html=True)