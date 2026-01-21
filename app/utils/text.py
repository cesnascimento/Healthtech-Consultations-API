"""
Utilitários para processamento de texto.

Funções puras para normalização, truncamento e formatação
de textos clínicos.
"""

from app.core.constants import TEXT_LIMITS


class TextProcessor:
    """
    Processador de texto para normalização e formatação.

    Todas as operações são determinísticas e sem efeitos colaterais.
    """

    @staticmethod
    def truncate(
        text: str | None,
        max_length: int,
        suffix: str = "...",
    ) -> tuple[str, bool]:
        """
        Trunca texto para o limite máximo especificado.

        Args:
            text: Texto a ser truncado (None retorna string vazia).
            max_length: Comprimento máximo permitido.
            suffix: Sufixo a adicionar quando truncado.

        Returns:
            Tupla (texto_truncado, foi_truncado).

        Example:
            >>> TextProcessor.truncate("Hello World", 5)
            ('He...', True)
            >>> TextProcessor.truncate("Hi", 10)
            ('Hi', False)
        """
        if not text:
            return "", False

        text = text.strip()

        if len(text) <= max_length:
            return text, False

        truncated = text[: max_length - len(suffix)].strip() + suffix
        return truncated, True

    @staticmethod
    def normalize_whitespace(text: str | None) -> str:
        """
        Normaliza espaços em branco no texto.

        Remove espaços duplicados, tabs e quebras de linha excessivas.

        Args:
            text: Texto a normalizar.

        Returns:
            Texto com espaços normalizados.
        """
        if not text:
            return ""

        import re

        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def remove_duplicates(items: list[str]) -> tuple[list[str], list[str]]:
        """
        Remove itens duplicados preservando ordem.

        Args:
            items: Lista de strings.

        Returns:
            Tupla (lista_sem_duplicatas, duplicatas_removidas).

        Example:
            >>> TextProcessor.remove_duplicates(["a", "b", "a", "c"])
            (['a', 'b', 'c'], ['a'])
        """
        seen: set[str] = set()
        unique: list[str] = []
        duplicates: list[str] = []

        for item in items:
            normalized = item.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(item.strip())
            elif normalized:
                duplicates.append(item.strip())

        return unique, duplicates

    @staticmethod
    def format_date_br(date_str: str) -> str:
        """
        Converte data ISO para formato brasileiro.

        Args:
            date_str: Data no formato YYYY-MM-DD.

        Returns:
            Data no formato DD/MM/YYYY.

        Example:
            >>> TextProcessor.format_date_br("1985-03-15")
            '15/03/1985'
        """
        try:
            from datetime import datetime

            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            return str(date_str)

    @staticmethod
    def calculate_age(birth_date_str: str) -> int | None:
        """
        Calcula idade a partir da data de nascimento.

        Args:
            birth_date_str: Data de nascimento (YYYY-MM-DD).

        Returns:
            Idade em anos ou None se data inválida.
        """
        try:
            from datetime import date, datetime

            birth = datetime.fromisoformat(birth_date_str).date()
            today = date.today()
            age = today.year - birth.year

            if (today.month, today.day) < (birth.month, birth.day):
                age -= 1

            return age
        except (ValueError, TypeError):
            return None

    @staticmethod
    def mask_cpf(cpf: str) -> str:
        """
        Mascara CPF para exibição parcial.

        Args:
            cpf: CPF no formato XXX.XXX.XXX-XX.

        Returns:
            CPF mascarado: ***.***.XXX-XX.

        Example:
            >>> TextProcessor.mask_cpf("123.456.789-00")
            '***.***789-00'
        """
        if not cpf or len(cpf) < 14:
            return cpf or ""

        return f"***.***{cpf[7:]}"

    @staticmethod
    def format_vital_sign(
        value: int | float | None,
        unit: str,
        label: str | None = None,
    ) -> str | None:
        """
        Formata um sinal vital para exibição.

        Args:
            value: Valor numérico do sinal vital.
            unit: Unidade de medida.
            label: Rótulo opcional (ex: "PA", "FC").

        Returns:
            String formatada ou None se valor ausente.

        Example:
            >>> TextProcessor.format_vital_sign(120, "mmHg", "PAS")
            'PAS: 120 mmHg'
        """
        if value is None:
            return None

        if label:
            return f"{label}: {value} {unit}"
        return f"{value} {unit}"

    @staticmethod
    def get_limit(field_name: str) -> int:
        """
        Obtém o limite de caracteres para um campo.

        Args:
            field_name: Nome do campo.

        Returns:
            Limite de caracteres (padrão 2000 se não definido).
        """
        return TEXT_LIMITS.get(field_name, 2000)
