"""
Pytest configuration and shared fixtures.

Este módulo contém fixtures reutilizáveis para todos os testes.
"""

from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.common import (
    BiologicalSex,
    BloodType,
    MedicationFrequency,
    MedicationRoute,
    SummarizerStrategy,
)
from app.models.consultation import ConsultationCreate
from app.models.medication import Allergy, Medication
from app.models.patient import Patient, VitalSigns


@pytest.fixture
def client() -> TestClient:
    """Cliente de teste para a API FastAPI."""
    return TestClient(app)


@pytest.fixture
def valid_patient() -> Patient:
    """Paciente válido para testes."""
    return Patient(
        full_name="Maria Silva Santos",
        cpf="123.456.789-00",
        birth_date=date(1985, 3, 15),
        biological_sex=BiologicalSex.FEMALE,
        blood_type=BloodType.O_POSITIVE,
        is_pregnant=False,
    )


@pytest.fixture
def valid_patient_male() -> Patient:
    """Paciente masculino válido para testes."""
    return Patient(
        full_name="João Carlos Pereira",
        cpf="987.654.321-00",
        birth_date=date(1970, 8, 22),
        biological_sex=BiologicalSex.MALE,
    )


@pytest.fixture
def pregnant_patient() -> Patient:
    """Paciente gestante para testes."""
    return Patient(
        full_name="Ana Beatriz Costa",
        cpf="111.222.333-44",
        birth_date=date(1992, 5, 10),
        biological_sex=BiologicalSex.FEMALE,
        is_pregnant=True,
        gestational_weeks=28,
    )


@pytest.fixture
def valid_vital_signs() -> VitalSigns:
    """Sinais vitais normais para testes."""
    return VitalSigns(
        systolic_bp=120,
        diastolic_bp=80,
        heart_rate=72,
        respiratory_rate=16,
        temperature_celsius=36.5,
        oxygen_saturation=98,
        pain_scale=0,
        weight_kg=70.0,
        height_cm=170.0,
    )


@pytest.fixture
def abnormal_vital_signs() -> VitalSigns:
    """Sinais vitais anormais para testes de warnings."""
    return VitalSigns(
        systolic_bp=180,  # Alta
        diastolic_bp=110,  # Alta
        heart_rate=110,  # Taquicardia
        respiratory_rate=24,  # Alta
        temperature_celsius=38.5,  # Febre
        oxygen_saturation=92,  # Baixa
        pain_scale=8,
    )


@pytest.fixture
def critical_vital_signs() -> VitalSigns:
    """Sinais vitais críticos para testes."""
    return VitalSigns(
        systolic_bp=60,  # Crítico baixo
        diastolic_bp=30,  # Crítico baixo
        heart_rate=35,  # Crítico baixo
        oxygen_saturation=85,  # Crítico baixo
    )


@pytest.fixture
def valid_medication() -> Medication:
    """Medicamento válido para testes."""
    return Medication(
        active_ingredient="losartana potássica",
        commercial_name="Cozaar",
        dosage="50mg",
        frequency=MedicationFrequency.ONCE_DAILY,
        route=MedicationRoute.ORAL,
        start_date=date(2023, 1, 15),
        prescriber="Dr. Carlos Mendes",
    )


@pytest.fixture
def valid_allergy() -> Allergy:
    """Alergia válida para testes."""
    return Allergy(
        allergen="dipirona",
        reaction_type="allergic",
        severity="moderate",
        reaction_description="Urticária generalizada",
        confirmed=True,
    )


@pytest.fixture
def severe_allergy() -> Allergy:
    """Alergia grave para testes."""
    return Allergy(
        allergen="penicilina",
        reaction_type="allergic",
        severity="life_threatening",
        reaction_description="Anafilaxia",
        confirmed=True,
    )


@pytest.fixture
def minimal_consultation(valid_patient: Patient) -> ConsultationCreate:
    """Consulta com dados mínimos obrigatórios."""
    return ConsultationCreate(
        patient=valid_patient,
        consultation_date=date(2024, 1, 15),
        chief_complaint="Dor de cabeça persistente há 3 dias",
        professional_name="Dr. João Pedro Oliveira",
    )


@pytest.fixture
def complete_consultation(
    valid_patient: Patient,
    valid_vital_signs: VitalSigns,
    valid_medication: Medication,
    valid_allergy: Allergy,
) -> ConsultationCreate:
    """Consulta completa com todos os campos."""
    return ConsultationCreate(
        patient=valid_patient,
        consultation_date=date(2024, 1, 15),
        consultation_type="follow_up",
        facility_name="Clínica Saúde Total",
        chief_complaint="Dor de cabeça persistente há 3 dias",
        history_present_illness=(
            "Paciente refere cefaleia holocraniana de intensidade "
            "moderada (6/10) iniciada há 3 dias. Piora no final do dia."
        ),
        vital_signs=valid_vital_signs,
        current_medications=[valid_medication],
        allergies=[valid_allergy],
        past_medical_history=[
            "Hipertensão arterial sistêmica (2018)",
            "Enxaqueca sem aura (2015)",
        ],
        family_history=["Mãe: HAS e DM2", "Pai: IAM aos 62 anos"],
        social_history="Não tabagista. Etilismo social.",
        physical_examination=(
            "BEG, corada, hidratada. ACV: RCR 2T BNF. AR: MV+ bilateral."
        ),
        professional_name="Dr. João Pedro Oliveira",
        professional_council_id="CRM-SP 123456",
        specialty="Clínica Médica",
        treatment_plan="1. Paracetamol 750mg 6/6h se dor\n2. Retorno em 7 dias",
        additional_notes="Paciente orientada.",
        strategy=SummarizerStrategy.RULE_BASED,
    )


@pytest.fixture
def consultation_with_abnormal_vitals(
    valid_patient: Patient,
    abnormal_vital_signs: VitalSigns,
) -> ConsultationCreate:
    """Consulta com sinais vitais anormais."""
    return ConsultationCreate(
        patient=valid_patient,
        consultation_date=date(2024, 1, 15),
        chief_complaint="Mal estar geral",
        vital_signs=abnormal_vital_signs,
        professional_name="Dr. João Pedro Oliveira",
    )


@pytest.fixture
def minimal_consultation_dict() -> dict[str, Any]:
    """Dicionário com dados mínimos para request."""
    return {
        "patient": {
            "full_name": "Maria Silva Santos",
            "cpf": "123.456.789-00",
            "birth_date": "1985-03-15",
            "biological_sex": "female",
        },
        "consultation_date": "2024-01-15",
        "chief_complaint": "Dor de cabeça persistente há 3 dias",
        "professional_name": "Dr. João Pedro Oliveira",
    }


@pytest.fixture
def complete_consultation_dict() -> dict[str, Any]:
    """Dicionário completo para request."""
    return {
        "patient": {
            "full_name": "Maria Silva Santos",
            "cpf": "123.456.789-00",
            "birth_date": "1985-03-15",
            "biological_sex": "female",
            "blood_type": "O+",
            "is_pregnant": False,
        },
        "consultation_date": "2024-01-15",
        "consultation_type": "follow_up",
        "facility_name": "Clínica Saúde Total",
        "chief_complaint": "Dor de cabeça persistente há 3 dias",
        "history_present_illness": "Paciente refere cefaleia há 3 dias.",
        "vital_signs": {
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "heart_rate": 72,
            "respiratory_rate": 16,
            "temperature_celsius": 36.5,
            "oxygen_saturation": 98,
            "pain_scale": 3,
        },
        "current_medications": [
            {
                "active_ingredient": "losartana potássica",
                "dosage": "50mg",
                "frequency": "1x/day",
                "route": "oral",
            }
        ],
        "allergies": [
            {
                "allergen": "dipirona",
                "reaction_type": "allergic",
                "severity": "moderate",
                "confirmed": True,
            }
        ],
        "past_medical_history": ["Hipertensão arterial (2018)"],
        "family_history": ["Mãe: HAS"],
        "social_history": "Não tabagista.",
        "physical_examination": "BEG, corada, hidratada.",
        "professional_name": "Dr. João Pedro Oliveira",
        "professional_council_id": "CRM-SP 123456",
        "specialty": "Clínica Médica",
        "treatment_plan": "Paracetamol 750mg se dor",
        "strategy": "rule_based",
    }
