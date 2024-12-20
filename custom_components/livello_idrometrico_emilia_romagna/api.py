"""Sample API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout


class IntegrationBlueprintApiClientError(Exception):
    """Exception to indicate a general API error."""


class IntegrationBlueprintApiClientCommunicationError(
    IntegrationBlueprintApiClientError,
):
    """Exception to indicate a communication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    response.raise_for_status()


class IntegrationBlueprintApiClient:
    """Sample API Client."""

    def __init__(
        self,
        station_name: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Sample API Client."""
        self._station_name = station_name
        self._session = session

    async def async_get_data(self) -> Any:
        """Get station data."""
        result = None
        """Get data from the API."""
        stations = await self.async_get_stations()
        for station in stations:
            if station["nomestaz"] == self._station_name:
                station_id = station["idstazione"]
                result = {
                    "lon": station["lon"],
                    "lat": station["lat"],
                    "soglia1": station["soglia1"],
                    "soglia2": station["soglia2"],
                    "soglia3": station["soglia3"],
                    "value": None,
                }

                values = await self._api_wrapper(
                    method="get",
                    url="https://allertameteo.regione.emilia-romagna.it/o/api/allerta/get-time-series/?stazione="
                    + station_id
                    + "&variabile=254,0,0/1,-,-,-/B13215",
                )
                t = 0
                v = None
                for value in values:
                    if value["v"] is not None and value["t"] > t:
                        t = value["t"]
                        v = value["v"]

                if v is not None:
                    result["value"] = v

        return result

    async def async_get_stations(self) -> Any:
        """Get the stations from the web api."""
        result = []
        stations = await self._api_wrapper(
            method="get",
            url="https://allertameteo.regione.emilia-romagna.it/o/api/allerta/get-sensor-values-no-time?variabile=254,0,0/1,-,-,-/B13215",
        )
        for station in stations:
            if "nomestaz" in station:
                result.append(station)  # noqa: PERF401

        return result

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise IntegrationBlueprintApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise IntegrationBlueprintApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise IntegrationBlueprintApiClientError(
                msg,
            ) from exception
