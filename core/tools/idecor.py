"""IDECOR / OMI Córdoba Market Benchmark Tool.

Consumes official real estate observatory benchmarks (Observatorio del Mercado Inmobiliario - IDECOR)
for the city of Córdoba to audit property acquisition and exit pricing per square meter.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from core.schemas import Opportunity


class NeighborhoodBenchmark(BaseModel):
    """Statistical price distribution per square meter for finished residential units in USD."""
    neighborhood: str
    p25_usd_m2: float
    median_usd_m2: float
    p75_usd_m2: float


# Official IDECOR / OMI benchmarks for finished/renovated apartments in Córdoba Capital
IDECOR_OMI_BENCHMARKS: Dict[str, NeighborhoodBenchmark] = {
    "nueva_cordoba": NeighborhoodBenchmark(
        neighborhood="Nueva Córdoba",
        p25_usd_m2=1400.0,
        median_usd_m2=1750.0,
        p75_usd_m2=2100.0,
    ),
    "general_paz": NeighborhoodBenchmark(
        neighborhood="General Paz",
        p25_usd_m2=1200.0,
        median_usd_m2=1450.0,
        p75_usd_m2=1750.0,
    ),
    "guemes": NeighborhoodBenchmark(
        neighborhood="Güemes",
        p25_usd_m2=1150.0,
        median_usd_m2=1380.0,
        p75_usd_m2=1650.0,
    ),
    "cerro_de_las_rosas": NeighborhoodBenchmark(
        neighborhood="Cerro de las Rosas",
        p25_usd_m2=1300.0,
        median_usd_m2=1700.0,
        p75_usd_m2=2200.0,
    ),
    "alberdi": NeighborhoodBenchmark(
        neighborhood="Alberdi / Alto Alberdi",
        p25_usd_m2=850.0,
        median_usd_m2=1050.0,
        p75_usd_m2=1250.0,
    ),
    "centro": NeighborhoodBenchmark(
        neighborhood="Centro",
        p25_usd_m2=900.0,
        median_usd_m2=1100.0,
        p75_usd_m2=1350.0,
    ),
    "cordoba_general": NeighborhoodBenchmark(
        neighborhood="Córdoba Capital (Promedio General)",
        p25_usd_m2=1100.0,
        median_usd_m2=1450.0,
        p75_usd_m2=1850.0,
    ),
}


def _normalize_text(text: str) -> str:
    """Normalize text by removing accents, special characters, and lowering case."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    return re.sub(r"[^a-z0-9]+", " ", normalized.lower()).strip()


def resolve_neighborhood(location: str, title: str = "") -> NeighborhoodBenchmark:
    """Resolve the matching neighborhood benchmark from opportunity location and title text."""
    combined = f"{_normalize_text(location)} {_normalize_text(title)}"

    if "nueva cordoba" in combined:
        return IDECOR_OMI_BENCHMARKS["nueva_cordoba"]
    elif "general paz" in combined:
        return IDECOR_OMI_BENCHMARKS["general_paz"]
    elif "guemes" in combined:
        return IDECOR_OMI_BENCHMARKS["guemes"]
    elif "cerro" in combined or "rosas" in combined:
        return IDECOR_OMI_BENCHMARKS["cerro_de_las_rosas"]
    elif "alberdi" in combined:
        return IDECOR_OMI_BENCHMARKS["alberdi"]
    elif "centro" in combined:
        return IDECOR_OMI_BENCHMARKS["centro"]
    else:
        return IDECOR_OMI_BENCHMARKS["cordoba_general"]


class MarketValuationAudit(BaseModel):
    """Structured audit of an opportunity's valuation against IDECOR benchmarks."""
    neighborhood: str
    usable_area_m2: Optional[float] = None
    benchmark_p25_usd_m2: float
    benchmark_median_usd_m2: float
    benchmark_p75_usd_m2: float
    purchase_price_per_m2: Optional[float] = None
    exit_price_per_m2: Optional[float] = None
    is_exit_realistic: bool = True
    is_below_market_entry: bool = False
    exit_deviation_pct: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)


def audit_property_valuation(opportunity: Opportunity) -> MarketValuationAudit:
    """Audit an opportunity's pricing against IDECOR / OMI market benchmarks."""
    benchmark = resolve_neighborhood(opportunity.location, opportunity.title)
    warnings: List[str] = []
    insights: List[str] = []

    area = opportunity.usable_area_m2
    purchase_m2 = opportunity.purchase_price_per_m2
    exit_m2 = opportunity.exit_price_per_m2

    if not area or area <= 0:
        return MarketValuationAudit(
            neighborhood=benchmark.neighborhood,
            usable_area_m2=None,
            benchmark_p25_usd_m2=benchmark.p25_usd_m2,
            benchmark_median_usd_m2=benchmark.median_usd_m2,
            benchmark_p75_usd_m2=benchmark.p75_usd_m2,
            purchase_price_per_m2=None,
            exit_price_per_m2=None,
            is_exit_realistic=True,
            is_below_market_entry=False,
            warnings=["Propiedad no especifica m2 cubiertos; se omite auditoría métrica IDECOR."],
            insights=[f"Benchmark zonal de referencia ({benchmark.neighborhood}): USD {benchmark.median_usd_m2:,.0f}/m²."],
        )

    is_exit_realistic = True
    is_below_market_entry = False
    exit_dev_pct: Optional[float] = None

    # Audit Entry (Purchase price per m2)
    if purchase_m2 is not None:
        if purchase_m2 < benchmark.p25_usd_m2:
            is_below_market_entry = True
            discount_pct = round(((benchmark.median_usd_m2 - purchase_m2) / benchmark.median_usd_m2) * 100, 1)
            insights.append(
                f"Entrada atractiva: USD {purchase_m2:,.0f}/m² se ubica por debajo del percentil 25 (USD {benchmark.p25_usd_m2:,.0f}/m²), "
                f"un {discount_pct}% por debajo de la mediana zonal."
            )
        elif purchase_m2 > benchmark.p75_usd_m2:
            warnings.append(
                f"Alerta de compra: USD {purchase_m2:,.0f}/m² supera el percentil 75 zonal (USD {benchmark.p75_usd_m2:,.0f}/m²)."
            )

    # Audit Exit Valuation per m2
    if exit_m2 is not None:
        exit_dev_pct = round(((exit_m2 - benchmark.median_usd_m2) / benchmark.median_usd_m2) * 100, 1)
        # More than 5% above P75 is flagged as unrealistic / over-optimistic
        if exit_m2 > benchmark.p75_usd_m2 * 1.05:
            is_exit_realistic = False
            warnings.append(
                f"Alerta de salida: Salida proyectada en USD {exit_m2:,.0f}/m² excede el techo de mercado zonal "
                f"(P75 IDECOR: USD {benchmark.p75_usd_m2:,.0f}/m² por {exit_dev_pct}% sobre la mediana). "
                f"Riesgo de liquidez y sobrevaluación en desinversión."
            )
        else:
            insights.append(
                f"Valuación de salida coherente: USD {exit_m2:,.0f}/m² dentro de los rangos oficiales del OMI para {benchmark.neighborhood}."
            )

    return MarketValuationAudit(
        neighborhood=benchmark.neighborhood,
        usable_area_m2=area,
        benchmark_p25_usd_m2=benchmark.p25_usd_m2,
        benchmark_median_usd_m2=benchmark.median_usd_m2,
        benchmark_p75_usd_m2=benchmark.p75_usd_m2,
        purchase_price_per_m2=purchase_m2,
        exit_price_per_m2=exit_m2,
        is_exit_realistic=is_exit_realistic,
        is_below_market_entry=is_below_market_entry,
        exit_deviation_pct=exit_dev_pct,
        warnings=warnings,
        insights=insights,
    )
