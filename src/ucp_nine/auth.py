from dataclasses import dataclass
from typing import Annotated, Callable, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant_id: str
    scopes: frozenset[str]


TOKENS = {
    "demo-agent-token": Principal(
        subject="agentic-commerce-client",
        tenant_id="tenant_naresh",
        scopes=frozenset({"journey:run", "tools:invoke", "agents:read"}),
    ),
    "demo-analyst-token": Principal(
        subject="portfolio-reviewer",
        tenant_id="tenant_naresh",
        scopes=frozenset({"agents:read"}),
    ),
}


def authenticate(credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)]) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    principal = TOKENS.get(credentials.credentials)
    if principal is None:
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    return principal


def require_scope(scope: str) -> Callable[[Principal], Principal]:
    def dependency(principal: Annotated[Principal, Depends(authenticate)]) -> Principal:
        if scope not in principal.scopes:
            raise HTTPException(status_code=403, detail=f"Missing scope: {scope}")
        return principal

    return dependency
