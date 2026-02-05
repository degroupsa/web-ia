import sqlite3
import hashlib
import uuid
import datetime

DB_NAME = "kortexa_db.sqlite"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla Usuarios
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password_hash TEXT,
            plan TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Tabla Chats
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            username TEXT,
            titulo TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(username) REFERENCES usuarios(username)
        )
    ''')
    # Tabla Mensajes
    c.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES chats(id)
        )
    ''')
    conn.commit()
    conn.close()

# --- USUARIOS ---
def crear_user(username, password):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO usuarios (username, password_hash, plan) VALUES (?, ?, 'free')", (username, pwd_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login(username, password):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM usuarios WHERE username=? AND password_hash=?", (username, pwd_hash))
    user = c.fetchone()
    conn.close()
    return user is not None

def obtener_plan_usuario(username):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT plan FROM usuarios WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    if res: return res[0]
    return "free"

def actualizar_plan_usuario(username, nuevo_plan):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET plan=? WHERE username=?", (nuevo_plan, username))
    conn.commit()
    conn.close()

# --- CHATS ---
def crear_sesion(username, rol, primer_mensaje):
    init_db()
    chat_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    titulo = primer_mensaje[:30] + "..."
    c.execute("INSERT INTO chats (id, username, titulo) VALUES (?, ?, ?)", (chat_id, username, titulo))
    conn.commit()
    conn.close()
    return chat_id

def obtener_sesiones(username):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, titulo, timestamp FROM chats WHERE username=? ORDER BY timestamp DESC", (username,))
    data = c.fetchall()
    conn.close()
    return [(row[0], {'titulo': row[1], 'timestamp': row[2]}) for row in data]

def cargar_msgs(username, chat_id):
    if not chat_id: return []
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role, content FROM mensajes WHERE chat_id=? ORDER BY id ASC", (chat_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

def guardar_msg(username, chat_id, role, content):
    if not chat_id: return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO mensajes (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, role, content))
    conn.commit()
    conn.close()

# --- FUNCIONES DE BORRADO (LAS QUE NECESITAS) ---

def eliminar_chat(chat_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Primero mensajes, luego el chat (por integridad referencial)
    c.execute("DELETE FROM mensajes WHERE chat_id=?", (chat_id,))
    c.execute("DELETE FROM chats WHERE id=?", (chat_id,))
    conn.commit()
    conn.close()

def eliminar_todo(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Subquery para borrar mensajes de todos los chats de ese usuario
    c.execute("DELETE FROM mensajes WHERE chat_id IN (SELECT id FROM chats WHERE username=?)", (username,))
    c.execute("DELETE FROM chats WHERE username=?", (username,))
    conn.commit()
    conn.close()