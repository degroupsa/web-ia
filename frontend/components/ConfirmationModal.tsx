import React from "react";
import { AlertTriangle, X } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  isDanger?: boolean;
}

export default function ConfirmationModal({ isOpen, onClose, onConfirm, title, message, isDanger = false }: Props) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-[#1C1E24] border border-[#41444C] rounded-2xl w-full max-w-md shadow-2xl relative overflow-hidden">
        {/* Barra superior de color */}
        <div className={`h-1 w-full ${isDanger ? 'bg-red-500' : 'bg-[#FF5F1F]'}`}></div>
        
        <div className="p-6">
          <div className="flex items-start gap-4">
            <div className={`p-3 rounded-full shrink-0 ${isDanger ? 'bg-red-500/10 text-red-500' : 'bg-[#FF5F1F]/10 text-[#FF5F1F]'}`}>
              <AlertTriangle size={24} />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
              <p className="text-sm text-[#9799A5] leading-relaxed">{message}</p>
            </div>
          </div>

          <div className="mt-8 flex justify-end gap-3">
            <button 
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-[#9799A5] hover:text-white hover:bg-[#262730] transition-colors"
            >
              Cancelar
            </button>
            <button 
              onClick={() => { onConfirm(); onClose(); }}
              className={`px-4 py-2 rounded-lg text-sm font-bold text-white shadow-lg transition-all ${
                isDanger 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : 'bg-gradient-to-r from-[#FF5F1F] to-[#FFAA00] hover:opacity-90'
              }`}
            >
              Confirmar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}