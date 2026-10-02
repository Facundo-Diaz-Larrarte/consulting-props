"""Tests for Property Ingestion Agent."""

from core.agents.ingestion import PropertyIngestionAgent
from core.schemas import DealStage, StrategyType


def test_ingestion_agent_heuristic_broker_message():
    raw_message = (
        "OPORTUNIDAD EXCLUSIVA EN NUEVA CORDOBA! Depto 2 dormitorios a reciclar en calle Obispo Trejo. "
        "Piden USD 85.000 pero con 75.000 se cierra en mano. "
        "Estimamos 15.000 de capex en cocina y bano para salir en USD 130.000 en 10 meses. "
        "Excelente flip!"
    )

    agent = PropertyIngestionAgent()
    opportunity = agent.ingest(raw_message)

    assert "Nueva Cordoba" in opportunity.location
    assert opportunity.strategy == StrategyType.RENOVATE_AND_SELL
    assert opportunity.status == DealStage.NORMALIZED
    assert opportunity.holding_period_months == 10
    assert opportunity.asking_price > 0
    assert opportunity.projected_purchase_price > 0
    assert opportunity.estimated_capex > 0
    assert opportunity.projected_exit_value > opportunity.projected_purchase_price
    assert opportunity.notes == raw_message.strip()


def test_ingestion_agent_rental_detection():
    raw_message = (
        "Casa en Barrio Jardin, ideal para renta temporal o alquiler tradicional. "
        "Precio de venta: USD 160.000."
    )

    agent = PropertyIngestionAgent()
    opportunity = agent.ingest(raw_message)

    assert "Barrio Jardin" in opportunity.location
    assert opportunity.strategy == StrategyType.BUY_AND_HOLD
    assert opportunity.asking_price == 160000.0
