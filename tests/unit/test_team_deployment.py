"""Tests for Team Deployment (Phase 5).

Tests for database models, authentication, permissions, and audit logging.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock


class TestDatabaseConfig:
    """Test database configuration."""

    def test_default_config(self):
        from saw.db.config import DatabaseConfig

        config = DatabaseConfig()
        assert config.url == "sqlite:///saw.db"
        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert not config.is_postgres

    def test_postgres_url_detection(self):
        from saw.db.config import DatabaseConfig

        config = DatabaseConfig(url="postgresql://user:pass@host:5432/db")
        assert config.is_postgres
        assert "asyncpg" in config.async_url

    def test_from_env(self, monkeypatch):
        from saw.db.config import DatabaseConfig

        monkeypatch.setenv("DATABASE_URL", "postgresql://test@localhost/db")
        monkeypatch.setenv("DB_POOL_SIZE", "10")

        config = DatabaseConfig.from_env()
        assert config.url == "postgresql://test@localhost/db"
        assert config.pool_size == 10


class TestModels:
    """Test SQLAlchemy models."""

    def test_user_model_defaults(self):
        from saw.db.models import User, generate_uuid, utcnow

        user = User(
            id=generate_uuid(),
            email="test@example.com",
            hashed_password="hashed",
            role="viewer",
            is_active=True,
            created_at=utcnow(),
        )
        assert user.role == "viewer"
        assert user.is_active is True
        assert user.created_at is not None

    def test_vault_model_defaults(self):
        from saw.db.models import Vault, generate_uuid, utcnow

        vault = Vault(
            id=generate_uuid(),
            name="Test Vault",
            owner_id="user123",
            is_shared=False,
            created_at=utcnow(),
        )
        assert vault.is_shared is False
        assert vault.created_at is not None

    def test_claim_model(self):
        from saw.db.models import Claim, generate_uuid

        claim = Claim(
            id=generate_uuid(),
            vault_id="vault123",
            content="Test claim content",
            content_hash="abc123",
            source_uuid="source123",
            confidence=1,
        )
        assert claim.confidence == 1
        assert claim.media_timestamp_start is None

    def test_claim_with_media_timestamp(self):
        from saw.db.models import Claim, generate_uuid

        claim = Claim(
            id=generate_uuid(),
            vault_id="vault123",
            content="Transcribed segment",
            content_hash="abc123",
            source_uuid="source123",
            media_timestamp_start=10.5,
            media_timestamp_end=25.0,
            media_vault_id="media123",
        )
        assert claim.media_timestamp_start == 10.5
        assert claim.media_timestamp_end == 25.0

    def test_vault_permission_model(self):
        from saw.db.models import VaultPermission, utcnow

        perm = VaultPermission(
            vault_id="vault123",
            user_id="user456",
            permission="write",
            granted_at=utcnow(),
        )
        assert perm.permission == "write"
        assert perm.granted_at is not None

    def test_audit_log_model(self):
        from saw.db.models import AuditLog, generate_uuid, utcnow

        log = AuditLog(
            id=generate_uuid(),
            user_id="user123",
            action="create",
            resource_type="vault",
            resource_id="vault456",
            timestamp=utcnow(),
        )
        assert log.action == "create"
        assert log.timestamp is not None


class TestPasswordHasher:
    """Test password hashing."""

    def test_hash_password(self):
        from saw.auth.jwt_auth import PasswordHasher

        # Skip if bcrypt not installed
        try:
            hasher = PasswordHasher()
            hashed = hasher.hash_password("test_password")
            assert hashed != "test_password"
            assert len(hashed) > 20
        except ImportError:
            pytest.skip("bcrypt not installed")

    def test_verify_password(self):
        from saw.auth.jwt_auth import PasswordHasher

        try:
            hasher = PasswordHasher()
            hashed = hasher.hash_password("test_password")
            assert hasher.verify_password("test_password", hashed)
            assert not hasher.verify_password("wrong_password", hashed)
        except ImportError:
            pytest.skip("bcrypt not installed")


class TestJWTHandler:
    """Test JWT handling."""

    def test_create_access_token(self):
        from saw.auth.jwt_auth import JWTHandler, AuthConfig

        config = AuthConfig(secret_key="test_secret_key")
        handler = JWTHandler(config)

        token = handler.create_access_token("user123", "editor")
        assert token is not None
        assert len(token) > 50

    def test_create_token_pair(self):
        from saw.auth.jwt_auth import JWTHandler, AuthConfig

        config = AuthConfig(secret_key="test_secret_key")
        handler = JWTHandler(config)

        pair = handler.create_token_pair("user123", "viewer")
        assert pair.access_token is not None
        assert pair.refresh_token is not None
        assert pair.token_type == "bearer"
        assert pair.expires_in > 0

    def test_decode_token(self):
        from saw.auth.jwt_auth import JWTHandler, AuthConfig

        config = AuthConfig(secret_key="test_secret_key")
        handler = JWTHandler(config)

        token = handler.create_access_token("user123", "admin")
        payload = handler.decode_token(token)

        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_verify_access_token(self):
        from saw.auth.jwt_auth import JWTHandler, AuthConfig

        config = AuthConfig(secret_key="test_secret_key")
        handler = JWTHandler(config)

        token = handler.create_access_token("user123", "editor")
        data = handler.verify_access_token(token)

        assert data.sub == "user123"
        assert data.role == "editor"

    def test_expired_token(self):
        from saw.auth.jwt_auth import JWTHandler, AuthConfig
        from datetime import timedelta

        config = AuthConfig(secret_key="test_secret_key")
        handler = JWTHandler(config)

        # Create token that expired in the past
        token = handler.create_access_token(
            "user123",
            expires_delta=timedelta(seconds=-1)
        )

        with pytest.raises(ValueError, match="expired"):
            handler.verify_access_token(token)

    def test_invalid_token(self):
        from saw.auth.jwt_auth import JWTHandler, AuthConfig

        config = AuthConfig(secret_key="test_secret_key")
        handler = JWTHandler(config)

        with pytest.raises(ValueError):
            handler.decode_token("invalid_token")


class TestAuthService:
    """Test authentication service."""

    def test_register_user(self):
        from saw.auth.jwt_auth import AuthService, AuthConfig

        config = AuthConfig(secret_key="test_key")
        service = AuthService(config)

        # Mock hasher to avoid bcrypt dependency
        service.hasher = Mock()
        service.hasher.hash_password = Mock(return_value="hashed_password")

        user_data = service.register_user(
            email="test@example.com",
            password="password123",
            role="editor",
            display_name="Test User",
        )

        assert user_data["email"] == "test@example.com"
        assert user_data["hashed_password"] == "hashed_password"
        assert user_data["role"] == "editor"
        assert user_data["is_active"] is True


class TestPermissions:
    """Test permission system."""

    def test_permission_enum(self):
        from saw.auth.permissions import Permission

        assert Permission.READ.value == 1
        assert Permission.WRITE.value == 2
        assert Permission.ADMIN.value == 3

    def test_role_enum(self):
        from saw.auth.permissions import Role

        assert Role.VIEWER.value == 1
        assert Role.EDITOR.value == 2
        assert Role.ADMIN.value == 3

    def test_role_permissions(self):
        from saw.auth.permissions import get_role_permissions, Permission

        admin_perms = get_role_permissions("admin")
        assert Permission.READ in admin_perms
        assert Permission.WRITE in admin_perms
        assert Permission.ADMIN in admin_perms

        viewer_perms = get_role_permissions("viewer")
        assert Permission.READ in viewer_perms
        assert Permission.WRITE not in viewer_perms

    def test_has_permission(self):
        from saw.auth.permissions import has_permission, Permission

        assert has_permission("admin", Permission.ADMIN)
        assert has_permission("editor", Permission.WRITE)
        assert not has_permission("viewer", Permission.WRITE)

    def test_permission_service_vault_access(self):
        from saw.auth.permissions import PermissionService, Permission

        service = PermissionService()

        # Mock user and vault
        user = Mock(id="user123", role="viewer", is_active=True)
        vault = Mock(id="vault456", owner_id="user123", is_shared=False)

        # Owner check
        result = service.check_vault_access(user, vault, Permission.READ)
        assert result.allowed
        assert result.reason == "owner"

        # Different user, private vault
        user2 = Mock(id="user789", role="viewer", is_active=True)
        result = service.check_vault_access(user2, vault, Permission.READ)
        assert not result.allowed

    def test_permission_service_shared_vault(self):
        from saw.auth.permissions import PermissionService, Permission

        service = PermissionService()

        # Mock shared vault
        vault = Mock(id="vault456", owner_id="owner123", is_shared=True)
        editor = Mock(id="editor456", role="editor", is_active=True)

        result = service.check_vault_access(editor, vault, Permission.READ)
        assert result.allowed
        assert result.reason == "role_permission"

    def test_can_create_vault(self):
        from saw.auth.permissions import PermissionService

        service = PermissionService()

        editor = Mock(role="editor", is_active=True)
        viewer = Mock(role="viewer", is_active=True)

        assert service.can_create_vault(editor)
        assert not service.can_create_vault(viewer)


class TestAuditService:
    """Test audit logging."""

    def test_audit_entry_creation(self):
        from saw.audit.service import AuditService, AuditAction, ResourceType

        service = AuditService()

        entry = service.create_entry(
            action=AuditAction.CREATE,
            resource_type=ResourceType.VAULT,
            resource_id="vault123",
            user_id="user456",
        )

        assert entry.action == "create"
        assert entry.resource_type == "vault"
        assert entry.resource_id == "vault123"
        assert entry.user_id == "user456"

    def test_audit_entry_to_model(self):
        from saw.audit.service import AuditEntry, AuditAction, ResourceType

        entry = AuditEntry(
            action=AuditAction.CREATE,
            resource_type=ResourceType.VAULT,
            resource_id="vault123",
            user_id="user456",
            details={"name": "Test Vault"},
        )

        model = entry.to_model()
        assert model.action == "create"
        assert model.resource_type == "vault"
        assert model.details is not None

    def test_audit_action_types(self):
        from saw.audit.service import AuditAction

        assert AuditAction.CREATE == "create"
        assert AuditAction.READ == "read"
        assert AuditAction.DELETE == "delete"
        assert AuditAction.LOGIN == "login"

    def test_resource_types(self):
        from saw.audit.service import ResourceType

        assert ResourceType.USER == "user"
        assert ResourceType.VAULT == "vault"
        assert ResourceType.CLAIM == "claim"


class TestHealthEndpoints:
    """Test health check functions."""

    @pytest.mark.skip(reason="Requires FastAPI")
    def test_health_check(self):
        pass

    @pytest.mark.skip(reason="Requires FastAPI")
    def test_liveness_check(self):
        pass

    @pytest.mark.skip(reason="Requires FastAPI and database")
    def test_check_database_sqlite(self):
        pass


class TestTokenData:
    """Test token data structures."""

    def test_token_data_creation(self):
        from saw.auth.jwt_auth import TokenData

        now = datetime.now(timezone.utc)
        data = TokenData(
            sub="user123",
            exp=now,
            iat=now,
            role="editor",
        )

        assert data.sub == "user123"
        assert data.role == "editor"

    def test_token_data_to_dict(self):
        from saw.auth.jwt_auth import TokenData

        now = datetime.now(timezone.utc)
        data = TokenData(
            sub="user123",
            exp=now,
            iat=now,
            role="admin",
        )

        d = data.to_dict()
        assert d["sub"] == "user123"
        assert d["role"] == "admin"
        assert "exp" in d
        assert "iat" in d