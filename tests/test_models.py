"""
Testes para os modelos Pydantic.

Verifica validações, constraints e comportamentos dos schemas.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models.common import (
    BiologicalSex,
    BloodType,
    MedicationFrequency,
    MedicationRoute,
    SummarizerStrategy,
    WarningLevel,
)
from app.models.consultation import ConsultationCreate
from app.models.medication import Allergy, Medication
from app.models.patient import Patient, VitalSigns


class TestPatientModel:
    """Testes para o modelo Patient."""

    def test_valid_patient(self, valid_patient: Patient) -> None:
        """Paciente válido deve ser criado sem erros."""
        assert valid_patient.full_name == "Maria Silva Santos"
        assert valid_patient.cpf == "123.456.789-00"
        assert valid_patient.biological_sex == BiologicalSex.FEMALE

    def test_patient_name_normalization(self) -> None:
        """Nome com espaços extras deve ser normalizado."""
        patient = Patient(
            full_name="  Maria   Silva   Santos  ",
            cpf="123.456.789-00",
            birth_date=date(1985, 3, 15),
            biological_sex=BiologicalSex.FEMALE,
        )
        assert patient.full_name == "Maria Silva Santos"

    def test_patient_invalid_cpf_format(self) -> None:
        """CPF com formato inválido deve falhar."""
        with pytest.raises(ValidationError) as exc_info:
            Patient(
                full_name="Maria Silva",
                cpf="12345678900",  # Formato inválido
                birth_date=date(1985, 3, 15),
                biological_sex=BiologicalSex.FEMALE,
            )
        assert "cpf" in str(exc_info.value)

    def test_patient_invalid_cpf_pattern(self) -> None:
        """CPF com padrão incorreto deve falhar."""
        with pytest.raises(ValidationError):
            Patient(
                full_name="Maria Silva",
                cpf="123.456.789-0",  # Incompleto
                birth_date=date(1985, 3, 15),
                biological_sex=BiologicalSex.FEMALE,
            )

    def test_patient_name_too_short(self) -> None:
        """Nome muito curto deve falhar."""
        with pytest.raises(ValidationError):
            Patient(
                full_name="M",
                cpf="123.456.789-00",
                birth_date=date(1985, 3, 15),
                biological_sex=BiologicalSex.FEMALE,
            )

    def test_patient_extra_fields_forbidden(self) -> None:
        """Campos extras devem ser rejeitados."""
        with pytest.raises(ValidationError) as exc_info:
            Patient(
                full_name="Maria Silva",
                cpf="123.456.789-00",
                birth_date=date(1985, 3, 15),
                biological_sex=BiologicalSex.FEMALE,
                unknown_field="valor",  # type: ignore
            )
        assert "extra" in str(exc_info.value).lower()

    def test_pregnant_patient_requires_gestational_weeks(self) -> None:
        """Gestante deve ter semanas gestacionais em ConsultationCreate."""
        patient = Patient(
            full_name="Ana Costa",
            cpf="111.222.333-44",
            birth_date=date(1992, 5, 10),
            biological_sex=BiologicalSex.FEMALE,
            is_pregnant=True,
            gestational_weeks=None,  # Faltando
        )
        # A validação ocorre em ConsultationCreate, não em Patient
        with pytest.raises(ValidationError) as exc_info:
            ConsultationCreate(
                patient=patient,
                consultation_date=date(2024, 1, 15),
                chief_complaint="Dor abdominal",
                professional_name="Dr. João",
            )
        assert "gestational_weeks" in str(exc_info.value)

    def test_male_cannot_be_pregnant(self) -> None:
        """Paciente masculino não pode ser gestante."""
        patient = Patient(
            full_name="João Silva",
            cpf="123.456.789-00",
            birth_date=date(1985, 3, 15),
            biological_sex=BiologicalSex.MALE,
            is_pregnant=True,
            gestational_weeks=20,
        )
        with pytest.raises(ValidationError) as exc_info:
            ConsultationCreate(
                patient=patient,
                consultation_date=date(2024, 1, 15),
                chief_complaint="Dor de cabeça",
                professional_name="Dr. João",
            )
        assert "is_pregnant" in str(exc_info.value).lower() or "male" in str(exc_info.value).lower()


class TestVitalSignsModel:
    """Testes para o modelo VitalSigns."""

    def test_valid_vital_signs(self, valid_vital_signs: VitalSigns) -> None:
        """Sinais vitais válidos devem ser criados."""
        assert valid_vital_signs.systolic_bp == 120
        assert valid_vital_signs.heart_rate == 72

    def test_vital_signs_all_optional(self) -> None:
        """Todos os campos de sinais vitais são opcionais."""
        vs = VitalSigns()
        assert vs.systolic_bp is None
        assert vs.heart_rate is None

    def test_vital_signs_bp_range(self) -> None:
        """Pressão arterial deve estar na faixa válida."""
        # Válido
        vs = VitalSigns(systolic_bp=120, diastolic_bp=80)
        assert vs.systolic_bp == 120

        # Inválido - muito baixo
        with pytest.raises(ValidationError):
            VitalSigns(systolic_bp=30)  # Mínimo é 40

        # Inválido - muito alto
        with pytest.raises(ValidationError):
            VitalSigns(systolic_bp=350)  # Máximo é 300

    def test_vital_signs_heart_rate_range(self) -> None:
        """Frequência cardíaca deve estar na faixa válida."""
        with pytest.raises(ValidationError):
            VitalSigns(heart_rate=10)  # Mínimo é 20

        with pytest.raises(ValidationError):
            VitalSigns(heart_rate=350)  # Máximo é 300

    def test_vital_signs_temperature_range(self) -> None:
        """Temperatura deve estar na faixa válida."""
        with pytest.raises(ValidationError):
            VitalSigns(temperature_celsius=25.0)  # Mínimo é 30

        with pytest.raises(ValidationError):
            VitalSigns(temperature_celsius=50.0)  # Máximo é 45

    def test_vital_signs_oxygen_saturation_range(self) -> None:
        """Saturação deve estar na faixa válida."""
        with pytest.raises(ValidationError):
            VitalSigns(oxygen_saturation=40)  # Mínimo é 50

        with pytest.raises(ValidationError):
            VitalSigns(oxygen_saturation=105)  # Máximo é 100

    def test_vital_signs_pain_scale_range(self) -> None:
        """Escala de dor deve estar entre 0 e 10."""
        vs = VitalSigns(pain_scale=0)
        assert vs.pain_scale == 0

        vs = VitalSigns(pain_scale=10)
        assert vs.pain_scale == 10

        with pytest.raises(ValidationError):
            VitalSigns(pain_scale=-1)

        with pytest.raises(ValidationError):
            VitalSigns(pain_scale=11)


class TestMedicationModel:
    """Testes para o modelo Medication."""

    def test_valid_medication(self, valid_medication: Medication) -> None:
        """Medicamento válido deve ser criado."""
        assert valid_medication.active_ingredient == "losartana potássica"
        assert valid_medication.frequency == MedicationFrequency.ONCE_DAILY

    def test_medication_required_fields(self) -> None:
        """Campos obrigatórios devem ser fornecidos."""
        with pytest.raises(ValidationError):
            Medication(
                active_ingredient="paracetamol",
                # dosage faltando
                frequency=MedicationFrequency.AS_NEEDED,
                route=MedicationRoute.ORAL,
            )  # type: ignore

    def test_medication_all_frequencies(self) -> None:
        """Todas as frequências devem ser válidas."""
        for freq in MedicationFrequency:
            med = Medication(
                active_ingredient="teste",
                dosage="10mg",
                frequency=freq,
                route=MedicationRoute.ORAL,
            )
            assert med.frequency == freq

    def test_medication_all_routes(self) -> None:
        """Todas as vias devem ser válidas."""
        for route in MedicationRoute:
            med = Medication(
                active_ingredient="teste",
                dosage="10mg",
                frequency=MedicationFrequency.ONCE_DAILY,
                route=route,
            )
            assert med.route == route


class TestAllergyModel:
    """Testes para o modelo Allergy."""

    def test_valid_allergy(self, valid_allergy: Allergy) -> None:
        """Alergia válida deve ser criada."""
        assert valid_allergy.allergen == "dipirona"
        assert valid_allergy.severity == "moderate"

    def test_allergy_severity_values(self) -> None:
        """Severidades válidas devem ser aceitas."""
        for severity in ["mild", "moderate", "severe", "life_threatening"]:
            allergy = Allergy(
                allergen="teste",
                reaction_type="allergic",
                severity=severity,
            )
            assert allergy.severity == severity

    def test_allergy_invalid_severity(self) -> None:
        """Severidade inválida deve falhar."""
        with pytest.raises(ValidationError):
            Allergy(
                allergen="teste",
                reaction_type="allergic",
                severity="invalid",
            )

    def test_allergy_reaction_types(self) -> None:
        """Tipos de reação válidos devem ser aceitos."""
        for reaction_type in ["allergic", "intolerance", "adverse"]:
            allergy = Allergy(
                allergen="teste",
                reaction_type=reaction_type,
                severity="mild",
            )
            assert allergy.reaction_type == reaction_type


class TestConsultationCreateModel:
    """Testes para o modelo ConsultationCreate."""

    def test_minimal_consultation(self, minimal_consultation: ConsultationCreate) -> None:
        """Consulta mínima deve ser válida."""
        assert minimal_consultation.patient.full_name == "Maria Silva Santos"
        assert minimal_consultation.strategy == SummarizerStrategy.RULE_BASED

    def test_complete_consultation(self, complete_consultation: ConsultationCreate) -> None:
        """Consulta completa deve ser válida."""
        assert complete_consultation.consultation_type == "follow_up"
        assert len(complete_consultation.current_medications) == 1
        assert len(complete_consultation.allergies) == 1

    def test_consultation_type_values(self, valid_patient: Patient) -> None:
        """Tipos de consulta válidos devem ser aceitos."""
        for consult_type in ["first_visit", "follow_up", "emergency", "telemedicine", "routine"]:
            consultation = ConsultationCreate(
                patient=valid_patient,
                consultation_date=date(2024, 1, 15),
                consultation_type=consult_type,
                chief_complaint="Dor de cabeça",
                professional_name="Dr. João",
            )
            assert consultation.consultation_type == consult_type

    def test_consultation_invalid_type(self, valid_patient: Patient) -> None:
        """Tipo de consulta inválido deve falhar."""
        with pytest.raises(ValidationError):
            ConsultationCreate(
                patient=valid_patient,
                consultation_date=date(2024, 1, 15),
                consultation_type="invalid_type",
                chief_complaint="Dor de cabeça",
                professional_name="Dr. João",
            )

    def test_consultation_strategy_default(self, valid_patient: Patient) -> None:
        """Estratégia padrão deve ser rule_based."""
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Dor de cabeça",
            professional_name="Dr. João",
        )
        assert consultation.strategy == SummarizerStrategy.RULE_BASED

    def test_consultation_chief_complaint_min_length(self, valid_patient: Patient) -> None:
        """Queixa principal muito curta deve falhar."""
        with pytest.raises(ValidationError):
            ConsultationCreate(
                patient=valid_patient,
                consultation_date=date(2024, 1, 15),
                chief_complaint="Dor",  # Mínimo 5 caracteres
                professional_name="Dr. João",
            )

    def test_consultation_professional_council_id_pattern(self, valid_patient: Patient) -> None:
        """Registro profissional deve seguir padrão."""
        # Válido
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Dor de cabeça",
            professional_name="Dr. João",
            professional_council_id="CRM-SP 123456",
        )
        assert consultation.professional_council_id == "CRM-SP 123456"

        # Inválido
        with pytest.raises(ValidationError):
            ConsultationCreate(
                patient=valid_patient,
                consultation_date=date(2024, 1, 15),
                chief_complaint="Dor de cabeça",
                professional_name="Dr. João",
                professional_council_id="12345",  # Formato inválido
            )

    def test_consultation_removes_empty_history_items(self, valid_patient: Patient) -> None:
        """Itens vazios no histórico devem ser removidos."""
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Dor de cabeça",
            professional_name="Dr. João",
            past_medical_history=["HAS", "", "  ", "DM2"],
        )
        assert consultation.past_medical_history == ["HAS", "DM2"]


class TestEnums:
    """Testes para os enums."""

    def test_biological_sex_values(self) -> None:
        """Valores de BiologicalSex devem estar corretos."""
        assert BiologicalSex.MALE.value == "male"
        assert BiologicalSex.FEMALE.value == "female"
        assert BiologicalSex.INTERSEX.value == "intersex"

    def test_blood_type_values(self) -> None:
        """Valores de BloodType devem estar corretos."""
        assert BloodType.O_POSITIVE.value == "O+"
        assert BloodType.AB_NEGATIVE.value == "AB-"

    def test_summarizer_strategy_values(self) -> None:
        """Valores de SummarizerStrategy devem estar corretos."""
        assert SummarizerStrategy.RULE_BASED.value == "rule_based"
        assert SummarizerStrategy.LLM_BASED.value == "llm_based"

    def test_warning_level_values(self) -> None:
        """Valores de WarningLevel devem estar corretos."""
        assert WarningLevel.INFO.value == "info"
        assert WarningLevel.LOW.value == "low"
        assert WarningLevel.MEDIUM.value == "medium"
        assert WarningLevel.HIGH.value == "high"
