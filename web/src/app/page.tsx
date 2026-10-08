"use client";

import { useState } from "react";
import {
  Building2,
  TrendingUp,
  ShieldCheck,
  FileText,
  Users,
  Activity,
  SlidersHorizontal,
  Layers,
  MapPin,
  Clock,
  Download,
  Filter,
  Briefcase,
  Calendar,
} from "lucide-react";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";

interface DealItem {
  id: string;
  title: string;
  address: string;
  neighborhood: string;
  areaM2: number;
  strategy: "Value-Add Renovation" | "Ground-Up Development" | "Distressed Acquisition";
  askingPrice: number;
  pricePerM2: number;
  totalCapex: number;
  capexPerM2: number;
  projectedExit: number;
  exitPricePerM2: number;
  holdingPeriodMonths: number;
  targetIrr: number;
  moic: number;
  hurdleSpreadBps: number;
  verdict: "APPROVED" | "REJECTED" | "COUNTER_OFFER";
  counterOfferPrice?: number;
  mandateMatch: string;
  riskRating: "Low" | "Moderate" | "Elevated";
  underwritingNotes: string;
  monthlyFlows: { month: number; label: string; amount: number }[];
  sensitivityMatrix: {
    capexDelta: string;
    exitMinus10: number;
    exitBase: number;
    exitPlus10: number;
  }[];
  agentsLog: {
    agent: string;
    role: string;
    note: string;
    stance: "bullish" | "bearish" | "neutral";
    score: number;
  }[];
}

const SAMPLE_DEALS: DealItem[] = [
  {
    id: "OPP-001",
    title: "Edificio Rondeau — Unidad 4B",
    address: "Rondeau 450",
    neighborhood: "Nueva Córdoba",
    areaM2: 78,
    strategy: "Value-Add Renovation",
    askingPrice: 85000,
    pricePerM2: 1090,
    totalCapex: 22000,
    capexPerM2: 282,
    projectedExit: 142000,
    exitPricePerM2: 1820,
    holdingPeriodMonths: 14,
    targetIrr: 0.238,
    moic: 1.33,
    hurdleSpreadBps: 580,
    verdict: "APPROVED",
    mandateMatch: "ArgenCapital Core-Plus Fund I (Hurdle: 18.0%)",
    riskRating: "Low",
    underwritingNotes: "Consolidated student micro-market. Below-market basis with clean title deed. Turnaround program focused on premium interior renovation.",
    monthlyFlows: [
      { month: 0, label: "T0: Adquisición y Gastos Escritura", amount: -88825 },
      { month: 2, label: "M2: Capex Reforma — Fase 1", amount: -11000 },
      { month: 4, label: "M4: Capex Reforma — Fase 2", amount: -11000 },
      { month: 14, label: "M14: Salida / Disposición Activo", amount: 142000 },
    ],
    sensitivityMatrix: [
      { capexDelta: "-10% Capex ($19.8k)", exitMinus10: 0.198, exitBase: 0.252, exitPlus10: 0.301 },
      { capexDelta: "Base Capex ($22.0k)", exitMinus10: 0.181, exitBase: 0.238, exitPlus10: 0.285 },
      { capexDelta: "+15% Capex ($25.3k)", exitMinus10: 0.162, exitBase: 0.219, exitPlus10: 0.264 },
    ],
    agentsLog: [
      {
        agent: "Underwriting Agent",
        role: "Evaluación Financiera",
        note: "DCF confirma TIR no apalancada de 23.8% y múltiplo MOIC de 1.33x a 14 meses. Supera holgadamente el hurdle del 18.0%.",
        stance: "bullish",
        score: 9.4,
      },
      {
        agent: "Risk Agent",
        role: "Análisis de Sensibilidad",
        note: "Estrés superado: Incluso ante un desvío de 4 meses en plazos y +15% de capex, la TIR retiene un piso de 21.9%.",
        stance: "bullish",
        score: 8.8,
      },
      {
        agent: "Investment Committee",
        role: "Resolución Final",
        note: "Aprobación unánime del comité. Se autoriza la asignación de capital del fondo y la apertura de negociaciones formales.",
        stance: "bullish",
        score: 9.6,
      },
    ],
  },
  {
    id: "OPP-002",
    title: "Lote Residencial Cañitas",
    address: "Av. O'Higgins 3800",
    neighborhood: "Zona Sur",
    areaM2: 420,
    strategy: "Ground-Up Development",
    askingPrice: 195000,
    pricePerM2: 464,
    totalCapex: 340000,
    capexPerM2: 810,
    projectedExit: 680000,
    exitPricePerM2: 1619,
    holdingPeriodMonths: 24,
    targetIrr: 0.174,
    moic: 1.27,
    hurdleSpreadBps: -260,
    verdict: "COUNTER_OFFER",
    counterOfferPrice: 168000,
    mandateMatch: "Opportunistic Housing Mandate (Hurdle: 20.0%)",
    riskRating: "Moderate",
    underwritingNotes: "Sensibilidad elevada a costos de obra y plazos de habilitación. Al precio pretendido no alcanza la tasa de retorno mínima.",
    monthlyFlows: [
      { month: 0, label: "T0: Adquisición de Terreno", amount: -203775 },
      { month: 6, label: "M6: Estructura y Obra Gruesa", amount: -170000 },
      { month: 14, label: "M14: Terminaciones y Conexiones", amount: -170000 },
      { month: 24, label: "M24: Pre-ventas y Escrituración", amount: 680000 },
    ],
    sensitivityMatrix: [
      { capexDelta: "-10% Capex ($306k)", exitMinus10: 0.145, exitBase: 0.192, exitPlus10: 0.236 },
      { capexDelta: "Base Capex ($340k)", exitMinus10: 0.128, exitBase: 0.174, exitPlus10: 0.218 },
      { capexDelta: "+15% Capex ($391k)", exitMinus10: 0.098, exitBase: 0.142, exitPlus10: 0.186 },
    ],
    agentsLog: [
      {
        agent: "Underwriting Agent",
        role: "Evaluación Financiera",
        note: "La TIR proyectada de 17.4% queda 260 bps por debajo del mandato (20.0%). El lote presenta un sobreprecio de aprox $27k.",
        stance: "bearish",
        score: 6.2,
      },
      {
        agent: "Risk Agent",
        role: "Análisis de Sensibilidad",
        note: "Alta exposición al índice CAC de construcción en un horizonte de 24 meses.",
        stance: "bearish",
        score: 5.5,
      },
      {
        agent: "Investment Committee",
        role: "Resolución Final",
        note: "Contraoferta condicionada: Bajar postura de compra a $168,000 para recomponer el spread a 20.4% de TIR.",
        stance: "neutral",
        score: 7.0,
      },
    ],
  },
  {
    id: "OPP-003",
    title: "Local Comercial San Martín",
    address: "San Martín 180",
    neighborhood: "Centro Histórico",
    areaM2: 145,
    strategy: "Distressed Acquisition",
    askingPrice: 130000,
    pricePerM2: 896,
    totalCapex: 45000,
    capexPerM2: 310,
    projectedExit: 175000,
    exitPricePerM2: 1206,
    holdingPeriodMonths: 18,
    targetIrr: 0.112,
    moic: 1.10,
    hurdleSpreadBps: -680,
    verdict: "REJECTED",
    mandateMatch: "Opportunistic Growth Mandate (Hurdle: 18.0%)",
    riskRating: "Elevated",
    underwritingNotes: "Tendencia de vacancia en locales de centro histórico. Riesgo de liquidez y reconversión no compensado.",
    monthlyFlows: [
      { month: 0, label: "T0: Adquisición Oportunidad", amount: -135850 },
      { month: 4, label: "M4: Puesta en Valor Fachada", amount: -45000 },
      { month: 18, label: "M18: Desinversión", amount: 175000 },
    ],
    sensitivityMatrix: [
      { capexDelta: "-10% Capex ($40.5k)", exitMinus10: 0.082, exitBase: 0.124, exitPlus10: 0.165 },
      { capexDelta: "Base Capex ($45.0k)", exitMinus10: 0.065, exitBase: 0.112, exitPlus10: 0.151 },
      { capexDelta: "+15% Capex ($51.7k)", exitMinus10: 0.041, exitBase: 0.091, exitPlus10: 0.132 },
    ],
    agentsLog: [
      {
        agent: "Underwriting Agent",
        role: "Evaluación Financiera",
        note: "Retorno insuficiente: 11.2% de TIR frente a un mínimo exigido del 18.0%.",
        stance: "bearish",
        score: 3.4,
      },
      {
        agent: "Risk Agent",
        role: "Análisis de Sensibilidad",
        note: "Iliquidez severa en el microcentro para locales comerciales de metraje medio.",
        stance: "bearish",
        score: 2.8,
      },
      {
        agent: "Investment Committee",
        role: "Resolución Final",
        note: "Rechazado. La ecuación riesgo/retorno no es admisible bajo ningún mandato activo.",
        stance: "bearish",
        score: 2.5,
      },
    ],
  },
];

export default function InvestmentTerminalPage() {
  const [selectedDealId, setSelectedDealId] = useState<string>("OPP-001");
  const [inspectorTab, setInspectorTab] = useState<"dcf" | "agents" | "memo">("dcf");

  const selectedDeal = SAMPLE_DEALS.find((d) => d.id === selectedDealId) || SAMPLE_DEALS[0];

  return (
    <div className="flex flex-col min-h-screen bg-[var(--background)] text-slate-200">
      {/* Top Header — Sober Institutional Bar */}
      <header className="border-b border-[var(--border)] bg-[var(--card)] px-6 py-3.5 flex items-center justify-between select-none">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <Briefcase className="w-4 h-4 text-slate-300" />
            <span className="font-semibold text-sm tracking-tight text-slate-100">
              Real Estate Capital OS
            </span>
          </div>
          <span className="text-slate-700">|</span>
          <span className="text-xs text-slate-400 font-medium">Terminal Interna de Inversiones</span>
          <span className="text-slate-700">|</span>
          <span className="text-xs text-slate-400">Plaza Córdoba</span>
        </div>

        <div className="flex items-center gap-5 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span className="text-slate-300 font-medium">Comité Activo</span>
          </div>
          <span className="text-slate-700">|</span>
          <div className="flex items-center gap-1.5 text-slate-400">
            <Calendar className="w-3.5 h-3.5" />
            <span>Octubre 2026</span>
          </div>
        </div>
      </header>

      {/* KPI Portfolio Summary */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-px bg-[var(--border)] border-b border-[var(--border)]">
        <div className="bg-[var(--card)] px-6 py-4">
          <div className="text-xs text-slate-400 font-medium flex items-center justify-between">
            <span>Capital Comprometido</span>
            <span className="text-[11px] text-slate-400">3 Mandatos</span>
          </div>
          <div className="mt-1.5 text-2xl font-semibold text-slate-100 font-tabular tracking-tight">
            {formatCurrency(1250000)}
          </div>
          <div className="text-xs text-slate-500 mt-1">Fondos disponibles para despliegue</div>
        </div>

        <div className="bg-[var(--card)] px-6 py-4">
          <div className="text-xs text-slate-400 font-medium flex items-center justify-between">
            <span>Pipeline Evaluado</span>
            <span className="text-[11px] text-slate-400">3 Inmuebles</span>
          </div>
          <div className="mt-1.5 text-2xl font-semibold text-slate-100 font-tabular tracking-tight">
            {formatCurrency(410000)}
          </div>
          <div className="text-xs text-slate-500 mt-1">Inversión requerida: $817,000</div>
        </div>

        <div className="bg-[var(--card)] px-6 py-4">
          <div className="text-xs text-slate-400 font-medium flex items-center justify-between">
            <span>TIR Promedio Ponderada</span>
            <span className="text-[11px] text-emerald-400 font-medium">+260 bps vs hurdle</span>
          </div>
          <div className="mt-1.5 text-2xl font-semibold text-emerald-400 font-tabular tracking-tight">
            20.6%
          </div>
          <div className="text-xs text-slate-500 mt-1">Múltiplo de capital: 1.28x MOIC</div>
        </div>

        <div className="bg-[var(--card)] px-6 py-4">
          <div className="text-xs text-slate-400 font-medium flex items-center justify-between">
            <span>Tasa de Aprobación</span>
            <span className="text-[11px] text-slate-400">Rigor del Comité</span>
          </div>
          <div className="mt-1.5 text-2xl font-semibold text-slate-100 font-tabular tracking-tight">
            33.3%
          </div>
          <div className="text-xs text-slate-400 mt-1 flex gap-2">
            <span className="text-emerald-400 font-medium">1 Aprobado</span> •
            <span className="text-amber-400 font-medium">1 Contraoferta</span> •
            <span className="text-slate-400">1 Rechazado</span>
          </div>
        </div>
      </section>

      {/* Main Grid Viewport */}
      <main className="flex-1 grid grid-cols-1 xl:grid-cols-12 min-h-0">
        {/* Left Column (7 cols): Opportunity List */}
        <div className="xl:col-span-7 border-r border-[var(--border)] flex flex-col bg-[var(--background)]">
          {/* Subheader */}
          <div className="px-6 py-3 border-b border-[var(--border)] flex items-center justify-between bg-[var(--card)]">
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-slate-400" />
              <span className="text-xs font-semibold text-slate-200">
                Oportunidades en Cartera
              </span>
            </div>
            <span className="text-xs text-slate-400">Ordenado por TIR descendente</span>
          </div>

          {/* Table Header */}
          <div className="grid grid-cols-12 px-6 py-2.5 border-b border-[var(--border)] bg-slate-900/40 text-xs font-medium text-slate-400">
            <div className="col-span-5">Activo y Ubicación</div>
            <div className="col-span-2 text-right">Precio Entrada</div>
            <div className="col-span-2 text-right">Capex Obra</div>
            <div className="col-span-1 text-right">TIR</div>
            <div className="col-span-2 text-right">Dictamen</div>
          </div>

          {/* Deal Rows */}
          <div className="divide-y divide-[var(--border)] flex-1 overflow-y-auto">
            {SAMPLE_DEALS.map((deal) => {
              const isSelected = deal.id === selectedDealId;
              return (
                <div
                  key={deal.id}
                  onClick={() => setSelectedDealId(deal.id)}
                  className={cn(
                    "px-6 py-4 cursor-pointer transition-colors duration-150 border-l-2",
                    isSelected
                      ? "bg-slate-900/80 border-l-slate-200"
                      : "hover:bg-slate-900/40 border-l-transparent"
                  )}
                >
                  <div className="grid grid-cols-12 items-center">
                    <div className="col-span-5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-medium text-slate-400">{deal.id}</span>
                        <h3 className="font-medium text-sm text-slate-100">{deal.title}</h3>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-500" />
                          {deal.neighborhood}
                        </span>
                        <span>•</span>
                        <span>{deal.areaM2} m²</span>
                        <span>•</span>
                        <span className="text-slate-400">{deal.strategy}</span>
                      </div>
                    </div>

                    <div className="col-span-2 text-right">
                      <div className="text-xs font-medium text-slate-200 font-tabular">
                        {formatCurrency(deal.askingPrice)}
                      </div>
                      <div className="text-[11px] text-slate-500 font-tabular">
                        ${deal.pricePerM2}/m²
                      </div>
                    </div>

                    <div className="col-span-2 text-right">
                      <div className="text-xs font-medium text-slate-200 font-tabular">
                        {formatCurrency(deal.totalCapex)}
                      </div>
                      <div className="text-[11px] text-slate-500 font-tabular">
                        ${deal.capexPerM2}/m²
                      </div>
                    </div>

                    <div className="col-span-1 text-right">
                      <div
                        className={cn(
                          "text-xs font-semibold font-tabular",
                          deal.targetIrr >= 0.2 ? "text-emerald-400" : deal.targetIrr >= 0.15 ? "text-amber-400" : "text-rose-400"
                        )}
                      >
                        {formatPercent(deal.targetIrr)}
                      </div>
                      <div className="text-[10px] text-slate-500 font-tabular">
                        {deal.moic.toFixed(2)}x
                      </div>
                    </div>

                    <div className="col-span-2 flex justify-end">
                      <span
                        className={cn(
                          "px-2.5 py-1 rounded text-[11px] font-medium tracking-wide border",
                          deal.verdict === "APPROVED" && "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                          deal.verdict === "COUNTER_OFFER" && "bg-amber-500/10 text-amber-400 border-amber-500/20",
                          deal.verdict === "REJECTED" && "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        )}
                      >
                        {deal.verdict === "APPROVED" && "Aprobado"}
                        {deal.verdict === "COUNTER_OFFER" && "Contraoferta"}
                        {deal.verdict === "REJECTED" && "Rechazado"}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column (5 cols): Institutional Inspector */}
        <div className="xl:col-span-5 flex flex-col bg-[var(--card)]">
          {/* Tabs */}
          <div className="border-b border-[var(--border)] flex items-center justify-between px-6 bg-slate-900/30 select-none">
            <div className="flex gap-6 text-xs">
              <button
                onClick={() => setInspectorTab("dcf")}
                className={cn(
                  "py-3 font-medium border-b-2 transition-colors",
                  inspectorTab === "dcf"
                    ? "border-slate-200 text-slate-100"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                )}
              >
                Modelo Financiero
              </button>
              <button
                onClick={() => setInspectorTab("agents")}
                className={cn(
                  "py-3 font-medium border-b-2 transition-colors",
                  inspectorTab === "agents"
                    ? "border-slate-200 text-slate-100"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                )}
              >
                Dictamen del Comité
              </button>
              <button
                onClick={() => setInspectorTab("memo")}
                className={cn(
                  "py-3 font-medium border-b-2 transition-colors",
                  inspectorTab === "memo"
                    ? "border-slate-200 text-slate-100"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                )}
              >
                Investment Memo
              </button>
            </div>
            <span className="text-xs font-mono text-slate-400 font-medium">{selectedDeal.id}</span>
          </div>

          {/* Inspector Content */}
          <div className="p-6 flex-1 flex flex-col gap-6 overflow-y-auto">
            {/* Asset Identity Card */}
            <div>
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Estrategia: <strong className="text-slate-200">{selectedDeal.strategy}</strong></span>
                <span>Riesgo: <strong className="text-slate-200">{selectedDeal.riskRating}</strong></span>
              </div>
              <h2 className="text-lg font-semibold text-slate-100 mt-1.5">{selectedDeal.title}</h2>
              <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                {selectedDeal.address}, {selectedDeal.neighborhood} ({selectedDeal.areaM2} m²)
              </p>
              <p className="text-xs text-slate-300 mt-3 bg-slate-900/60 p-3 rounded border border-slate-800 leading-relaxed">
                {selectedDeal.underwritingNotes}
              </p>
            </div>

            {/* TAB 1: FINANCIAL MODEL */}
            {inspectorTab === "dcf" && (
              <div className="space-y-5">
                <div className="p-4 rounded border border-[var(--border)] bg-slate-900/40">
                  <div className="text-xs font-medium text-slate-400 pb-2 mb-3 border-b border-slate-800 flex justify-between">
                    <span>Estructura de Capital y Retorno</span>
                    <span className="text-slate-200 font-semibold font-tabular">Horizonte: {selectedDeal.holdingPeriodMonths} meses</span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-500 block text-[11px]">Precio de Compra</span>
                      <span className="text-slate-100 font-medium font-tabular text-sm">
                        {formatCurrency(selectedDeal.askingPrice)}
                      </span>
                      <span className="text-slate-500 text-[11px] block font-tabular">${selectedDeal.pricePerM2}/m²</span>
                    </div>

                    <div>
                      <span className="text-slate-500 block text-[11px]">Capex de Puesta en Valor</span>
                      <span className="text-slate-100 font-medium font-tabular text-sm">
                        {formatCurrency(selectedDeal.totalCapex)}
                      </span>
                      <span className="text-slate-500 text-[11px] block font-tabular">${selectedDeal.capexPerM2}/m²</span>
                    </div>

                    <div>
                      <span className="text-slate-500 block text-[11px]">Inversión Total Desplegada</span>
                      <span className="text-slate-100 font-medium font-tabular text-sm">
                        {formatCurrency(selectedDeal.askingPrice + selectedDeal.totalCapex)}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-500 block text-[11px]">Precio Proyectado de Salida</span>
                      <span className="text-slate-100 font-medium font-tabular text-sm">
                        {formatCurrency(selectedDeal.projectedExit)}
                      </span>
                      <span className="text-slate-500 text-[11px] block font-tabular">${selectedDeal.exitPricePerM2}/m²</span>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800 grid grid-cols-2 gap-4 bg-slate-900/60 p-3 rounded">
                    <div>
                      <span className="text-[11px] text-slate-400 block">TIR Neta Anualizada</span>
                      <span className="text-lg font-semibold text-emerald-400 font-tabular">
                        {formatPercent(selectedDeal.targetIrr)}
                      </span>
                    </div>
                    <div>
                      <span className="text-[11px] text-slate-400 block">Múltiplo sobre Capital (MOIC)</span>
                      <span className="text-lg font-semibold text-slate-100 font-tabular">
                        {selectedDeal.moic.toFixed(2)}x
                      </span>
                    </div>
                  </div>
                </div>

                {/* Cash Flow Timeline */}
                <div className="p-4 rounded border border-[var(--border)] bg-slate-900/30 text-xs">
                  <div className="text-xs font-medium text-slate-400 mb-2">Hitos de Flujo de Fondos</div>
                  <div className="space-y-1.5">
                    {selectedDeal.monthlyFlows.map((flow, i) => (
                      <div key={i} className="flex justify-between py-1 border-b border-slate-800 last:border-0">
                        <span className="text-slate-400">{flow.label}</span>
                        <span className={cn("font-medium font-tabular", flow.amount < 0 ? "text-slate-300" : "text-emerald-400")}>
                          {formatCurrency(flow.amount)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Sensitivity Table */}
                <div className="p-4 rounded border border-[var(--border)] bg-slate-900/30 text-xs">
                  <div className="text-xs font-medium text-slate-400 mb-2">Matriz de Sensibilidad: Capex vs. Precio de Salida</div>
                  <table className="w-full text-right font-tabular text-xs">
                    <thead>
                      <tr className="text-slate-500 border-b border-slate-800">
                        <th className="text-left py-1 font-medium">Escenario Obra</th>
                        <th className="py-1 font-medium">-10% Salida</th>
                        <th className="py-1 font-medium">Salida Base</th>
                        <th className="py-1 font-medium">+10% Salida</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-300">
                      {selectedDeal.sensitivityMatrix.map((row, idx) => (
                        <tr key={idx}>
                          <td className="text-left py-1.5 text-slate-400">{row.capexDelta}</td>
                          <td className="py-1.5">{formatPercent(row.exitMinus10)}</td>
                          <td className="py-1.5 font-semibold text-emerald-400">{formatPercent(row.exitBase)}</td>
                          <td className="py-1.5 text-emerald-300">{formatPercent(row.exitPlus10)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 2: AGENTS RESOLUTION */}
            {inspectorTab === "agents" && (
              <div className="space-y-3 text-xs">
                {selectedDeal.agentsLog.map((log, idx) => (
                  <div key={idx} className="p-3.5 rounded border border-[var(--border)] bg-slate-900/40">
                    <div className="flex items-center justify-between mb-1.5">
                      <div>
                        <span className="font-semibold text-slate-100">{log.agent}</span>
                        <span className="text-slate-500 text-[11px] ml-2">({log.role})</span>
                      </div>
                      <span className="text-[11px] font-medium text-slate-300">Calificación: {log.score}/10</span>
                    </div>
                    <p className="text-slate-300 leading-relaxed">{log.note}</p>
                  </div>
                ))}

                {selectedDeal.counterOfferPrice && (
                  <div className="p-3.5 rounded border border-amber-500/20 bg-amber-500/5 text-xs text-amber-200">
                    <div className="font-semibold">Recomendación de Contraoferta:</div>
                    <p className="mt-1 text-slate-300 leading-relaxed">
                      El comité sugiere ofrecer como máximo{" "}
                      <strong className="text-slate-100 font-tabular font-semibold">
                        {formatCurrency(selectedDeal.counterOfferPrice)}
                      </strong>{" "}
                      para reencuadrar la rentabilidad en el objetivo de 20.0% de TIR.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: INVESTMENT MEMO */}
            {inspectorTab === "memo" && (
              <div className="p-5 rounded border border-[var(--border)] bg-slate-900/50 text-xs space-y-4">
                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                  <h3 className="font-semibold text-slate-100">Memorándum de Inversión — Resumen Ejecutivo</h3>
                  <button className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded transition-colors">
                    <Download className="w-3.5 h-3.5" />
                    Exportar PDF
                  </button>
                </div>

                <div className="space-y-3 text-slate-300 leading-relaxed">
                  <div>
                    <h4 className="font-medium text-slate-100 text-xs">1. Tesis de Adquisición</h4>
                    <p className="mt-1">
                      Adquisición de unidad residencial de {selectedDeal.areaM2} m² en {selectedDeal.address} por un monto de{" "}
                      {formatCurrency(selectedDeal.askingPrice)} (${selectedDeal.pricePerM2}/m²). Se proyecta un capex de{" "}
                      {formatCurrency(selectedDeal.totalCapex)} para reposicionamiento comercial en el mercado de renta de Nueva Córdoba.
                    </p>
                  </div>

                  <div>
                    <h4 className="font-medium text-slate-100 text-xs">2. Métricas Clave</h4>
                    <p className="mt-1">
                      TIR Neta esperada de{" "}
                      <strong className="text-emerald-400 font-tabular">{formatPercent(selectedDeal.targetIrr)}</strong> con un MOIC de{" "}
                      <strong className="text-slate-100 font-tabular">{selectedDeal.moic.toFixed(2)}x</strong> en {selectedDeal.holdingPeriodMonths} meses de horizonte de inversión.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Bottom Actions */}
            <div className="pt-2 border-t border-[var(--border)] flex gap-3">
              <button
                onClick={() => setInspectorTab("memo")}
                className="flex-1 py-2.5 px-4 bg-slate-100 hover:bg-white text-slate-950 font-medium text-xs rounded transition-colors"
              >
                Ver Memorándum Completo
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
