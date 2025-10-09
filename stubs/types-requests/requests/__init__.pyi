from collections.abc import Mapping
from typing import Optional

class Response:
    def raise_for_status(self) -> None: ...
    def json(self) -> object: ...

class Session:
    def post(
        self,
        url: str,
        *,
        json: Mapping[str, object] | None = ...,
        headers: Mapping[str, str] | None = ...,
        timeout: Optional[float] = ...,
    ) -> Response: ...
