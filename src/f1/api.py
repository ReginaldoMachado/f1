"""Cliente HTTP para os endpoints históricos da API OpenF1."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

Record = dict[str, Any]


class OpenF1APIError(Exception):
    """Indica falha ao consultar ou interpretar uma resposta da OpenF1."""


class OpenF1Client:
    """Consulta dados da OpenF1 sem acoplar o transporte à interface."""

    def __init__(
        self,
        base_url: str = "https://api.openf1.org/v1",
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(
        self,
        endpoint: str,
        params: dict[str, str | int] | None = None,
    ) -> list[Record]:
        query = urlencode(params or {})
        url = f"{self.base_url}/{endpoint}"
        if query:
            url = f"{url}?{query}"

        try:
            with urlopen(url, timeout=self.timeout) as response:
                payload = json.loads(response.read())
        except HTTPError as error:
            raise OpenF1APIError(
                f"A OpenF1 respondeu com HTTP {error.code} ao consultar /{endpoint}."
            ) from error
        except (URLError, TimeoutError) as error:
            raise OpenF1APIError(
                f"Não foi possível consultar /{endpoint} na OpenF1: {error}."
            ) from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise OpenF1APIError(
                f"A OpenF1 retornou JSON inválido em /{endpoint}."
            ) from error

        if not isinstance(payload, list) or not all(
            isinstance(record, dict) for record in payload
        ):
            raise OpenF1APIError(
                f"A resposta de /{endpoint} não contém uma lista de registros."
            )
        return payload

    def get_meetings(self, year: int) -> list[Record]:
        """Retorna os eventos disponíveis para uma temporada."""
        return self._get("meetings", {"year": year})

    def get_sessions(self, meeting_key: str | int) -> list[Record]:
        """Retorna as sessões de um evento."""
        return self._get("sessions", {"meeting_key": meeting_key})

    def get_drivers(self, session_key: str | int) -> list[Record]:
        """Retorna os pilotos participantes de uma sessão."""
        return self._get("drivers", {"session_key": session_key})

    def get_laps(self, session_key: str | int) -> list[Record]:
        """Retorna as voltas registradas em uma sessão."""
        return self._get("laps", {"session_key": session_key})

    def get_session_results(self, session_key: str | int) -> list[Record]:
        """Retorna o resultado final publicado para uma sessão."""
        return self._get("session_result", {"session_key": session_key})
