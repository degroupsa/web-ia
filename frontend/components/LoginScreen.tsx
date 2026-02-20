import React, { useState } from "react";
import { Mail, Lock, ArrowRight, Brain, KeyRound, ShieldCheck, X } from "lucide-react";
// ⚠️ Asegúrate de que esta ruta es correcta según tu estructura
import { auth, googleProvider } from "../src/lib/firebaseConfig"; 
import { signInWithPopup, sendPasswordResetEmail } from "firebase/auth";

// Icono Google Original
const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 48 48">
    <path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8c-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C12.955 4 4 12.955 4 24s8.955 20 20 20s20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"/>
    <path fill="#FF3D00" d="m6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C16.318 4 9.656 8.337 6.306 14.691z"/>
    <path fill="#4CAF50" d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0 1 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z"/>
    <path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.087 5.571l.003-.002l6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z"/>
  </svg>
);

export default function LoginScreen({ onLoginSuccess }: { onLoginSuccess: (email: string, plan: string) => void }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [isRecovering, setIsRecovering] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  // Estado para manejar la animación de transición
  const [animating, setAnimating] = useState(false);

  // Lógica Google
  const handleGoogle = async () => {
    setError("");
    if (!auth) { setError("Error Config Firebase"); return; }
    try {
        const result = await signInWithPopup(auth, googleProvider);
        const res = await fetch("http://localhost:8000/api/auth/google", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: result.user.email }),
        });
        const data = await res.json();
        if(res.ok) onLoginSuccess(data.email, data.plan);
        else throw new Error(data.detail || "Error en backend");
    } catch(e:any) { 
        if(e.code !== 'auth/popup-closed-by-user') setError(e.message); 
    }
  };

  // Lógica Recuperar
  const handleRecover = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true); setError("");
    try {
        if (!auth) throw new Error("Falta Firebase");
        await sendPasswordResetEmail(auth, email);
        alert(`Correo de recuperación enviado a ${email}`); 
        setIsRecovering(false);
    } catch(e:any) { 
        if (e.code === 'auth/user-not-found') setError("Este correo no está registrado.");
        else setError(e.message); 
    } finally { setLoading(false); }
  };

  // Lógica Login/Registro
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true); setError("");
    const ep = isRegistering ? "/api/register" : "/api/login";
    try {
        const res = await fetch(`http://localhost:8000${ep}`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if(!res.ok) throw new Error(data.detail);
        
        if(isRegistering) { alert("Cuenta creada exitosamente."); setIsRegistering(false); }
        else onLoginSuccess(data.email, data.plan);
    } catch(e:any) { setError(e.message); } finally { setLoading(false); }
  };

  // Función para cambiar entre modos con animación
  const toggleRegister = () => {
    setAnimating(true);
    setError("");
    setTimeout(() => {
      setIsRegistering(!isRegistering);
      setAnimating(false);
    }, 300); // Duración de la transición
  };

  // --- VISTA RECUPERACIÓN (Compacta) ---
  if(isRecovering) return (
    <div className="flex h-screen w-full bg-[#0E1117] items-center justify-center relative overflow-hidden font-sans">
        <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-[#FF5F1F]/20 rounded-full blur-[120px]"></div>
        
        <div className="z-10 bg-[#1C1E24] border border-[#41444C] p-8 rounded-2xl w-full max-w-md shadow-2xl text-center animate-in fade-in zoom-in duration-300">
            <div className="mb-5 flex justify-center">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF5F1F] to-[#FFAA00] flex items-center justify-center shadow-lg shadow-orange-500/20">
                    <KeyRound className="text-white" size={20} />
                </div>
            </div>
            <h2 className="text-xl font-extrabold text-white mb-2">Reestablecer Contraseña</h2>
            <p className="text-[#9799A5] text-xs mb-6 leading-relaxed">Ingresa tu correo electrónico y te enviaremos un enlace de recuperación.</p>
            
            <form onSubmit={handleRecover} className="space-y-4">
                <div className="relative text-left">
                    <Mail className="absolute left-4 top-3.5 text-[#9799A5]" size={16}/>
                    <input value={email} onChange={e=>setEmail(e.target.value)} type="email" required 
                        className="w-full bg-[#0E1117] border border-[#41444C] text-white py-3 pl-12 pr-4 rounded-xl outline-none focus:border-[#FF5F1F] transition-all placeholder:text-[#444] text-sm" 
                        placeholder="usuario@empresa.com"/>
                </div>
                
                {error && <div className="bg-red-500/10 border border-red-500/50 text-red-500 text-xs p-2 rounded-lg font-medium">{error}</div>}
                
                <button disabled={loading} className="w-full bg-gradient-to-r from-[#FF5F1F] to-[#FFAA00] text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-orange-500/20 hover:scale-[1.02] transition-all disabled:opacity-50 text-sm">
                    {loading ? "Enviando..." : "Enviar Enlace"}
                </button>
            </form>
            <button onClick={()=>setIsRecovering(false)} className="mt-5 text-xs text-[#9799A5] hover:text-white underline underline-offset-4 bg-transparent border-none cursor-pointer transition-colors">Volver al inicio</button>
        </div>
    </div>
  );

  // --- VISTA PRINCIPAL LOGIN (Compacta & Enterprise con Animación) ---
  return (
    <div className="flex h-screen w-full bg-[#0E1117] items-center justify-center relative overflow-hidden font-sans">
      {/* Fondo Ambient */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-[#FF5F1F]/20 rounded-full blur-[120px]"></div>
      <div className="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-[#FFAA00]/10 rounded-full blur-[120px]"></div>

      <div className="z-10 bg-[#1C1E24] border border-[#41444C] p-8 rounded-2xl w-full max-w-sm shadow-[0_0_50px_rgba(0,0,0,0.5)] animate-in fade-in zoom-in duration-500">
        
        {/* Header Branding */}
        <div className="text-center mb-5">
            <div className="flex justify-center mb-3">
                <img src="/icon.png" alt="K" className="w-12 h-12 object-contain drop-shadow-md" onError={(e) => (e.currentTarget.style.display = "none")} />
            </div>
            <h1 className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-[#FF5F1F] to-[#FFAA00] tracking-tight">KORTEXA AI</h1>
            <p className="text-[#9799A5] text-[9px] uppercase tracking-[0.2em] mt-1 font-bold">Kortexa & DE Group Enterprise</p>
        </div>

        {/* Botón Google (Compacto) */}
        <button onClick={handleGoogle} className="w-full bg-white hover:bg-gray-100 text-[#1C1E24] font-bold py-2.5 rounded-xl flex items-center justify-center gap-2 mb-4 transition-all shadow-md active:scale-95 border-none cursor-pointer group text-sm">
            <div className="group-hover:scale-110 transition-transform"><GoogleIcon/></div>
            <span>Continuar con Google</span>
        </button>

        <div className="flex items-center gap-4 mb-4 opacity-40">
            <div className="h-[1px] bg-[#9799A5] flex-1"></div>
            <span className="text-[9px] text-[#9799A5] font-bold uppercase transition-all duration-300">
              {isRegistering ? "Registro con email" : "O con credenciales"}
            </span>
            <div className="h-[1px] bg-[#9799A5] flex-1"></div>
        </div>

        {/* Formulario con Animación */}
        <div className={`transition-all duration-300 transform ${animating ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'}`}>
          <form onSubmit={handleSubmit} className="space-y-3">
              <div className="relative group">
                  <Mail className="absolute left-4 top-3.5 text-[#555] group-focus-within:text-[#FF5F1F] transition-colors" size={16}/>
                  <input value={email} onChange={e=>setEmail(e.target.value)} required type="email" 
                      className="w-full bg-[#0E1117] border border-[#41444C] text-white py-3 pl-12 pr-4 rounded-xl outline-none focus:border-[#FF5F1F] focus:ring-1 focus:ring-[#FF5F1F]/50 transition-all placeholder:text-[#333] text-sm" 
                      placeholder="usuario@empresa.com"/>
              </div>
              
              <div className="relative group">
                  <Lock className="absolute left-4 top-3.5 text-[#555] group-focus-within:text-[#FF5F1F] transition-colors" size={16}/>
                  <input value={password} onChange={e=>setPassword(e.target.value)} required type="password" 
                      className="w-full bg-[#0E1117] border border-[#41444C] text-white py-3 pl-12 pr-4 rounded-xl outline-none focus:border-[#FF5F1F] focus:ring-1 focus:ring-[#FF5F1F]/50 transition-all placeholder:text-[#333] text-sm" 
                      placeholder="••••••••"/>
              </div>

              {error && <div className="bg-red-500/10 border border-red-500/50 text-red-500 text-xs p-2 rounded-lg font-medium flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-red-500"></div>{error}</div>}

              <button disabled={loading} className="w-full bg-gradient-to-r from-[#FF5F1F] to-[#FFAA00] text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-orange-500/20 hover:scale-[1.02] active:scale-95 transition-all border-none cursor-pointer flex items-center justify-center gap-2 text-xs uppercase tracking-wide mt-2">
                  {loading ? "Procesando..." : (isRegistering ? "CREAR CUENTA" : "INICIAR SESIÓN")} <ArrowRight size={16} />
              </button>
          </form>
        </div>

        {/* Footer Links */}
        <div className="mt-6 flex flex-col gap-3 text-center">
            {!isRegistering && (
              <button onClick={()=>setIsRecovering(true)} className="text-xs text-[#9799A5] hover:text-[#FF5F1F] bg-transparent border-none cursor-pointer flex justify-center items-center gap-1.5 transition-colors">
                  <KeyRound size={12}/> ¿Olvidaste tu contraseña?
              </button>
            )}
            <button onClick={toggleRegister} className="text-xs text-[#9799A5] transition-colors bg-transparent border-none cursor-pointer">
                {isRegistering ? "¿Ya tienes cuenta? " : "¿Nuevo Usuario? "}
                <span className="text-white font-bold hover:underline underline-offset-4">
                  {isRegistering ? "Inicia Sesión" : "Regístrate"}
                </span>
            </button>
        </div>

        <div className="mt-6 flex justify-center gap-2 opacity-20 items-center">
            <ShieldCheck size={15} color="#3cff00" className="text-white"/> <span className="text-[8px] text-white uppercase tracking-[0.2em] font-bold">Cifrado de Extremo a Extremo</span>
        </div>
      </div>
    </div>
  );
}