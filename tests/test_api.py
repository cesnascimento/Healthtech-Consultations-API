"""
Testes para os endpoints da API.

Testes de integração para verificar o comportamento dos endpoints.
"""

from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Testes para o endpoint /health."""

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_response_structure(self, client: TestClient) -> None:
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "rule_engine_version" in data
        assert "timestamp" in data
        assert "summarizer_strategy" in data
        assert "llm_enabled" in data

    def test_health_status_healthy(self, client: TestClient) -> None:
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_default_strategy(self, client: TestClient) -> None:
        response = client.get("/health")
        data = response.json()

        # Estratégia depende do .env (rule_based ou llm_based)
        assert data["summarizer_strategy"] in ["rule_based", "llm_based"]


class TestConsultationsEndpoint:
    """Testes para o endpoint POST /consultations."""

    def test_minimal_consultation_returns_200(
        self,
        client: TestClient,
        minimal_consultation_dict: dict[str, Any],
    ) -> None:
        response = client.post("/consultations", json=minimal_consultation_dict)
        assert response.status_code == status.HTTP_200_OK

    def test_complete_consultation_returns_200(
        self,
        client: TestClient,
        complete_consultation_dict: dict[str, Any],
    ) -> None:
        response = client.post("/consultations", json=complete_consultation_dict)
        assert response.status_code == status.HTTP_200_OK

    def test_response_structure(
        self,
        client: TestClient,
        minimal_consultation_dict: dict[str, Any],
    ) -> None:
        response = client.post("/consultations", json=minimal_consultation_dict)
        data = response.json()

        assert "summary" in data
        assert "sections" in data["summary"]
        assert "full_text" in data["summary"]
        assert "warnings" in data
        assert "metadata" in data

    def test_metadata_structure(
        self,
        client: TestClient,
        minimal_consultation_dict: dict[str, Any],
    ) -> None:
        response = client.post("/consultations", json=minimal_consultation_dict)
        data = response.json()
        metadata = data["metadata"]

        assert "request_id" in metadata
        assert "strategy_used" in metadata
        assert "strategy_requested" in metadata
        assert "rule_engine_version" in metadata
        assert "processed_at" in metadata
        assert "processing_time_ms" in metadata

    def test_request_id_is_uuid(
        self,
        client: TestClient,
        minimal_consultation_dict: dict[str, Any],
    ) -> None:
        import uuid

        response = client.post("/consultations", json=minimal_consultation_dict)
        data = response.json()

        request_id = data["metadata"]["request_id"]
        uuid.UUID(request_id)

    def test_strategy_used_is_rule_based(
        self,
        client: TestClient,
        minimal_consultation_dict: dict[str, Any],
    ) -> None:
        response = client.post("/consultations", json=minimal_consultation_dict)
        data = response.json()

        assert data["metadata"]["strategy_used"] == "rule_based"
        assert data["metadata"]["strategy_requested"] == "rule_based"

    def test_sections_have_required_fields(
        self,
        client: TestClient,
        minimal_consultation_dict: dict[str, Any],
    ) -> None:
        response = client.post("/consultations", json=minimal_consultation_dict)
        data = response.json()

        for section in data["summary"]["sections"]:
            assert "title" in section
            assert "code" in section
            assert "content" in section
            assert "order" in section

    def test_sections_ordered_correctly(
        self,
        client: TestClient,
        complete_consultation_dict: dict[str, Any],
    ) -> None:
        response = client.post("/consultations", json=complete_consultation_dict)
        data = response.json()

        orders = [s["order"] for s in data["summary"]["sections"]]
        assert orders == sorted(orders)

    def test_identification_section_present(
        self,
        client: TestClient,
        minimal_consultation_dict: dict[str, Any],
    ) -> None:
        response = client.post("/consultations", json=minimal_consultation_dict)
        data = response.json()

        codes = [s["code"] for s in data["summary"]["sections"]]
        assert "identification" in codes

    def test_warnings_are_list(
        self,
        client: TestClient,
        minimal_consultation_dict: dict[str, Any],
    ) -> None:
        response = client.post("/consultations", json=minimal_consultation_dict)
        data = response.json()

        assert isinstance(data["warnings"], list)

    def test_minimal_consultation_generates_warnings(
        self,
        client: TestClient,
        minimal_consultation_dict: dict[str, Any],
    ) -> None:
        response = client.post("/consultations", json=minimal_consultation_dict)
        data = response.json()

        warning_codes = [w["code"] for w in data["warnings"]]
        assert "MISSING_VITAL_SIGNS" in warning_codes

    def test_abnormal_vitals_generate_warnings(
        self,
        client: TestClient,
    ) -> None:
        """Sinais vitais anormais devem gerar warnings."""
        payload = {
            "patient": {
                "full_name": "Teste Paciente",
                "cpf": "123.456.789-00",
                "birth_date": "1985-03-15",
                "biological_sex": "female",
            },
            "consultation_date": "2024-01-15",
            "chief_complaint": "Mal estar geral",
            "vital_signs": {
                "systolic_bp": 180,
                "diastolic_bp": 110,
                "heart_rate": 120,
            },
            "professional_name": "Dr. Teste",
        }

        response = client.post("/consultations", json=payload)
        data = response.json()

        warning_codes = [w["code"] for w in data["warnings"]]
        assert any("BP" in code or "SYSTOLIC" in code for code in warning_codes)


class TestConsultationsValidation:
    """Testes de validação do endpoint /consultations."""

    def test_missing_patient_returns_422(self, client: TestClient) -> None:
        payload = {
            "consultation_date": "2024-01-15",
            "chief_complaint": "Dor de cabeça",
            "professional_name": "Dr. João",
        }

        response = client.post("/consultations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_cpf_returns_422(self, client: TestClient) -> None:
        payload = {
            "patient": {
                "full_name": "Teste",
                "cpf": "12345678900",
                "birth_date": "1985-03-15",
                "biological_sex": "female",
            },
            "consultation_date": "2024-01-15",
            "chief_complaint": "Dor de cabeça",
            "professional_name": "Dr. João",
        }

        response = client.post("/consultations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_date_format_returns_422(self, client: TestClient) -> None:
        payload = {
            "patient": {
                "full_name": "Teste Paciente",
                "cpf": "123.456.789-00",
                "birth_date": "15/03/1985",
                "biological_sex": "female",
            },
            "consultation_date": "2024-01-15",
            "chief_complaint": "Dor de cabeça",
            "professional_name": "Dr. João",
        }

        response = client.post("/consultations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_biological_sex_returns_422(self, client: TestClient) -> None:
        payload = {
            "patient": {
                "full_name": "Teste Paciente",
                "cpf": "123.456.789-00",
                "birth_date": "1985-03-15",
                "biological_sex": "invalid",
            },
            "consultation_date": "2024-01-15",
            "chief_complaint": "Dor de cabeça",
            "professional_name": "Dr. João",
        }

        response = client.post("/consultations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chief_complaint_too_short_returns_422(self, client: TestClient) -> None:
        payload = {
            "patient": {
                "full_name": "Teste Paciente",
                "cpf": "123.456.789-00",
                "birth_date": "1985-03-15",
                "biological_sex": "female",
            },
            "consultation_date": "2024-01-15",
            "chief_complaint": "Dor",
            "professional_name": "Dr. João",
        }

        response = client.post("/consultations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_extra_fields_returns_422(self, client: TestClient) -> None:
        payload = {
            "patient": {
                "full_name": "Teste Paciente",
                "cpf": "123.456.789-00",
                "birth_date": "1985-03-15",
                "biological_sex": "female",
                "unknown_field": "value",
            },
            "consultation_date": "2024-01-15",
            "chief_complaint": "Dor de cabeça",
            "professional_name": "Dr. João",
        }

        response = client.post("/consultations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_vital_signs_out_of_range_returns_422(self, client: TestClient) -> None:
        payload = {
            "patient": {
                "full_name": "Teste Paciente",
                "cpf": "123.456.789-00",
                "birth_date": "1985-03-15",
                "biological_sex": "female",
            },
            "consultation_date": "2024-01-15",
            "chief_complaint": "Dor de cabeça",
            "vital_signs": {
                "systolic_bp": 500,
            },
            "professional_name": "Dr. João",
        }

        response = client.post("/consultations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_medication_frequency_returns_422(self, client: TestClient) -> None:
        payload = {
            "patient": {
                "full_name": "Teste Paciente",
                "cpf": "123.456.789-00",
                "birth_date": "1985-03-15",
                "biological_sex": "female",
            },
            "consultation_date": "2024-01-15",
            "chief_complaint": "Dor de cabeça",
            "current_medications": [
                {
                    "active_ingredient": "paracetamol",
                    "dosage": "500mg",
                    "frequency": "invalid_frequency",
                    "route": "oral",
                }
            ],
            "professional_name": "Dr. João",
        }

        response = client.post("/consultations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_pregnant_male_returns_422(self, client: TestClient) -> None:
        payload = {
            "patient": {
                "full_name": "João Silva",
                "cpf": "123.456.789-00",
                "birth_date": "1985-03-15",
                "biological_sex": "male",
                "is_pregnant": True,
                "gestational_weeks": 20,
            },
            "consultation_date": "2024-01-15",
            "chief_complaint": "Dor de cabeça",
            "professional_name": "Dr. João",
        }

        response = client.post("/consultations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_validation_error_response_format(self, client: TestClient) -> None:
        payload = {
            "patient": {
                "full_name": "T",
                "cpf": "invalid",
                "birth_date": "1985-03-15",
                "biological_sex": "female",
            },
            "consultation_date": "2024-01-15",
            "chief_complaint": "Dor de cabeça",
            "professional_name": "Dr. João",
        }

        response = client.post("/consultations", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

        for error in data["detail"]:
            assert "loc" in error
            assert "msg" in error
            assert "type" in error


class TestRootEndpoint:
    """Testes para o endpoint raiz."""

    def test_root_returns_200(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

    def test_root_contains_docs_link(self, client: TestClient) -> None:
        response = client.get("/")
        data = response.json()

        assert "docs" in data


class TestOpenAPIEndpoint:
    """Testes para o endpoint OpenAPI."""

    def test_openapi_returns_200(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK

    def test_openapi_is_valid_json(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_openapi_contains_consultations_path(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        data = response.json()

        assert "/consultations" in data["paths"]

    def test_openapi_contains_health_path(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        data = response.json()

        assert "/health" in data["paths"]
