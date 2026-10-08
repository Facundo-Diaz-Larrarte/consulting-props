"""Property Ingestion & Normalization Agent for Real Estate Capital OS.

Implements Sections 16.2 & 16.6 (Property Sourcing & Normalization Agent):
Extracts unstructured broker messages, WhatsApp notes, or listings into
strictly validated `Opportunity` domain objects.
"""

from __future__ import annotations

import os
import re
from typing import Optional
from core.schemas import DealStage, Opportunity, StrategyType


class PropertyIngestionAgent:
    """Agent capable of ingesting raw unstructured property notes and emitting an Opportunity."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def ingest(self, raw_text: str) -> Opportunity:
        """Parse raw text into a validated Opportunity object.

        Uses LLM with Structured Outputs if API key is present;
        otherwise uses deterministic regex & semantic heuristic parser.
        """
        if self.api_key:
            try:
                return self._ingest_with_llm(raw_text)
            except Exception:
                # Graceful fallback to heuristic parser if LLM call fails
                return self._ingest_with_heuristics(raw_text)
        return self._ingest_with_heuristics(raw_text)

    def _ingest_with_llm(self, raw_text: str) -> Opportunity:
        """Call LLM API using structured outputs."""
        # Using standard openai client if installed
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un agente senior de adquisiciones inmobiliarias para Real Estate Capital OS. "
                            "Tu tarea es analizar la ficha o mensaje y extraer todos los datos económicos requeridos "
                            "en una estructura Opportunity. Asegúrate de inferir precios en USD, capex, plazo y salida."
                        ),
                    },
                    {"role": "user", "content": raw_text},
                ],
                response_format=Opportunity,
            )
            return completion.choices[0].message.parsed
        except Exception:
            return self._ingest_with_heuristics(raw_text)

    def _ingest_with_heuristics(self, raw_text: str) -> Opportunity:
        """Deterministic pattern parser for broker texts (especially Córdoba / Argentina formats)."""
        normalized_text = raw_text.replace("\n", " ").strip()

        # 1. Location detection
        cordoba_locations = [
            "Nueva Córdoba", "Nueva Cordoba", "General Paz", "Güemes", "Guemes",
            "Cerro de las Rosas", "Alberdi", "Centro", "Villa Belgrano",
            "Alta Córdoba", "Alta Cordoba", "Cofico", "Barrio Jardín", "Barrio Jardin",
            "Villa Carlos Paz"
        ]
        detected_location = "Cordoba, Argentina"
        for loc in cordoba_locations:
            if re.search(rf"\b{re.escape(loc)}\b", normalized_text, re.IGNORECASE):
                detected_location = f"{loc}, Cordoba"
                break

        # 2. Strategy detection
        strategy = StrategyType.RENOVATE_AND_SELL
        if re.search(r"alquiler|renta|rentabilidad|inquilino", normalized_text, re.IGNORECASE):
            strategy = StrategyType.BUY_AND_HOLD
        elif re.search(r"pozo|preventa|en construcci[oó]n", normalized_text, re.IGNORECASE):
            strategy = StrategyType.PRE_CONSTRUCTION
        elif re.search(r"lote|terreno|desarrollo", normalized_text, re.IGNORECASE):
            strategy = StrategyType.DEVELOPMENT
        elif re.search(r"subdivi|dividir", normalized_text, re.IGNORECASE):
            strategy = StrategyType.SPLIT_AND_SELL

        # 3. Numeric extraction: Look for numbers with USD or $
        # Matches patterns like USD 75.000, US$ 80,000, 75000 USD, 75k, etc.
        def extract_amounts(text: str) -> list[float]:
            # Convert 'k' notation (e.g. 75k -> 75000)
            text_expanded = re.sub(r"(\d+(?:\.\d+)?)\s*k\b", lambda m: str(int(float(m.group(1)) * 1000)), text, flags=re.IGNORECASE)
            
            # Find numbers associated with money
            amounts = []
            matches = re.findall(r"(?:USD|US\$|\$)?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+)", text_expanded, re.IGNORECASE)
            for m in matches:
                clean_num = m.replace(".", "").replace(",", ".")
                try:
                    val = float(clean_num)
                    if 1000 <= val <= 50_000_000:  # Reasonable real estate price filter
                        amounts.append(val)
                except ValueError:
                    continue
            return amounts

        amounts = extract_amounts(normalized_text)

        # Heuristic price assignment
        asking_price = 100000.0
        purchase_price = 90000.0
        capex = 15000.0
        exit_value = 140000.0
        holding_period = 12

        if len(amounts) >= 3:
            # Sort detected amounts: lowest might be capex, highest exit value
            # Example: [75000, 68000, 12000, 115000]
            # capex is usually the smallest amount (< 50k)
            small_amounts = [a for a in amounts if a <= 40000]
            large_amounts = [a for a in amounts if a > 40000]

            if small_amounts:
                capex = small_amounts[0]
            if len(large_amounts) >= 2:
                # large_amounts could be [asking, purchase, exit]
                asking_price = large_amounts[0]
                purchase_price = large_amounts[1] if len(large_amounts) > 2 else asking_price * 0.90
                exit_value = max(large_amounts)
            elif len(large_amounts) == 1:
                asking_price = large_amounts[0]
                purchase_price = asking_price * 0.90
                exit_value = (purchase_price + capex) * 1.25
        elif len(amounts) == 2:
            asking_price = amounts[0]
            purchase_price = asking_price * 0.92
            exit_value = amounts[1] if amounts[1] > asking_price else asking_price * 1.30
        elif len(amounts) == 1:
            asking_price = amounts[0]
            purchase_price = asking_price * 0.90
            exit_value = (purchase_price + capex) * 1.25

        # 4. Holding period extraction (e.g. "en 10 meses", "plazo 12 meses", "8 m")
        month_match = re.search(r"(\d+)\s*(?:meses|mes|m)\b", normalized_text, re.IGNORECASE)
        if month_match:
            try:
                m_val = int(month_match.group(1))
                if 1 <= m_val <= 60:
                    holding_period = m_val
            except ValueError:
                pass

        # 5. Title synthesis
        first_sentence = raw_text.strip().split(".")[0].strip()
        title = first_sentence[:60] if len(first_sentence) > 5 else f"Oportunidad en {detected_location}"

        return Opportunity(
            title=title,
            location=detected_location,
            strategy=strategy,
            asking_price=asking_price,
            projected_purchase_price=purchase_price,
            estimated_capex=capex,
            holding_period_months=holding_period,
            projected_exit_value=exit_value,
            status=DealStage.NORMALIZED,
            notes=raw_text.strip(),
        )
