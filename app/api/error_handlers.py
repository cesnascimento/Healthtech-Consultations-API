from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.errors import HealthtechError


def register_error_handlers(app: FastAPI) -> None:
    """
    Registra handlers de erro na aplicação FastAPI.

    Args:
        app: Instância da aplicação FastAPI.
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """
        Handler para erros de validação do Pydantic/FastAPI.

        Retorna erro 422 com detalhes dos campos inválidos.
        """
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "loc": list(error.get("loc", [])),
                    "msg": error.get("msg", "Erro de validação"),
                    "type": error.get("type", "validation_error"),
                }
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": errors},
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        """
        Handler para erros de validação do Pydantic puro.

        Captura erros que ocorrem fora do contexto do FastAPI.
        """
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "loc": list(error.get("loc", [])),
                    "msg": error.get("msg", "Erro de validação"),
                    "type": error.get("type", "validation_error"),
                }
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": errors},
        )

    @app.exception_handler(HealthtechError)
    async def healthtech_error_handler(
        request: Request,
        exc: HealthtechError,
    ) -> JSONResponse:
        """
        Handler para exceções customizadas da aplicação.

        Retorna erro com código e mensagem padronizados.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": exc.message,
                "code": exc.code,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """
        Handler para exceções não tratadas.

        Retorna erro genérico sem expor detalhes internos.
        Em produção, deve logar o erro completo.
        """
        # TODO: Adicionar logging em produção
        # logger.error(f"Unhandled exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Erro interno do servidor",
                "code": "INTERNAL_ERROR",
            },
        )
