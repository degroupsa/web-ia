"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Send, Menu, Plus, MessageSquare, User, Zap,
  ChevronLeft, ChevronDown, Trash2, LogOut, Brain, UploadCloud,
  Globe, ImageIcon, BarChart3, HelpCircle, Palette, Check, MoreVertical,
  Copy, Download, FileText, Table, FileIcon, Paperclip, X, ShieldAlert, Play
} from "lucide-react";
import ReactMarkdown from "react-markdown";

// 🔥 LIBRERÍA DE DISEÑO DE CÓDIGO 🔥
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Importamos componentes
import PricingModal from "../components/PricingModal";
import LoginScreen from "../components/LoginScreen";
import ConfirmationModal from "../components/ConfirmationModal";

interface Message { role: "user" | "assistant"; content: string; }
interface ChatSession { id: string; title: string; date: string; }

// ==========================================
// 🔥 NUEVO: RENDERIZADOR AVANZADO CON VISTA PREVIA WEB 🔥
// ==========================================
const CodeBlockRenderer = ({ inline, className, children, onCopy, ...props }: any) => {
  const match = /language-(\w+)/.exec(className || "");
  const codeString = String(children).replace(/\n$/, "");
  const isHtml = match && match[1] === "html";
  const [viewMode, setViewMode] = useState<'code' | 'preview'>('code');

  if (!inline && match) {
    return (
      <div className="relative group/code mt-4 mb-4 rounded-xl overflow-hidden shadow-2xl border border-[#41444C] bg-[#0E1117]">
        <div className="flex items-center justify-between bg-[#1C1E24] px-4 py-2 border-b border-[#41444C]">
          <div className="flex items-center gap-4">
            <span className="text-[10px] text-[#9799A5] uppercase font-bold tracking-wider">
              {match[1]}
            </span>
            
            {/* Si es HTML, mostramos el switch de Vista Previa */}
            {isHtml && (
              <div className="flex bg-[#0E1117] rounded-md p-0.5 border border-[#41444C]">
                <button
                  onClick={() => setViewMode('code')}
                  className={`text-[9px] px-3 py-1 rounded-sm uppercase font-bold transition-all border-none cursor-pointer ${viewMode === 'code' ? 'bg-[#FF5F1F] text-white shadow-md' : 'bg-transparent text-[#9799A5] hover:text-white'}`}
                >
                  Código
                </button>
                <button
                  onClick={() => setViewMode('preview')}
                  className={`flex items-center gap-1 text-[9px] px-3 py-1 rounded-sm uppercase font-bold transition-all border-none cursor-pointer ${viewMode === 'preview' ? 'bg-[#FF5F1F] text-white shadow-md' : 'bg-transparent text-[#9799A5] hover:text-white'}`}
                >
                  <Play size={10} /> Vista Previa
                </button>
              </div>
            )}
          </div>

          <button
            onClick={() => {
              navigator.clipboard.writeText(codeString);
              if (onCopy) onCopy("✅ Código copiado al portapapeles");
            }}
            className="text-[#9799A5] hover:text-[#FF5F1F] transition-colors p-1 bg-transparent border-none cursor-pointer"
            title="Copiar código"
          >
            <Copy size={14} />
          </button>
        </div>
        
        {/* Renderizado Condicional: Código vs Web en Vivo */}
        {viewMode === 'preview' && isHtml ? (
           <div className="bg-white w-full h-[500px] overflow-hidden">
             <iframe 
               srcDoc={codeString} 
               className="w-full h-full border-none bg-white" 
               sandbox="allow-scripts allow-modals"
               title="Vista Previa Kortexa"
             />
           </div>
        ) : (
          <SyntaxHighlighter
            {...props}
            style={vscDarkPlus}
            language={match[1]}
            PreTag="div"
            className="!m-0 !bg-[#0E1117] text-[13px] scrollbar-thin max-h-[500px]"
            showLineNumbers={true}
          >
            {codeString}
          </SyntaxHighlighter>
        )}
      </div>
    );
  }
  return (
    <code {...props} className={`${className} bg-[#1C1E24] text-[#FF5F1F] px-1.5 py-0.5 rounded-md text-[13px] font-mono`}>
      {children}
    </code>
  );
};


// ==========================================
// APP PRINCIPAL
// ==========================================
export default function KortexaPage() {
  const [authData, setAuthData] = useState<{email:string, plan:string} | null>(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true); 
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingText, setLoadingText] = useState("CARGANDO RESPUESTA DEL NÚCLEO...");
  const [chatHistory, setChatHistory] = useState<ChatSession[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  
  const [currentRole, setCurrentRole] = useState("Asistente General (Multimodal)");
  const [useInternet, setUseInternet] = useState(true);
  const [useImages, setUseImages] = useState(false);
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [showPricing, setShowPricing] = useState(false);
  
  const [showInputMenu, setShowInputMenu] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [suggestionAlert, setSuggestionAlert] = useState<string | null>(null);
  
  const [isDeletingChats, setIsDeletingChats] = useState(false);
  const [deletingChatId, setDeletingChatId] = useState<string | null>(null); 
  const [showSecurityAlert, setShowSecurityAlert] = useState<{role: string, type: 'legal' | 'health' | 'security'} | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLDivElement>(null); 
  const toggleMenuRef = useRef<HTMLButtonElement>(null); 
  
  const [confirmModal, setConfirmModal] = useState({ 
    isOpen: false, title: "", message: "", action: () => {}, isDanger: false 
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // RECUPERAR SESIÓN
  useEffect(() => {
    const savedSession = sessionStorage.getItem("kortexa_session");
    if (savedSession) {
      try { setAuthData(JSON.parse(savedSession)); } catch (e) {}
    }
    setIsCheckingSession(false);
  }, []);

  // CERRAR MENÚ AL CLIC AFUERA
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        showInputMenu && 
        menuRef.current && 
        !menuRef.current.contains(event.target as Node) &&
        toggleMenuRef.current && 
        !toggleMenuRef.current.contains(event.target as Node)
      ) {
        setShowInputMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showInputMenu]);

  // OCULTAR TOAST
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  useEffect(() => { if (authData) fetchHistory(authData.email); }, [authData]);
  useEffect(() => { if (authData) messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isLoading, authData]);

  useEffect(() => {
    if (messages.length === 0) return;
    const lastMsg = messages[messages.length - 1];
    if (lastMsg.role === 'assistant') {
      const regex = /💡\s*\**Sugerencia Kortexa:?\**\s*Para obtener un resultado de nivel experto en este tema, te recomiendo cambiar al modo\s*\**(.*?)\**\s*en el panel lateral\.?/i;
      const match = lastMsg.content.match(regex);
      if (match) {
        setSuggestionAlert(match[1].trim());
        setTimeout(() => setSuggestionAlert(null), 10000);
      }
    }
  }, [messages]);

  const fetchHistory = async (email: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/history?user_id=${email}`);
      if (res.ok) setChatHistory(await res.json());
    } catch (e) { console.error(e); }
  };

  const handleLogout = () => { 
      setAuthData(null); 
      sessionStorage.removeItem("kortexa_session");
      setMessages([]); 
      setChatHistory([]); 
      setActiveChatId(null); 
      setAttachedFile(null); 
  };

  const determineLoadingState = (text: string) => {
    const lower = text.toLowerCase();
    if (attachedFile) return `ANALIZANDO ARCHIVO: ${attachedFile.name.toUpperCase()}...`;
    if (lower.includes("imag") || lower.includes("dibuj")) return "DISEÑANDO EN KORTEXA STUDIO...";
    if (lower.includes("analiz") || lower.includes("dato") || lower.includes("excel")) return "ANALIZANDO CONJUNTO DE DATOS...";
    if (lower.includes("busc") || lower.includes("web")) return "NAVEGANDO EN LA RED GLOBAL...";
    return "CARGANDO RESPUESTA DEL NÚCLEO...";
  };

  const triggerDeleteSingle = (chatId: string) => {
    setConfirmModal({
        isOpen: true, title: "Eliminar Chat", message: "¿Estás seguro de que deseas eliminar este chat? Esta acción no se puede deshacer.", isDanger: true,
        action: async () => {
            setConfirmModal(prev => ({...prev, isOpen: false})); 
            setDeletingChatId(chatId); 
            try {
                await fetch(`http://localhost:8000/api/history/${chatId}`, { method: "DELETE" });
                setChatHistory(prev => prev.filter(c => c.id !== chatId));
                if (activeChatId === chatId) { setMessages([]); setActiveChatId(null); }
            } catch (e) { alert("Error al eliminar"); }
            finally { setDeletingChatId(null); }
        }
    });
  };

  const triggerDeleteAll = () => {
    if (chatHistory.length === 0) return;
    setConfirmModal({
        isOpen: true, title: "⚠️ Eliminar todas las Conversaciones", message: "Estás a punto de eliminar TODAS tus conversaciones. Esto borrará permanentemente toda la información en la nube. ¿Confirmar eliminación?", isDanger: true,
        action: async () => {
            setConfirmModal(prev => ({...prev, isOpen: false}));
            setIsDeletingChats(true);
            try {
                const res = await fetch(`http://localhost:8000/api/history/clear?user_id=${authData?.email}`, { method: "DELETE" });
                if (res.ok) { 
                    setChatHistory([]); 
                    setMessages([]); 
                    setActiveChatId(null); 
                } 
                else { throw new Error("Error Interno"); }
            } catch (e) { 
                alert("No se pudo eliminar el historial."); 
            } finally {
                setIsDeletingChats(false);
            }
        }
    });
  };

  const handleSelectChat = async (id: string) => {
    setActiveChatId(id); setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/history/${id}?user_id=${authData?.email}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.map((m: any) => ({ role: m.role === "model" ? "assistant" : m.role, content: m.content })));
      }
    } catch (e) { console.error(e); } finally { setIsLoading(false); }
  };

  const handleRoleChange = (newRole: string) => {
    setSuggestionAlert(null);
    if (newRole.includes("Abogado") || newRole.includes("Legal")) {
        setShowSecurityAlert({role: newRole, type: 'legal'});
    } else if (newRole.includes("Psicólogo") || newRole.includes("Asistencia Psicológica")) {
        setShowSecurityAlert({role: newRole, type: 'health'});
    } else if (newRole.includes("Hacker") || newRole.includes("Ciberseguridad")) {
        setShowSecurityAlert({role: newRole, type: 'security'});
    } else {
        setCurrentRole(newRole);
    }
  };

  const handleCopyLastMessage = () => {
    const lastMsg = [...messages].reverse().find(m => m.role === 'assistant');
    if (lastMsg) { 
        const cleanContent = lastMsg.content.replace(/💡\s*\**Sugerencia Kortexa:?\**\s*Para obtener un resultado de nivel experto en este tema, te recomiendo cambiar al modo\s*\**(.*?)\**\s*en el panel lateral\.?/gi, "").trim();
        navigator.clipboard.writeText(cleanContent); 
        setToastMessage("✅ Última respuesta copiada al portapapeles");
    }
    setShowInputMenu(false);
  };

  const handleExportTXT = () => {
    if (messages.length === 0) return;
    const textData = messages.map(m => {
        const cleanContent = m.role === 'assistant' ? m.content.replace(/💡\s*\**Sugerencia Kortexa:?\**\s*Para obtener un resultado de nivel experto en este tema, te recomiendo cambiar al modo\s*\**(.*?)\**\s*en el panel lateral\.?/gi, "").trim() : m.content;
        return `${m.role === 'user' ? 'OPERADOR' : 'KORTEXA AI'}:\n${cleanContent}\n\n`;
    }).join('---\n');
    descargarArchivo(textData, 'txt', 'text/plain');
  };

  const handleExportDocs = () => {
    if (messages.length === 0) return;
    const textData = messages.map(m => {
        const cleanContent = m.role === 'assistant' ? m.content.replace(/💡\s*\**Sugerencia Kortexa:?\**\s*Para obtener un resultado de nivel experto en este tema, te recomiendo cambiar al modo\s*\**(.*?)\**\s*en el panel lateral\.?/gi, "").trim() : m.content;
        return `${m.role === 'user' ? 'OPERADOR' : 'KORTEXA AI'}:\n${cleanContent}\n\n`;
    }).join('---\n');
    descargarArchivo(textData, 'doc', 'application/msword');
  };

  const handleExportSheets = () => {
    if (messages.length === 0) return;
    const csvData = "Rol,Mensaje\n" + messages.map(m => {
        const cleanContent = m.role === 'assistant' ? m.content.replace(/💡\s*\**Sugerencia Kortexa:?\**\s*Para obtener un resultado de nivel experto en este tema, te recomiendo cambiar al modo\s*\**(.*?)\**\s*en el panel lateral\.?/gi, "").trim() : m.content;
        return `"${m.role === 'user' ? 'Operador' : 'Kortexa'}","${cleanContent.replace(/"/g, '""')}"`;
    }).join('\n');
    descargarArchivo(csvData, 'csv', 'text/csv;charset=utf-8;');
  };

  const handleExportPDF = () => {
    if (messages.length === 0) return;
    const printWindow = window.open('', '', 'height=600,width=800');
    if (printWindow) {
        const html = `
            <html><head><title>Kortexa Chat Export</title>
            <style>body{font-family:sans-serif; padding:20px; color:#333;} .msg{margin-bottom:20px; padding:15px; border-radius:10px;} .user{background:#f0f0f0;} .ai{background:#fff3e0; border-left:4px solid #ff5f1f;} h4{margin:0 0 10px 0; color:#555;}</style>
            </head><body>
            <h2>Reporte de Inteligencia Neuronal - Kortexa AI</h2><hr/>
            ${messages.map(m => {
                const cleanContent = m.role === 'assistant' ? m.content.replace(/💡\s*\**Sugerencia Kortexa:?\**\s*Para obtener un resultado de nivel experto en este tema, te recomiendo cambiar al modo\s*\**(.*?)\**\s*en el panel lateral\.?/gi, "").trim() : m.content;
                return `<div class="msg ${m.role === 'user' ? 'user' : 'ai'}"><h4>${m.role === 'user' ? '👤 Operador' : '🧠 Kortexa AI'}</h4><p>${cleanContent.replace(/\n/g, '<br/>')}</p></div>`;
            }).join('')}
            </body></html>
        `;
        printWindow.document.write(html);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => { printWindow.print(); printWindow.close(); }, 500);
    }
    setShowInputMenu(false);
  };

  const descargarArchivo = (data: string, extension: string, type: string) => {
    const blob = new Blob([data], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `Kortexa_Export_${new Date().toISOString().slice(0,10)}.${extension}`;
    a.click(); URL.revokeObjectURL(url);
    setShowInputMenu(false);
    setToastMessage(`✅ Archivo .${extension} descargado correctamente`);
  };

  const handleClearScreen = () => { setMessages([]); setActiveChatId(null); setShowInputMenu(false); setAttachedFile(null); };

  const handleSendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault(); 
    if ((!inputValue.trim() && !attachedFile) || isLoading) return;
    
    let userText = inputValue; 
    let fileBase64: string | null = null;
    let fileMime: string | null = null;

    if (attachedFile) {
        const reader = new FileReader();
        const filePromise = new Promise<string>((resolve) => {
            reader.onload = () => resolve((reader.result as string).split(',')[1]);
            reader.readAsDataURL(attachedFile);
        });
        fileBase64 = await filePromise;
        fileMime = attachedFile.type;
        
        if (!userText) {
            userText = `Analiza este archivo: ${attachedFile.name}`;
        } else {
            userText = `[📄 Archivo adjunto: ${attachedFile.name}]\n` + userText;
        }
    }

    setInputValue("");
    setShowInputMenu(false);
    setSuggestionAlert(null); 

    setLoadingText(determineLoadingState(userText));
    setMessages(prev => [...prev, { role: "user", content: userText }]);
    setIsLoading(true);

    try {
      setAttachedFile(null); 

      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            user_id: authData?.email, 
            message: userText, 
            role: currentRole, 
            image_mode: useImages, 
            internet_mode: useInternet,
            chat_id: activeChatId,
            file_data: fileBase64,
            file_mime: fileMime
        }),
      });
      const data = await response.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.response }]);
      if (data.chat_id && data.chat_id !== activeChatId) { setActiveChatId(data.chat_id); fetchHistory(authData!.email); }
    } catch (e) { setMessages(prev => [...prev, { role: "assistant", content: "⚠️ Error de conexión." }]); } 
    finally { setIsLoading(false); }
  };

  if (isCheckingSession) {
    return (
      <div className="flex h-screen w-full bg-[#0E1117] items-center justify-center">
        <div className="w-10 h-10 border-4 border-[#FF5F1F] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!authData) return <LoginScreen onLoginSuccess={(e, p) => {
      setAuthData({email:e, plan:p});
      sessionStorage.setItem("kortexa_session", JSON.stringify({email:e, plan:p}));
  }} />;

  return (
    <div className="flex h-screen w-full bg-[#0E1117] text-[#FAFAFA] overflow-hidden font-sans relative">
      <PricingModal isOpen={showPricing} onClose={() => setShowPricing(false)} userEmail={authData.email} />
      <ConfirmationModal isOpen={confirmModal.isOpen} onClose={() => setConfirmModal(prev => ({...prev, isOpen: false}))} onConfirm={confirmModal.action} title={confirmModal.title} message={confirmModal.message} isDanger={confirmModal.isDanger} />

      {/* 🔥 ALERTA FLOTANTE (TOAST) MEJORADA 🔥 */}
      {toastMessage && (
          <div className="absolute top-6 left-1/2 transform -translate-x-1/2 z-[110] animate-in fade-in slide-in-from-top-4 duration-300">
              <div className="bg-[#1C1E24] border border-[#FF5F1F]/50 shadow-[0_0_20px_rgba(255,95,31,0.2)] rounded-xl p-4 flex items-center gap-3">
                  <Check size={20} className="text-[#FF5F1F]" />
                  <p className="text-sm text-white font-medium m-0">{toastMessage}</p>
              </div>
          </div>
      )}

      {showSecurityAlert && (
          <div className="absolute inset-0 bg-[#0E1117]/90 backdrop-blur-xl z-[100] flex items-center justify-center p-6">
              <div className="bg-[#1C1E24] border-2 border-red-500 shadow-[0_0_50px_rgba(239,68,68,0.3)] rounded-3xl p-8 max-w-lg w-full text-center animate-in zoom-in-95">
                  <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                      <ShieldAlert size={32} className="text-red-500" />
                  </div>
                  <h2 className="text-2xl font-black text-white uppercase tracking-tighter mb-4">Protocolo de Seguridad Activado</h2>
                  <p className="text-[#9799A5] text-sm leading-relaxed mb-8">
                      Estás intentando acceder al módulo de <span className="text-white font-bold">{showSecurityAlert.role}</span>. 
                      Kortexa AI es una herramienta de asistencia neuronal y no reemplaza el consejo profesional humano calificado. 
                      El uso indebido de herramientas de seguridad o asesoramiento para fines ilícitos o de salud crítica está estrictamente prohibido.
                  </p>
                  <div className="flex flex-col gap-3">
                      <button 
                          onClick={() => { setCurrentRole(showSecurityAlert.role); setShowSecurityAlert(null); }}
                          className="w-full py-4 bg-red-500 hover:bg-red-600 border-none cursor-pointer text-white font-black uppercase tracking-widest rounded-xl transition-all shadow-lg"
                      >
                          Aceptar Responsabilidad
                      </button>
                      <button 
                          onClick={() => setShowSecurityAlert(null)}
                          className="w-full py-4 bg-transparent border-none cursor-pointer text-[#9799A5] hover:text-white font-bold uppercase text-xs transition-all"
                      >
                          Cancelar y volver
                      </button>
                  </div>
              </div>
          </div>
      )}

      <div className="absolute top-0 left-0 w-full h-[4px] bg-gradient-to-r from-[#FF5F1F] to-[#FFAA00] z-50 shadow-[0_0_15px_rgba(255,95,31,0.6)]"></div>

      <aside className={`${isSidebarOpen ? "w-[21rem]" : "w-0"} h-full bg-[#262730] border-r border-[#41444C] transition-all duration-300 ease-in-out flex flex-col relative z-40 overflow-hidden shrink-0`}>
        <div className="flex flex-col h-full min-w-[21rem]">
          <div className="p-5 pt-8 text-left">
             <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                   <img src="/icon.png" alt="Logo" className="w-10 h-10 object-contain drop-shadow-md" onError={(e) => e.currentTarget.style.display='none'} />
                   <div className="flex flex-col justify-center">
                      <h1 className="text-xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-[#FF5F1F] to-[#FFAA00] leading-tight m-0">KORTEXA AI</h1>
                      <span className="text-[10px] text-[#9799A5] tracking-[0.2em] uppercase font-semibold">Inteligencia Neuronal</span>
                   </div>
                </div>
                <button onClick={() => setIsSidebarOpen(false)} className="text-[#9799A5] hover:text-white bg-transparent border-none cursor-pointer"><ChevronLeft size={20} /></button>
             </div>
             <div className="mb-2 text-sm text-[#FAFAFA] font-medium flex items-center gap-2">
             <span className="text-[#FAFAFA]">Plan actual:</span> 
              <span className="font-bold text-white flex items-center gap-1 uppercase">
            {authData.plan === 'pro' ? '💎' : authData.plan === 'business' ? '⭐' : '⚡'} {authData.plan}
            </span>
             </div>
             <button onClick={() => setShowPricing(true)} className="w-full py-2 px-4 rounded-md bg-gradient-to-r from-[#FF5F1F] to-[#FFAA00] text-white font-bold text-sm shadow-lg hover:opacity-90 transition-all flex items-center justify-center gap-2 border-none cursor-pointer">
               <Zap size={16} fill="currentColor" /> Mejorar a Pro
             </button>
          </div>

          <div className="px-4 pb-4 border-b border-[#41444C]/30 text-left">
             <button onClick={() => {setMessages([]); setActiveChatId(null); setInputValue(""); setAttachedFile(null); setSuggestionAlert(null);}} className="w-full py-2.5 px-4 rounded-md border border-[#41444C] text-[#FAFAFA] bg-[#262730] hover:bg-[#1C1E24] hover:text-[#FF5F1F] hover:border-[#FF5F1F] transition-all flex items-center justify-center gap-2 text-sm font-medium cursor-pointer"><Plus size={16} /> Nuevo Chat</button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6 scrollbar-thin text-left">
            <div className="space-y-3">
              <span className="text-[10px] font-bold text-[#9799A5] uppercase tracking-wider pl-1">Configuración del Nodo</span>
              <div className="relative group">
                <select value={currentRole} onChange={(e) => handleRoleChange(e.target.value)} className="w-full bg-[#1C1E24] text-[#FAFAFA] border border-[#41444C] text-xs rounded-md p-2.5 pr-8 appearance-none focus:border-[#FF5F1F] outline-none cursor-pointer">
                  <option>Asistente General (Multimodal)</option>
                  <option>Kortexa Art Director</option>
                  <option>Diseñador de Logos & Branding</option>
                  <option>Fotógrafo Hiperrealista</option>
                  <option>Ilustrador Anime / Manga</option>
                  <option>Arquitecto de Interiores 3D</option>
                  <option>Diseñador de Tatuajes</option>
                  <option>Diseño de Moda y Ropa</option>
                  <option>Cineasta / Director de Cine</option>
                  <option>Consultor de Negocios (CEO)</option>
                  <option>Experto en Marketing & Ads</option>
                  <option>Experto en Instagram (Reels/Post)</option>
                  <option>Guionista de TikTok Viral</option>
                  <option>Copywriter (Diseñador de Copy)</option>
                  <option>Especialista SEO (Marketing Digital)</option>
                  <option>Community Manager</option>
                  <option>Creador de Nombres (Naming)</option>
                  <option>Product Manager (PM)</option>
                  <option>Diseñador UX / UX Writer</option>
                  <option>Analista de Métricas y KPIs</option>
                  <option>Comercial de Ventas (Negociación)</option>
                  <option>Asistencia para Emprendedores (PMV)</option>
                  <option>Ingeniero de Prompts</option>
                  <option>Arquitecto de Software</option>
                  <option>Full Stack (Diseñador Web)</option>
                  <option>Experto en Python & Data</option>
                  <option>Hacker Ético / Ciberseguridad</option>
                  <option>Desarrollador Móvil</option>
                  <option>Ingeniero DevOps</option>
                  <option>Analista de Datos (PDF/Excel)</option>
                  <option>Abogado Consultor</option>
                  <option>Recursos Humanos - CV</option>
                  <option>Experto en Excel</option>
                  <option>Redactor de Correos</option>
                  <option>Investigador Académico</option>
                  <option>Profesor de Idiomas</option>
                  <option>Traductor Universal</option>
                  <option>Asesor Financiero</option>
                  <option>Chef Ejecutivo</option>
                  <option>Entrenador Fitness & Salud</option>
                  <option>Asistencia Psicológica</option>
                  <option>Asesor de Viajes</option>
                  <option>Experto en Vinos</option>
                </select>
                <ChevronDown className="absolute right-3 top-3 text-[#9799A5] pointer-events-none" size={14} />
              </div>
              <div className="bg-[#1C1E24]/50 border border-[#41444C] rounded-md p-3 space-y-3">
                 <button className="w-full flex items-center justify-between text-left group bg-transparent border-none cursor-pointer" onClick={() => setUseInternet(!useInternet)}>
                    <div className="flex items-center gap-2 text-xs text-[#DDD]"><Globe size={14} className={useInternet ? "text-[#FF5F1F]" : "text-gray-500"} /> <span>Busqueda en Internet</span></div>
                    <div className={`w-8 h-4 rounded-full relative transition-colors ${useInternet ? "bg-[#FF5F1F]" : "bg-[#41444C]"}`}><div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all ${useInternet ? 'left-[18px]' : 'left-0.5'}`}></div></div>
                 </button>
                 <button className="w-full flex items-center justify-between text-left group bg-transparent border-none cursor-pointer" onClick={() => setUseImages(!useImages)}>
                    <div className="flex items-center gap-2 text-xs text-[#DDD]"><ImageIcon size={14} className={useImages ? "text-[#FF5F1F]" : "text-gray-500"} /> <span>Kortexa Studio (Pro)</span></div>
                    <div className={`w-8 h-4 rounded-full relative transition-colors ${useImages ? "bg-[#FF5F1F]" : "bg-[#41444C]"}`}><div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all ${useImages ? 'left-[18px]' : 'left-0.5'}`}></div></div>
                 </button>
              </div>
            </div>

            <div className="space-y-2">
               <div className="flex items-center justify-between pl-1">
                 <span className="text-[10px] font-bold text-[#9799A5] uppercase tracking-wider">Tus Conversaciones</span>
                 <button onClick={triggerDeleteAll} className="text-[#9799A5] hover:text-[#FF4B4B] p-1 rounded bg-transparent border-none cursor-pointer" title="Eliminar todo el historial"><Trash2 size={14} /></button>
               </div>
               <div className="space-y-1">
                 {isDeletingChats ? (
                     <div className="flex flex-col items-center justify-center py-6">
                        <div className="w-5 h-5 border-2 border-[#FF5F1F] border-t-transparent rounded-full animate-spin mb-2"></div>
                        <span className="text-[9px] text-[#FF5F1F] font-bold uppercase tracking-widest animate-pulse">Eliminando Conversaciones...</span>
                     </div>
                 ) : chatHistory.length === 0 ? (
                     <div className="text-center py-4 opacity-50"><MessageSquare size={24} className="mx-auto mb-1" /><p className="text-[10px]">No hay Conversaciones</p></div>
                 ) : (
                   chatHistory.map((chat) => (
                     <div key={chat.id} className="group relative">
                          <button onClick={() => handleSelectChat(chat.id)} className={`w-full text-left flex items-center gap-3 p-2.5 rounded-md text-xs transition-all border-l-2 cursor-pointer border-y-0 border-r-0 ${activeChatId === chat.id ? "bg-[#1C1E24] text-white border-[#FF5F1F] shadow-sm" : "text-[#9799A5] border-transparent hover:bg-[#1C1E24] hover:text-[#DDD]"}`}>
                              
                              {deletingChatId === chat.id ? (
                                  <div className="w-3.5 h-3.5 border-2 border-[#FF5F1F] border-t-transparent rounded-full animate-spin shrink-0"></div>
                              ) : (
                                  <MessageSquare size={14} className={`shrink-0 ${activeChatId === chat.id ? "text-[#FF5F1F]" : "text-[#555]"}`} />
                              )}

                              <div className="flex-1 min-w-0"><span className="block truncate font-medium">{chat.title}</span><span className="block text-[9px] opacity-60 mt-0.5">{chat.date}</span></div>
                          </button>
                          <button onClick={(e) => {e.stopPropagation(); triggerDeleteSingle(chat.id);}} className="absolute right-2 top-3 p-1.5 text-red-500 opacity-0 group-hover:opacity-100 bg-transparent border-none cursor-pointer transition-opacity hover:bg-red-500/10 rounded-md" disabled={deletingChatId === chat.id}><Trash2 size={14} /></button>
                     </div>
                   ))
                 )}
               </div>
            </div>
          </div>

          <div className="p-4 border-t border-[#41444C] bg-[#1C1E24]/50 backdrop-blur-sm text-left">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#FF5F1F] to-[#FFAA00] flex items-center justify-center text-white font-bold text-xs shadow-md">{authData.email.substring(0, 1).toUpperCase()}</div>
              <div className="flex-1 overflow-hidden"><p className="text-xs font-bold text-white truncate m-0">{authData.email}</p><div className="flex items-center gap-2 mt-0.5"><div className="w-1.5 h-1.5 rounded-full bg-green-500"></div><span className="text-[9px] text-[#9799A5]">Online</span></div></div>
              <button onClick={handleLogout} className="text-[#9799A5] hover:text-white p-1.5 hover:bg-[#41444C] rounded-md transition-colors bg-transparent border-none cursor-pointer"><LogOut size={14} /></button>
            </div>
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col relative h-full">
        {suggestionAlert && (
            <>
                <div 
                    className="absolute inset-0 bg-[#0E1117]/70 backdrop-blur-sm z-40 animate-in fade-in duration-500 cursor-pointer" 
                    onClick={() => setSuggestionAlert(null)}
                ></div>
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 animate-in fade-in zoom-in-95 duration-500">
                    <div className="bg-[#1C1E24] border-2 border-[#FF5F1F] shadow-[0_0_100px_rgba(255,95,31,0.5)] rounded-2xl p-5 flex items-start gap-4 max-w-md w-full">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF5F1F] to-[#FFAA00] flex items-center justify-center shrink-0 shadow-lg">
                            <Brain size={20} className="text-white" />
                        </div>
                        <div className="flex-1 text-left">
                            <h4 className="text-[#FF5F1F] font-black text-[10px] uppercase tracking-widest mb-1 m-0">Sugerencia de Kortexa AI</h4>
                            <p className="text-sm text-[#FAFAFA] leading-relaxed m-0">
                                Para obtener una respuesta de un experto en este tema, se recomienda cambiar al rol <span className="font-bold text-[#FFAA00] uppercase">{suggestionAlert}</span> en el panel desplegable izquierdo.
                            </p>
                        </div>
                        <button onClick={() => setSuggestionAlert(null)} className="text-[#9799A5] hover:text-white transition-colors bg-transparent border-none cursor-pointer p-1">
                            <X size={16} />
                        </button>
                    </div>
                </div>
            </>
        )}

        {!isSidebarOpen && <button onClick={() => setIsSidebarOpen(true)} className="absolute top-4 left-4 z-50 p-2 bg-[#262730] border border-[#41444C] rounded-md text-[#9799A5] hover:text-[#FF5F1F] shadow-lg cursor-pointer"><Menu size={20} /></button>}

        <div className="pt-8 pb-2 px-8 flex flex-col gap-2 text-left border-b border-[#41444C]/30">
           <div className="flex items-center gap-2"><Brain className="text-[#FAFAFA]" size={24} /><h2 className="text-xl font-bold text-[#FAFAFA] m-0">Núcleo Central de Kortexa AI</h2></div>
           <div><span className="inline-block border border-[#FF5F1F] text-[#FF5F1F] text-[9px] font-black px-3 py-1 rounded-full uppercase bg-[#1C1E24] tracking-wide mb-2">MODO: {currentRole}</span></div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 md:px-12 pb-40 scrollbar-thin text-left">
           {messages.length === 0 ? (
             <div className="flex flex-col items-center justify-center mt-12 max-w-4xl mx-auto animate-in fade-in duration-700 slide-in-from-bottom-4">
                <Brain size={56} className="text-[#FF5F1F] mb-6 drop-shadow-[0_0_15px_rgba(255,95,31,0.5)]" />
                <h1 className="font-black italic text-4xl md:text-5xl font-extrabold mb-3 text-center tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-[#FF5F1F] to-[#FFAA00] uppercase pr-2">
                  Hola! Soy Kortexa AI
                </h1>
                <p className="text-base text-[#9799A5] font-medium text-center m-0 mb-6">
                  Sistema de Inteligencia Neuronal | <span className="text-[#FF5F1F] font-bold italic">Kortexa & DE Group Enterprise</span>
                </p>
                <div className="flex items-center gap-4 opacity-40 mb-12 w-full max-w-xs justify-center">
                  <div className="h-[1px] flex-1 bg-white"></div>
                  <p className="text-[10px] text-white uppercase tracking-[0.3em] font-bold m-0 shrink-0">Kortexa v3.0</p>
                  <div className="h-[1px] flex-1 bg-white"></div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full px-4 max-w-3xl">
                   <button onClick={() => setInputValue("Quiero analizar un archivo de datos...")} className="bg-[#1C1E24] border border-[#41444C] p-6 rounded-2xl text-left hover:border-[#FF5F1F] hover:shadow-[0_0_20px_rgba(255,95,31,0.1)] transition-all group cursor-pointer flex flex-col gap-3">
                      <BarChart3 size={28} className="text-[#FF5F1F] group-hover:scale-110 transition-transform" />
                      <h3 className="font-black tracking-tighter uppercase text-sm text-white m-0">Análisis de Datos</h3>
                      <p className="text-xs text-[#9799A5] leading-relaxed m-0">Carga de archivos y procesamiento complejo de información estructurada.</p>
                   </button>
                   <button onClick={() => setInputValue("Genera un diseño en alta resolución de...")} className="bg-[#1C1E24] border border-[#41444C] p-6 rounded-2xl text-left hover:border-[#FFAA00] hover:shadow-[0_0_20px_rgba(255,170,0,0.1)] transition-all group cursor-pointer flex flex-col gap-3">
                      <Palette size={28} className="text-[#FFAA00] group-hover:scale-110 transition-transform" />
                      <h3 className="font-black tracking-tighter uppercase text-sm text-white m-0">Kortexa Studio</h3>
                      <p className="text-xs text-[#9799A5] leading-relaxed m-0">Generación de archivos visuales en alta resolución mediante prompts avanzados.</p>
                   </button>
                </div>
             </div>
           ) : (
             <div className="max-w-3xl mx-auto space-y-8 pt-4">
               {messages.map((msg, i) => {
                 let displayContent = msg.content;
                 if (msg.role === 'assistant') {
                    displayContent = displayContent.replace(/💡\s*\**Sugerencia Kortexa:?\**\s*Para obtener un resultado de nivel experto en este tema, te recomiendo cambiar al modo\s*\**(.*?)\**\s*en el panel lateral\.?/gi, "").trim();
                 }

                 return (
                 <div key={i} className={`flex gap-5 ${msg.role === "user" ? "justify-end" : "justify-start"} group animate-in fade-in duration-300`}>
                    {msg.role === "assistant" && <div className="w-9 h-9 rounded-lg bg-[#1C1E24] border border-[#41444C] flex items-center justify-center shrink-0 mt-1 shadow-sm overflow-hidden"><img src="/icon.png" className="w-6 h-6 object-contain" onError={(e) => e.currentTarget.style.display='none'} /></div>}
                    <div className={`max-w-[85%] px-6 py-4 rounded-2xl shadow-md ${msg.role === "user" ? "bg-[#262730] border border-[#41444C] text-[#FAFAFA] rounded-tr-sm" : "bg-transparent text-[#FAFAFA] w-full"}`}>
                      {msg.role === "assistant" ? (
                        
                        // 🔥 AQUI LLAMAMOS AL NUEVO RENDERIZADOR COMPLETO 🔥
                        <div className="markdown-body prose prose-invert max-w-none text-sm leading-relaxed">
                          <ReactMarkdown
                            components={{
                              code(props: any) {
                                return <CodeBlockRenderer {...props} onCopy={(m: string) => setToastMessage(m)} />;
                              }
                            }}
                          >
                            {displayContent}
                          </ReactMarkdown>
                        </div>

                      ) : (
                        <p className="text-sm">{displayContent}</p>
                      )}
                    </div>
                    {msg.role === "user" && <div className="w-9 h-9 rounded-lg bg-[#262730] border border-[#41444C] flex items-center justify-center shrink-0 mt-1 shadow-sm"><User size={18} className="text-[#9799A5]" /></div>}
                 </div>
                 )
               })}
               
               {isLoading && (
                 <div className="flex items-center gap-3 ml-14 mt-4 animate-in fade-in duration-300">
                    <div className="w-2.5 h-2.5 bg-[#FF5F1F] rounded-full animate-ping"></div>
                    <span className="text-[10px] text-[#FF5F1F] font-black uppercase tracking-widest italic animate-pulse">
                        {loadingText}
                    </span>
                 </div>
               )}
               <div ref={messagesEndRef} />
             </div>
           )}
        </div>

        <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-[#0E1117] via-[#0E1117] to-transparent pt-12 pb-6 px-4">
           <div className="max-w-3xl mx-auto relative">
              
              {showInputMenu && (
                <div ref={menuRef} className="absolute bottom-[4.5rem] left-2 w-56 bg-[#1C1E24] border border-[#41444C] rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.8)] p-2 flex flex-col gap-1 z-50 animate-in fade-in slide-in-from-bottom-2">
                  <div className="px-2 py-1 mb-1"><span className="text-[9px] text-[#9799A5] uppercase font-bold tracking-widest">Herramientas</span></div>
                  <button onClick={handleCopyLastMessage} type="button" className="flex items-center gap-3 text-xs text-[#DDD] hover:text-white hover:bg-[#262730] p-2.5 rounded-lg transition-colors text-left border-none cursor-pointer">
                    <Copy size={14} className="text-[#FF5F1F]"/> Copiar última respuesta
                  </button>
                  <div className="px-2 py-1 mt-1"><span className="text-[9px] text-[#9799A5] uppercase font-bold tracking-widest">Exportar</span></div>
                  <button onClick={handleExportPDF} type="button" className="flex items-center gap-3 text-xs text-[#DDD] hover:text-white hover:bg-[#262730] p-2.5 rounded-lg transition-colors text-left border-none cursor-pointer">
                    <FileIcon size={14} className="text-red-400"/> A formato PDF
                  </button>
                  <button onClick={handleExportDocs} type="button" className="flex items-center gap-3 text-xs text-[#DDD] hover:text-white hover:bg-[#262730] p-2.5 rounded-lg transition-colors text-left border-none cursor-pointer">
                    <FileText size={14} className="text-blue-400"/> A Google Docs (Word)
                  </button>
                  <button onClick={handleExportSheets} type="button" className="flex items-center gap-3 text-xs text-[#DDD] hover:text-white hover:bg-[#262730] p-2.5 rounded-lg transition-colors text-left border-none cursor-pointer">
                    <Table size={14} className="text-green-400"/> A Google Sheets (CSV)
                  </button>
                  <div className="h-[1px] bg-[#41444C] my-1 mx-2"></div>
                  <button onClick={handleClearScreen} type="button" className="flex items-center gap-3 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 p-2.5 rounded-lg transition-colors text-left border-none cursor-pointer">
                    <Trash2 size={14} /> Limpiar Chat
                  </button>
                </div>
              )}

              {attachedFile && (
                <div className="absolute -top-10 left-4 bg-[#262730] border border-[#FF5F1F]/50 text-[#DDD] text-xs px-3 py-1.5 rounded-lg flex items-center gap-2 shadow-lg animate-in slide-in-from-bottom-2">
                    <Paperclip size={12} className="text-[#FF5F1F]" />
                    <span className="max-w-[200px] truncate font-medium">{attachedFile.name}</span>
                    <button type="button" onClick={() => setAttachedFile(null)} className="ml-2 text-[#9799A5] hover:text-white bg-transparent border-none cursor-pointer p-0.5 rounded-full hover:bg-[#41444C]">
                        <X size={12} />
                    </button>
                </div>
              )}

              <form onSubmit={handleSendMessage} className="relative flex items-center bg-[#262730] border border-[#41444C] rounded-2xl shadow-2xl focus-within:border-[#FF5F1F] transition-all">
                 <button ref={toggleMenuRef} onClick={() => setShowInputMenu(!showInputMenu)} type="button" className="pl-4 pr-1 text-[#9799A5] hover:text-white transition-colors bg-transparent border-none cursor-pointer">
                   <MoreVertical size={20} />
                 </button>
                 <input type="file" className="hidden" ref={fileInputRef} onChange={(e) => e.target.files && setAttachedFile(e.target.files[0])} />
                 <button onClick={() => fileInputRef.current?.click()} type="button" className="px-2 text-[#9799A5] hover:text-white transition-colors bg-transparent border-none cursor-pointer" title="Adjuntar documento o imagen">
                   <Paperclip size={18} />
                 </button>
                 
                 <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} placeholder="Escribe tu mensaje a Kortexa..." className="w-full bg-transparent border-none text-white px-2 py-4 focus:ring-0 placeholder-[#9799A5] outline-none" />
                 
                 <button type="submit" disabled={(!inputValue.trim() && !attachedFile) || isLoading} className={`absolute right-2 p-2.5 rounded-xl transition-all border-none cursor-pointer flex items-center justify-center ${(!inputValue.trim() && !attachedFile) || isLoading ? "bg-[#262730] text-[#41444C]" : "bg-[#FF5F1F] text-white shadow-lg hover:scale-105"}`}><Send size={18} /></button>
              </form>
           </div>
        </div>
      </main>
    </div>
  );
}