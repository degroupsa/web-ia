import React, { useState } from "react";
import { X, Zap, Check, Star, Image as ImageIcon, Gem } from "lucide-react";

// ==========================================
// COMPONENTE PRINCIPAL
// ==========================================

export default function PricingModal({ 
  isOpen, 
  onClose, 
  userEmail 
}: { 
  isOpen: boolean; 
  onClose: () => void;
  userEmail?: string; 
}) {
  const [isProcessing, setIsProcessing] = useState<string | null>(null);

  if (!isOpen) return null;

  // --- Lógica para pedir el Link de Pago al Backend ---
  const generarPago = async (proveedor: 'stripe' | 'mercadopago', plan: string) => {
    if (!userEmail) {
      alert("⚠️ Error de sesión: No se detectó tu correo. Por favor, recarga la página.");
      return;
    }

    setIsProcessing(`${plan}-${proveedor}`);

    try {
      const res = await fetch(`http://localhost:8000/api/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: userEmail, plan: plan, provider: proveedor })
      });
      
      const data = await res.json();
      
      if (data.url) {
        window.location.href = data.url;
      } else {
        alert("⚠️ Error: El servidor no devolvió un link de pago válido.");
        setIsProcessing(null);
      }
    } catch (e) {
      alert("⚠️ Error de conexión con el servidor de pagos. Verifica el backend.");
      setIsProcessing(null);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0E1117]/95 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-[#1C1E24] border border-[#41444C] rounded-2xl w-full max-w-6xl relative flex flex-col max-h-[95vh] shadow-[0_0_60px_rgba(255,95,31,0.15)] overflow-hidden">
        
        {/* HEADER */}
        <div className="p-6 border-b border-[#41444C] flex justify-between items-center bg-[#262730] shrink-0">
          <div>
            <h2 className="text-2xl font-black text-white flex items-center gap-3 uppercase tracking-tighter">
              <Zap className="text-[#FF5F1F]" fill="currentColor" size={28} /> 
              Planes de Suscripción
            </h2>
            <p className="text-[#9799A5] text-xs font-bold uppercase tracking-widest mt-1 pl-1">
              Potencia tu flujo de trabajo con Inteligencia Neuronal
            </p>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 bg-[#1C1E24] rounded-lg border border-[#41444C] text-[#9799A5] hover:text-white hover:border-[#FF5F1F] transition-all cursor-pointer"
          >
            <X size={24} />
          </button>
        </div>

        {/* CONTENIDO SCROLLABLE */}
        <div className="p-8 overflow-y-auto grid grid-cols-1 lg:grid-cols-3 gap-8 bg-[#0E1117] h-full">
           
           {/* === PLAN STARTER === */}
           <div className="p-6 border border-[#F0F0F0] bg-[#1C1E24] rounded-2xl flex flex-col relative opacity-60 hover:opacity-100 transition-all duration-300 group">
             <h3 className="text-[#9799A5] font-black tracking-widest text-sm uppercase mb-2 flex items-center gap-2"><Zap size={18} color="#FF5F1F" fill="#FF5F1F" /> Starter</h3>
             <div className="text-4xl font-black text-white my-4 flex items-end gap-1">
                $0 <span className="text-sm text-[#9799A5] font-medium mb-1">/mes</span>
             </div>
             <p className="text-[#9799A5] text-xs leading-relaxed mb-6 h-10">
                Funciones necesarias para experimentar el poder de Kortexa AI de forma rápida, sencilla y gratuita.
             </p>
             <ul className="text-[#777] text-[13px] space-y-4 mb-8 flex-1 group-hover:text-[#AAA] transition-colors">
                <li className="flex items-start gap-3"><Check size={16} className="text-[#F0F0F0] mt-0.5 shrink-0"/> <strong>Kortexa V2.0 (Respuesta Rápida)</strong></li>
                <li className="flex items-start gap-3"><Check size={16} className="text-[#F0F0F0] mt-0.5 shrink-0"/> 20 mensajes de texto diarios</li>
                <li className="flex items-start gap-3"><Check size={16} className="text-[#F0F0F0] mt-0.5 shrink-0"/> Almacenamiento en DB de 15 GB</li>
                <li className="flex items-start gap-3 text-white">
                  <ImageIcon size={16} className="text-[#FF5F1F] mt-0.5 shrink-0"/> 
                  <span><strong>Bono de Bienvenida:</strong><br/><span className="text-xs text-[#9799A5]">5 Imágenes HD (Kortexa Studio)</span></span>
                </li>
             </ul>
             <button disabled className="w-full py-3 bg-[#262730] border border-[#41444C] text-[#555] font-bold rounded-lg uppercase text-[11px] tracking-wider cursor-not-allowed">
               Tu Plan Actual
             </button>
           </div>

           {/* === PLAN PRO (DESTACADO) === */}
           <div className="p-6 border-2 border-[#FF5F1F] bg-[#1C1E24] rounded-2xl flex flex-col relative shadow-[0_0_40px_rgba(255,95,31,0.15)] transform hover:-translate-y-1 transition-all duration-300 z-10">
             <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-[#FF5F1F] to-[#FFAA00] text-white text-[10px] font-black px-4 py-1.5 rounded-full uppercase tracking-widest shadow-lg">
                Recomendado
             </div>
              <h3 className="text-[#FF5F1F] font-black tracking-widest text-sm uppercase mb-2 flex items-center gap-2"><Gem size={18} color="#00b7ff" /> Pro</h3>
             <div className="text-5xl font-black text-white my-4 flex items-end gap-1">
                $15 <span className="text-sm text-[#9799A5] font-medium mb-1">USD /mes</span>
             </div>
             <p className="text-white text-xs leading-relaxed mb-6 h-10">
                Potencia profesional. Razonamiento avanzado, lectura de documentos y arte visual en un mismo plan.
             </p>
             <ul className="text-[#FAFAFA] text-[13px] space-y-4 mb-8 flex-1">
                <li className="flex items-start gap-3"><Check size={16} className="text-[#FF5F1F] mt-0.5 shrink-0"/> <strong>Kortexa V3.0 Pro</strong> (Uso intensivo)</li>
                <li className="flex items-start gap-3"><Check size={16} className="text-[#FF5F1F] mt-0.5 shrink-0"/> <strong>Kortexa Studio</strong> (30 imágenes/día)</li>
                <li className="flex items-start gap-3"><Check size={16} className="text-[#FF5F1F] mt-0.5 shrink-0"/> Análisis de Documentos y PDFs</li>
                <li className="flex items-start gap-3"><Check size={16} className="text-[#FF5F1F] mt-0.5 shrink-0"/> Análisis en la Web en tiempo real</li>
                <li className="flex items-start gap-3"><Check size={16} className="text-[#FF5F1F] mt-0.5 shrink-0"/> <strong>Almacenamiento en DB de 100 GB</strong></li>
             </ul>
             
             {/* BOTONES DE PAGO PRO */}
             <div className="flex flex-col gap-2.5">
                 <button 
                    onClick={() => generarPago('mercadopago', 'pro')}
                    disabled={isProcessing !== null}
                    className="w-full py-2.5 bg-white hover:bg-[#F0F0F0] text-[#009EE3] font-extrabold rounded-lg transition-all shadow-md flex items-center justify-center cursor-pointer disabled:opacity-50 border border-transparent hover:border-[#009EE3]"
                 >
                   {isProcessing === 'pro-mercadopago' ? 
                     <div className="w-4 h-4 border-2 border-[#009EE3] border-t-transparent rounded-full animate-spin"></div> : 
                     <span className="flex items-center justify-center gap-3 text-[11px] tracking-widest">
                        <img src="/mercadopago.png" alt="MP" className="h-5 w-6 object-contain" /> 
                        MERCADO PAGO
                     </span>
                   }
                 </button>

                 <button 
                    onClick={() => generarPago('stripe', 'pro')}
                    disabled={isProcessing !== null}
                    className="w-full py-2.5 bg-white hover:bg-[#F0F0F0] text-[#635BFF] font-extrabold rounded-lg transition-all shadow-md flex items-center justify-center cursor-pointer disabled:opacity-50 border border-transparent hover:border-[#635BFF]"
                 >
                   {isProcessing === 'pro-stripe' ? 
                     <div className="w-4 h-4 border-2 border-[#635BFF] border-t-transparent rounded-full animate-spin"></div> : 
                     <span className="flex items-center justify-center gap-1 text-[11px] tracking-widest -translate-x-4">
                        <img src="/stripe.png" alt="Stripe" className="h-6 w-auto object-contain" /> 
                        STRIPE
                     </span>
                   }
                 </button>
             </div>
           </div>

           {/* === PLAN BUSINESS === */}
           <div className="p-6 border border-[#FFAA00] bg-[#1C1E24] rounded-2xl flex flex-col relative shadow-[0_0_20px_rgba(255,170,0,0.1)] hover:shadow-[0_0_50px_rgba(255,170,0,0.2)] transition-all duration-300">
             <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-[#FFAA00] text-black text-[9px] font-black px-3 py-1 rounded-full uppercase tracking-widest">
                Empresas
             </div>
             <h3 className="text-[#FFAA00] font-black tracking-widest text-sm uppercase mb-2 flex items-center gap-2">
                <Star size={16} fill="currentColor"/> Business
             </h3>
             <div className="text-5xl font-black text-white my-4 flex items-end gap-1">
                $49 <span className="text-sm text-[#9799A5] font-medium mb-1">USD /mes</span>
             </div>
             <p className="text-[#9799A5] text-xs leading-relaxed mb-6 h-10">
                Solución corporativa sin restricciones y con máxima prioridad. Accede a nuestro sistema Kortexa AI mas avanzado con respuestas eficientes.
             </p>
             <ul className="text-[#FAFAFA] text-[13px] space-y-4 mb-8 flex-1">
                <li className="flex items-start gap-3"><Check size={16} className="text-[#FFAA00] mt-0.5 shrink-0"/> <strong>Kortexa V3.0 Ultra</strong> (IA Ultra Avanzada)</li>
                <li className="flex items-start gap-3"><Check size={16} className="text-[#FFAA00] mt-0.5 shrink-0"/> <strong>Kortexa Studio</strong>(Ilimitado)</li>
                <li className="flex items-start gap-3"><Check size={16} className="text-[#FFAA00] mt-0.5 shrink-0"/> <strong>Análisis de datos</strong>(Ilimitado)</li>
                <li className="flex items-start gap-3"><Check size={16} className="text-[#FFAA00] mt-0.5 shrink-0"/> <strong>Soporte Técnico 24/7</strong></li>
                <li className="flex items-start gap-3"><Check size={16} className="text-[#FFAA00] mt-0.5 shrink-0"/> <strong>Almacenamiento en DB de 256 GB</strong></li>
             </ul>
             
             {/* BOTONES BUSINESS */}
             <div className="flex flex-col gap-2.5">
                 <button 
                    onClick={() => generarPago('mercadopago', 'business')}
                    disabled={isProcessing !== null}
                    className="w-full py-2.5 bg-white hover:bg-[#F0F0F0] text-[#009EE3] font-extrabold rounded-lg transition-all shadow-md flex items-center justify-center cursor-pointer disabled:opacity-50 border border-transparent hover:border-[#009EE3]"
                 >
                   {isProcessing === 'business-mercadopago' ? 
                     <div className="w-4 h-4 border-2 border-[#009EE3] border-t-transparent rounded-full animate-spin"></div> : 
                     <span className="flex items-center justify-center gap-3 text-[11px] tracking-widest">
                        <img src="/mercadopago.png" alt="MP" className="h-5 w-6 object-contain" /> 
                        MERCADO PAGO
                     </span>
                   }
                 </button>

                 <button 
                    onClick={() => generarPago('stripe', 'business')}
                    disabled={isProcessing !== null}
                    className="w-full py-2.5 bg-white hover:bg-[#F0F0F0] text-[#635BFF] font-extrabold rounded-lg transition-all shadow-md flex items-center justify-center cursor-pointer disabled:opacity-50 border border-transparent hover:border-[#635BFF]"
                 >
                   {isProcessing === 'business-stripe' ? 
                     <div className="w-4 h-4 border-2 border-[#635BFF] border-t-transparent rounded-full animate-spin"></div> : 
                     <span className="flex items-center justify-center gap-1 text-[11px] tracking-widest -translate-x-4">
                        <img src="/stripe.png" alt="Stripe" className="h-6 w-auto object-contain" /> 
                        STRIPE
                     </span>
                   }
                 </button>
             </div>
           </div>

        </div>
      </div>
    </div>
  );
}