"""
Testes para o validador clínico.

Verifica a geração de warnings para inconsistências e valores anormais.
"""

from datetime import date

import pytest

from app.models.common import BiologicalSex, MedicationFrequency, MedicationRoute, WarningLevel
from app.models.consultation import ConsultationCreate
from app.models.medication import Allergy, Medication
from app.models.patient import Patient, VitalSigns
from app.services.validators.clinical import ClinicalValidator


class TestClinicalValidatorVitalSigns:
    """Testes de validação de sinais vitais."""

    @pytest.fixture
    def validator(self) -> ClinicalValidator:
        """Instância do validador."""
        return ClinicalValidator()

    def test_missing_vital_signs_warning(
        self,
        validator: ClinicalValidator,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """Consulta sem sinais vitais deve gerar warning."""
        warnings = validator.validate(minimal_consultation)

        missing_vitals = [w for w in warnings if w.code == "MISSING_VITAL_SIGNS"]
        assert len(missing_vitals) == 1
        assert missing_vitals[0].level == WarningLevel.INFO

    def test_normal_vital_signs_no_warning(
        self,
        validator: ClinicalValidator,
        complete_consultation: ConsultationCreate,
    ) -> None:
        """Sinais vitais normais não devem gerar warnings de faixa."""
        warnings = validator.validate(complete_consultation)

        vital_warnings = [
            w for w in warnings
            if w.code.startswith("SYSTOLIC") or w.code.startswith("DIASTOLIC")
            or w.code.startswith("HEART") or w.code.startswith("RESPIRATORY")
        ]
        assert len(vital_warnings) == 0

    def test_high_blood_pressure_warning(
        self,
        validator: ClinicalValidator,
        consultation_with_abnormal_vitals: ConsultationCreate,
    ) -> None:
        """Pressão alta deve gerar warning."""
        warnings = validator.validate(consultation_with_abnormal_vitals)

        bp_warnings = [w for w in warnings if "BP" in w.code or "SYSTOLIC" in w.code]
        assert len(bp_warnings) > 0

    def test_critical_vital_signs_high_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
        critical_vital_signs: VitalSigns,
    ) -> None:
        """Sinais vitais críticos devem gerar warning HIGH."""
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Mal estar intenso",
            vital_signs=critical_vital_signs,
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        high_warnings = [w for w in warnings if w.level == WarningLevel.HIGH]
        assert len(high_warnings) > 0

    def test_bp_inconsistent_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
    ) -> None:
        """Sistólica <= diastólica deve gerar warning."""
        vital_signs = VitalSigns(
            systolic_bp=80,
            diastolic_bp=90,  # Maior que sistólica!
        )
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Check-up",
            vital_signs=vital_signs,
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        bp_inconsistent = [w for w in warnings if w.code == "BP_INCONSISTENT"]
        assert len(bp_inconsistent) == 1
        assert bp_inconsistent[0].level == WarningLevel.HIGH

    def test_low_pulse_pressure_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
    ) -> None:
        """Pressão de pulso muito baixa deve gerar warning."""
        vital_signs = VitalSigns(
            systolic_bp=100,
            diastolic_bp=90,  # Diferença de apenas 10
        )
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Check-up",
            vital_signs=vital_signs,
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        pulse_pressure = [w for w in warnings if w.code == "PULSE_PRESSURE_LOW"]
        assert len(pulse_pressure) == 1

    def test_tachycardia_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
    ) -> None:
        """Frequência cardíaca > 100 deve gerar warning."""
        vital_signs = VitalSigns(heart_rate=110)
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Palpitações",
            vital_signs=vital_signs,
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        hr_warnings = [w for w in warnings if "HEART_RATE" in w.code]
        assert len(hr_warnings) > 0

    def test_hypoxemia_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
    ) -> None:
        """SpO2 < 95% deve gerar warning."""
        vital_signs = VitalSigns(oxygen_saturation=92)
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Falta de ar",
            vital_signs=vital_signs,
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        spo2_warnings = [w for w in warnings if "OXYGEN" in w.code]
        assert len(spo2_warnings) > 0

    def test_fever_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
    ) -> None:
        """Temperatura > 37.5 deve gerar warning."""
        vital_signs = VitalSigns(temperature_celsius=38.5)
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Febre",
            vital_signs=vital_signs,
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        temp_warnings = [w for w in warnings if "TEMPERATURE" in w.code]
        assert len(temp_warnings) > 0


class TestClinicalValidatorPregnancy:
    """Testes de validação de gravidez."""

    @pytest.fixture
    def validator(self) -> ClinicalValidator:
        return ClinicalValidator()

    def test_pregnancy_young_age_warning(
        self,
        validator: ClinicalValidator,
    ) -> None:
        """Gravidez em paciente < 14 anos deve gerar warning HIGH."""
        # Paciente de 13 anos (nascido há 13 anos)
        from datetime import timedelta
        birth = date.today() - timedelta(days=13*365)  # ~13 anos atrás
        young_patient = Patient(
            full_name="Jovem Paciente",
            cpf="123.456.789-00",
            birth_date=birth,
            biological_sex=BiologicalSex.FEMALE,
            is_pregnant=True,
            gestational_weeks=12,
        )
        consultation = ConsultationCreate(
            patient=young_patient,
            consultation_date=date.today(),
            chief_complaint="Pré-natal",
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        young_pregnancy = [w for w in warnings if w.code == "PREGNANCY_YOUNG_AGE"]
        assert len(young_pregnancy) == 1
        assert young_pregnancy[0].level == WarningLevel.HIGH

    def test_pregnancy_advanced_age_warning(
        self,
        validator: ClinicalValidator,
    ) -> None:
        """Gravidez em paciente > 45 anos deve gerar warning MEDIUM."""
        older_patient = Patient(
            full_name="Paciente Idosa",
            cpf="123.456.789-00",
            birth_date=date(1975, 1, 1),  # ~49 anos
            biological_sex=BiologicalSex.FEMALE,
            is_pregnant=True,
            gestational_weeks=8,
        )
        consultation = ConsultationCreate(
            patient=older_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Pré-natal",
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        advanced_age = [w for w in warnings if w.code == "PREGNANCY_ADVANCED_AGE"]
        assert len(advanced_age) == 1
        assert advanced_age[0].level == WarningLevel.MEDIUM

    def test_post_term_pregnancy_warning(
        self,
        validator: ClinicalValidator,
    ) -> None:
        """Gravidez > 42 semanas deve gerar warning HIGH."""
        patient = Patient(
            full_name="Paciente Gestante",
            cpf="123.456.789-00",
            birth_date=date(1990, 1, 1),
            biological_sex=BiologicalSex.FEMALE,
            is_pregnant=True,
            gestational_weeks=44,  # Pós-termo
        )
        consultation = ConsultationCreate(
            patient=patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Pré-natal",
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        post_term = [w for w in warnings if w.code == "GESTATIONAL_WEEKS_HIGH"]
        assert len(post_term) == 1
        assert post_term[0].level == WarningLevel.HIGH


class TestClinicalValidatorAllergies:
    """Testes de validação de alergias."""

    @pytest.fixture
    def validator(self) -> ClinicalValidator:
        return ClinicalValidator()

    def test_severe_allergy_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
        severe_allergy: Allergy,
    ) -> None:
        """Alergia grave deve gerar warning."""
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Dor de cabeça",
            allergies=[severe_allergy],
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        severe_warnings = [w for w in warnings if w.code == "SEVERE_ALLERGIES_PRESENT"]
        assert len(severe_warnings) == 1
        assert "penicilina" in severe_warnings[0].message

    def test_unconfirmed_allergy_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
    ) -> None:
        """Alergia não confirmada deve gerar warning INFO."""
        unconfirmed = Allergy(
            allergen="camarão",
            reaction_type="allergic",
            severity="moderate",
            confirmed=False,
        )
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Dor de cabeça",
            allergies=[unconfirmed],
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        unconfirmed_warnings = [w for w in warnings if w.code == "UNCONFIRMED_ALLERGIES"]
        assert len(unconfirmed_warnings) == 1


class TestClinicalValidatorMedications:
    """Testes de validação de medicamentos."""

    @pytest.fixture
    def validator(self) -> ClinicalValidator:
        return ClinicalValidator()

    def test_medication_no_start_date_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
    ) -> None:
        """Medicamento sem data de início deve gerar warning INFO."""
        med_no_date = Medication(
            active_ingredient="metformina",
            dosage="850mg",
            frequency=MedicationFrequency.TWICE_DAILY,
            route=MedicationRoute.ORAL,
            # Sem start_date
        )
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Controle DM",
            current_medications=[med_no_date],
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        no_date_warnings = [w for w in warnings if w.code == "MEDICATION_NO_START_DATE"]
        assert len(no_date_warnings) == 1

    def test_medication_ended_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
    ) -> None:
        """Medicamento com data de término passada deve gerar warning."""
        ended_med = Medication(
            active_ingredient="amoxicilina",
            dosage="500mg",
            frequency=MedicationFrequency.THREE_TIMES_DAILY,
            route=MedicationRoute.ORAL,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 10),  # No passado
        )
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            chief_complaint="Retorno",
            current_medications=[ended_med],
            professional_name="Dr. João",
        )

        warnings = validator.validate(consultation)

        ended_warnings = [w for w in warnings if w.code == "MEDICATION_ENDED"]
        assert len(ended_warnings) == 1


class TestClinicalValidatorMissingData:
    """Testes de validação de dados ausentes."""

    @pytest.fixture
    def validator(self) -> ClinicalValidator:
        return ClinicalValidator()

    def test_missing_family_history_warning(
        self,
        validator: ClinicalValidator,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """Ausência de histórico familiar deve gerar warning INFO."""
        warnings = validator.validate(minimal_consultation)

        missing_family = [w for w in warnings if w.code == "MISSING_FAMILY_HISTORY"]
        assert len(missing_family) == 1

    def test_missing_past_history_warning(
        self,
        validator: ClinicalValidator,
        minimal_consultation: ConsultationCreate,
    ) -> None:
        """Ausência de antecedentes deve gerar warning INFO."""
        warnings = validator.validate(minimal_consultation)

        missing_past = [w for w in warnings if w.code == "MISSING_PAST_HISTORY"]
        assert len(missing_past) == 1

    def test_emergency_without_vitals_warning(
        self,
        validator: ClinicalValidator,
        valid_patient: Patient,
    ) -> None:
        """Emergência sem sinais vitais deve gerar warning MEDIUM."""
        consultation = ConsultationCreate(
            patient=valid_patient,
            consultation_date=date(2024, 1, 15),
            consultation_type="emergency",
            chief_complaint="Dor torácica aguda",
            professional_name="Dr. João",
            # Sem vital_signs
        )

        warnings = validator.validate(consultation)

        emergency_no_vitals = [w for w in warnings if w.code == "EMERGENCY_NO_VITALS"]
        assert len(emergency_no_vitals) == 1
        assert emergency_no_vitals[0].level == WarningLevel.MEDIUM
