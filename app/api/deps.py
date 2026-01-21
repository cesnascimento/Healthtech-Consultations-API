"""
Dependências injetáveis para os endpoints.

Centraliza a criação de dependências utilizadas
pelos endpoints via FastAPI Depends.
"""

from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.summarizers import SummarizerProtocol, get_summarizer


def get_settings_dep() -> Settings:
    """
    Dependência para obter configurações.

    Returns:
        Instância de Settings.
    """
    return get_settings()


def get_summarizer_dep() -> SummarizerProtocol:
    """
    Dependência para obter summarizer padrão.

    Retorna o summarizer configurado no ambiente.

    Returns:
        Instância de SummarizerProtocol.
    """
    return get_summarizer()


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
SummarizerDep = Annotated[SummarizerProtocol, Depends(get_summarizer_dep)]
