from datetime import date

from app.core.constants import VITAL_SIGNS_RANGES, VitalSignRange
from app.models.common import BiologicalSex, WarningLevel
from app.models.consultation import ConsultationCreate, ConsultationWarning
from app.models.patient import VitalSigns
from app.utils.text import TextProcessor


class ClinicalValidator:
    """
    Validador de regras clínicas para consultas.

    Gera warnings não-bloqueantes para inconsistências
    e valores fora das faixas de referência.

    Todas as validações são determinísticas e baseadas em regras.
    """

    def __init__(self) -> None:
        """Inicializa o validador."""
        self._warnings: list[ConsultationWarning] = []

    def validate(self, consultation: ConsultationCreate) -> list[ConsultationWarning]:
        """
        Executa todas as validações clínicas.

        Args:
            consultation: Dados da consulta a validar.

        Returns:
            Lista de warnings gerados.
        """
        self._warnings = []

        self._validate_vital_signs(consultation.vital_signs)
        self._validate_blood_pressure_consistency(consultation.vital_signs)
        self._validate_pregnancy(consultation)
        self._validate_age_specific(consultation)
        self._validate_medications(consultation)
        self._validate_allergies(consultation)
        self._validate_missing_data(consultation)

        return self._warnings

    def _add_warning(
        self,
        code: str,
        level: WarningLevel,
        message: str,
        field: str | None = None,
        value: str | None = None,
    ) -> None:
        """Adiciona um warning à lista."""
        self._warnings.append(
            ConsultationWarning(
                code=code,
                level=level,
                message=message,
                field=field,
                value=value,
            )
        )

    def _validate_vital_signs(self, vital_signs: VitalSigns | None) -> None:
        """Valida sinais vitais contra faixas de referência."""
        if not vital_signs:
            self._add_warning(
                code="MISSING_VITAL_SIGNS",
                level=WarningLevel.INFO,
                message="Sinais vitais não informados na consulta",
            )
            return

        vital_checks = [
            ("systolic_bp", vital_signs.systolic_bp, "Pressão sistólica"),
            ("diastolic_bp", vital_signs.diastolic_bp, "Pressão diastólica"),
            ("heart_rate", vital_signs.heart_rate, "Frequência cardíaca"),
            ("respiratory_rate", vital_signs.respiratory_rate, "Frequência respiratória"),
            ("temperature_celsius", vital_signs.temperature_celsius, "Temperatura"),
            ("oxygen_saturation", vital_signs.oxygen_saturation, "Saturação O2"),
        ]

        for field_name, value, label in vital_checks:
            if value is not None and field_name in VITAL_SIGNS_RANGES:
                self._check_vital_range(field_name, value, label)

    def _check_vital_range(
        self,
        field_name: str,
        value: int | float,
        label: str,
    ) -> None:
        """Verifica se um sinal vital está dentro das faixas."""
        range_def: VitalSignRange = VITAL_SIGNS_RANGES[field_name]

        if value < range_def.min_critical:
            self._add_warning(
                code=f"{field_name.upper()}_CRITICAL_LOW",
                level=WarningLevel.HIGH,
                message=f"{label} criticamente baixa: {value} {range_def.unit}",
                field=f"vital_signs.{field_name}",
                value=str(value),
            )
        elif value < range_def.min_normal:
            self._add_warning(
                code=f"{field_name.upper()}_LOW",
                level=WarningLevel.MEDIUM,
                message=f"{label} abaixo do esperado: {value} {range_def.unit}",
                field=f"vital_signs.{field_name}",
                value=str(value),
            )
        elif value > range_def.max_critical:
            self._add_warning(
                code=f"{field_name.upper()}_CRITICAL_HIGH",
                level=WarningLevel.HIGH,
                message=f"{label} criticamente elevada: {value} {range_def.unit}",
                field=f"vital_signs.{field_name}",
                value=str(value),
            )
        elif value > range_def.max_normal:
            self._add_warning(
                code=f"{field_name.upper()}_HIGH",
                level=WarningLevel.LOW,
                message=f"{label} acima do esperado: {value} {range_def.unit}",
                field=f"vital_signs.{field_name}",
                value=str(value),
            )

    def _validate_blood_pressure_consistency(
        self, vital_signs: VitalSigns | None
    ) -> None:
        """Valida consistência entre pressão sistólica e diastólica."""
        if not vital_signs:
            return

        systolic = vital_signs.systolic_bp
        diastolic = vital_signs.diastolic_bp

        if systolic is not None and diastolic is not None:
            if systolic <= diastolic:
                self._add_warning(
                    code="BP_INCONSISTENT",
                    level=WarningLevel.HIGH,
                    message=(
                        f"Pressão sistólica ({systolic}) deve ser maior que "
                        f"diastólica ({diastolic})"
                    ),
                    field="vital_signs",
                    value=f"{systolic}/{diastolic}",
                )

            pulse_pressure = systolic - diastolic
            if pulse_pressure < 25:
                self._add_warning(
                    code="PULSE_PRESSURE_LOW",
                    level=WarningLevel.MEDIUM,
                    message=f"Pressão de pulso baixa: {pulse_pressure} mmHg",
                    field="vital_signs",
                    value=str(pulse_pressure),
                )
            elif pulse_pressure > 60:
                self._add_warning(
                    code="PULSE_PRESSURE_HIGH",
                    level=WarningLevel.LOW,
                    message=f"Pressão de pulso elevada: {pulse_pressure} mmHg",
                    field="vital_signs",
                    value=str(pulse_pressure),
                )

    def _validate_pregnancy(self, consultation: ConsultationCreate) -> None:
        """Valida dados relacionados à gravidez."""
        patient = consultation.patient

        if patient.is_pregnant:
            age = TextProcessor.calculate_age(str(patient.birth_date))
            if age is not None:
                if age < 14:
                    self._add_warning(
                        code="PREGNANCY_YOUNG_AGE",
                        level=WarningLevel.HIGH,
                        message=f"Gravidez em paciente com {age} anos requer atenção especial",
                        field="patient.is_pregnant",
                        value=str(age),
                    )
                elif age > 45:
                    self._add_warning(
                        code="PREGNANCY_ADVANCED_AGE",
                        level=WarningLevel.MEDIUM,
                        message=f"Gravidez em paciente com {age} anos (idade materna avançada)",
                        field="patient.is_pregnant",
                        value=str(age),
                    )

            weeks = patient.gestational_weeks
            if weeks is not None and weeks > 42:
                self._add_warning(
                    code="GESTATIONAL_WEEKS_HIGH",
                    level=WarningLevel.HIGH,
                    message=f"Idade gestacional de {weeks} semanas (pós-termo)",
                    field="patient.gestational_weeks",
                    value=str(weeks),
                )

    def _validate_age_specific(self, consultation: ConsultationCreate) -> None:
        """Valida regras específicas por faixa etária."""
        age = TextProcessor.calculate_age(str(consultation.patient.birth_date))
        if age is None:
            return

        vital_signs = consultation.vital_signs
        if not vital_signs:
            return

        if age < 12 and vital_signs.heart_rate is not None:
            if vital_signs.heart_rate < 70:
                self._add_warning(
                    code="PEDIATRIC_HR_LOW",
                    level=WarningLevel.MEDIUM,
                    message=(
                        f"FC de {vital_signs.heart_rate} bpm pode ser baixa "
                        f"para paciente pediátrico ({age} anos)"
                    ),
                    field="vital_signs.heart_rate",
                    value=str(vital_signs.heart_rate),
                )

        if age >= 80 and vital_signs.systolic_bp is not None:
            if vital_signs.systolic_bp > 150 and vital_signs.systolic_bp <= 160:
                pass

    def _validate_medications(self, consultation: ConsultationCreate) -> None:
        """Valida dados de medicamentos."""
        for idx, med in enumerate(consultation.current_medications):
            if med.start_date is None:
                self._add_warning(
                    code="MEDICATION_NO_START_DATE",
                    level=WarningLevel.INFO,
                    message=f"Medicamento '{med.active_ingredient}' sem data de início",
                    field=f"current_medications[{idx}].start_date",
                    value="null",
                )

            if med.end_date is not None and med.end_date < date.today():
                self._add_warning(
                    code="MEDICATION_ENDED",
                    level=WarningLevel.LOW,
                    message=(
                        f"Medicamento '{med.active_ingredient}' com data de "
                        f"término no passado ({med.end_date})"
                    ),
                    field=f"current_medications[{idx}].end_date",
                    value=str(med.end_date),
                )

    def _validate_allergies(self, consultation: ConsultationCreate) -> None:
        """Valida dados de alergias."""
        severe_allergies = [
            a for a in consultation.allergies
            if a.severity in ("severe", "life_threatening")
        ]

        if severe_allergies:
            allergens = ", ".join(a.allergen for a in severe_allergies)
            self._add_warning(
                code="SEVERE_ALLERGIES_PRESENT",
                level=WarningLevel.MEDIUM,
                message=f"Paciente possui alergias graves: {allergens}",
                field="allergies",
                value=str(len(severe_allergies)),
            )

        unconfirmed = [a for a in consultation.allergies if not a.confirmed]
        if unconfirmed:
            self._add_warning(
                code="UNCONFIRMED_ALLERGIES",
                level=WarningLevel.INFO,
                message=f"{len(unconfirmed)} alergia(s) não confirmada(s) por exame",
                field="allergies",
                value=str(len(unconfirmed)),
            )

    def _validate_missing_data(self, consultation: ConsultationCreate) -> None:
        """Verifica dados opcionais ausentes que podem ser relevantes."""
        if not consultation.family_history:
            self._add_warning(
                code="MISSING_FAMILY_HISTORY",
                level=WarningLevel.INFO,
                message="Histórico familiar não informado",
                field="family_history",
                value="[]",
            )

        if not consultation.past_medical_history:
            self._add_warning(
                code="MISSING_PAST_HISTORY",
                level=WarningLevel.INFO,
                message="Antecedentes patológicos não informados",
                field="past_medical_history",
                value="[]",
            )

        if consultation.consultation_type == "emergency" and not consultation.vital_signs:
            self._add_warning(
                code="EMERGENCY_NO_VITALS",
                level=WarningLevel.MEDIUM,
                message="Consulta de emergência sem sinais vitais registrados",
                field="vital_signs",
                value="null",
            )
