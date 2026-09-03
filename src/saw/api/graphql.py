"""GraphQL API for Smart Agent Wiki.

Phase 6: API Platform — GraphQL endpoint.
Per APIP-07: GraphQL endpoint.

Uses Strawberry for GraphQL implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

# Strawberry GraphQL imports (lazy)
_strawberry = None


def _get_strawberry():
    global _strawberry
    if _strawberry is None:
        try:
            import strawberry
            _strawberry = strawberry
        except ImportError:
            raise ImportError(
                "Strawberry GraphQL not installed. Install: pip install strawberry-graphql"
            )
    return _strawberry


@dataclass
class GraphQLVault:
    """GraphQL Vault type."""
    id: str
    name: str
    owner_id: str
    is_shared: bool
    created_at: datetime
    claims: Optional[List["GraphQLClaim"]] = None


@dataclass
class GraphQLClaim:
    """GraphQL Claim type."""
    id: str
    vault_id: str
    content: str
    confidence: float
    source_mark: int
    created_at: datetime
    media_timestamp: Optional[List[float]] = None


@dataclass
class GraphQLUser:
    """GraphQL User type."""
    id: str
    email: str
    role: str
    display_name: Optional[str]
    created_at: datetime
    vaults: Optional[List[GraphQLVault]] = None


@dataclass
class GraphQLSearchResult:
    """GraphQL search result."""
    claims: List[GraphQLClaim]
    total: int


def create_schema():
    """Create GraphQL schema."""
    _get_strawberry()

    @strawberry.type
    class Vault:
        id: strawberry.ID
        name: str
        owner_id: str
        is_shared: bool
        created_at: datetime

        @strawberry.field
        def claims(self, limit: int = 10) -> List["Claim"]:
            # Placeholder - would query database
            return []

    @strawberry.type
    class Claim:
        id: strawberry.ID
        vault_id: str
        content: str
        confidence: float
        source_mark: int
        created_at: datetime
        media_timestamp: Optional[List[float]] = None

    @strawberry.type
    class User:
        id: strawberry.ID
        email: str
        role: str
        display_name: Optional[str]
        created_at: datetime

        @strawberry.field
        def vaults(self) -> List[Vault]:
            # Placeholder - would query database
            return []

    @strawberry.type
    class SearchResult:
        claims: List[Claim]
        total: int

    @strawberry.type
    class Query:
        @strawberry.field
        def vault(self, id: strawberry.ID) -> Optional[Vault]:
            # Placeholder - would query database
            return None

        @strawberry.field
        def vaults(
            self,
            user_id: Optional[str] = None,
            limit: int = 10,
        ) -> List[Vault]:
            # Placeholder - would query database
            return []

        @strawberry.field
        def claim(self, id: strawberry.ID) -> Optional[Claim]:
            # Placeholder - would query database
            return None

        @strawberry.field
        def claims(
            self,
            vault_id: Optional[str] = None,
            limit: int = 10,
        ) -> List[Claim]:
            # Placeholder - would query database
            return []

        @strawberry.field
        def search_claims(
            self,
            query: str,
            limit: int = 10,
        ) -> SearchResult:
            # Placeholder - would search
            return SearchResult(claims=[], total=0)

        @strawberry.field
        def user(self, id: strawberry.ID) -> Optional[User]:
            # Placeholder - would query database
            return None

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_vault(
            self,
            name: str,
            owner_id: str,
        ) -> Vault:
            # Placeholder - would create in database
            return Vault(
                id="new_id",
                name=name,
                owner_id=owner_id,
                is_shared=False,
                created_at=datetime.now(),
            )

        @strawberry.mutation
        def update_vault(
            self,
            id: strawberry.ID,
            name: Optional[str] = None,
            is_shared: Optional[bool] = None,
        ) -> Optional[Vault]:
            # Placeholder - would update in database
            return None

        @strawberry.mutation
        def delete_vault(self, id: strawberry.ID) -> bool:
            # Placeholder - would delete from database
            return True

        @strawberry.mutation
        def create_claim(
            self,
            vault_id: str,
            content: str,
            confidence: float = 1.0,
        ) -> Claim:
            # Placeholder - would create in database
            return Claim(
                id="new_id",
                vault_id=vault_id,
                content=content,
                confidence=confidence,
                source_mark=1,
                created_at=datetime.now(),
            )

    return strawberry.Schema(query=Query, mutation=Mutation)


# Schema instance (created on first import)
_schema = None


def get_schema():
    """Get the GraphQL schema instance."""
    global _schema
    if _schema is None:
        _schema = create_schema()
    return _schema


def get_graphql_router():
    """Get FastAPI router for GraphQL."""
    _get_strawberry()
    from strawberry.fastapi import GraphQLRouter

    schema = get_schema()
    return GraphQLRouter(schema)