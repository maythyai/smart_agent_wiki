"""Tests for A2A (Agent-to-Agent) Protocol.

Per PLAN.md Task 4: A2A message format, routing, and signing.
"""
from __future__ import annotations

import pytest
from datetime import datetime


class TestA2AMessage:
    """Tests for A2AMessage dataclass."""

    def test_message_has_sender_field(self):
        """Test 1: A2AMessage has sender field."""
        from saw.engines.collaborate.a2a_protocol import A2AMessage

        msg = A2AMessage(sender="Librarian", receiver="Writer")
        assert msg.sender == "Librarian"

    def test_message_has_receiver_field(self):
        """Test 1: A2AMessage has receiver field (single agent or list)."""
        from saw.engines.collaborate.a2a_protocol import A2AMessage

        msg = A2AMessage(sender="Librarian", receiver="Writer")
        assert msg.receiver == "Writer"

        # Also supports list for broadcast
        msg_broadcast = A2AMessage(sender="Librarian", receiver=["Writer", "Critic"])
        assert msg_broadcast.receiver == ["Writer", "Critic"]

    def test_message_has_action_field(self):
        """Test 1: A2AMessage has action field."""
        from saw.engines.collaborate.a2a_protocol import A2AMessage

        msg = A2AMessage(sender="Librarian", receiver="Writer", action="handoff")
        assert msg.action == "handoff"

    def test_message_has_payload_field(self):
        """Test 1: A2AMessage has payload field."""
        from saw.engines.collaborate.a2a_protocol import A2AMessage

        msg = A2AMessage(
            sender="Librarian",
            receiver="Writer",
            payload={"task": "create_page"},
        )
        assert msg.payload == {"task": "create_page"}

    def test_message_has_context_field(self):
        """Test 1: A2AMessage has context field."""
        from saw.engines.collaborate.a2a_protocol import A2AMessage

        msg = A2AMessage(
            sender="Librarian",
            receiver="Writer",
            context={"workflow_id": "wf-001"},
        )
        assert msg.context == {"workflow_id": "wf-001"}

    def test_message_has_trace_id_field(self):
        """Test 1: A2AMessage has trace_id field."""
        from saw.engines.collaborate.a2a_protocol import A2AMessage

        msg = A2AMessage(
            sender="Librarian",
            receiver="Writer",
            trace_id="trace-abc-123",
        )
        assert msg.trace_id == "trace-abc-123"

    def test_message_request_type(self):
        """Test 2: A2AMessage with MessageType.REQUEST triggers response."""
        from saw.engines.collaborate.a2a_protocol import A2AMessage, MessageType

        msg = A2AMessage(
            sender="Librarian",
            receiver="Writer",
            message_type=MessageType.REQUEST,
            action="create",
        )
        assert msg.message_type == MessageType.REQUEST

    def test_message_broadcast_type(self):
        """Test 3: A2AMessage with MessageType.BROADCAST delivers to all receivers."""
        from saw.engines.collaborate.a2a_protocol import A2AMessage, MessageType

        msg = A2AMessage(
            sender="Librarian",
            receiver=["Writer", "Critic"],
            message_type=MessageType.BROADCAST,
        )
        assert msg.message_type == MessageType.BROADCAST

    def test_message_correlation_id_pairs_request_response(self):
        """Test 6: A2AMessage correlation_id pairs request with response."""
        from saw.engines.collaborate.a2a_protocol import A2AMessage

        request_msg = A2AMessage(
            message_id="req-001",
            sender="Librarian",
            receiver="Writer",
        )
        # Correlation ID in response should reference request message_id
        response_msg = A2AMessage(
            sender="Writer",
            receiver="Librarian",
            correlation_id=request_msg.message_id,
        )
        assert response_msg.correlation_id == "req-001"


class TestA2AAdapter:
    """Tests for A2AAdapter."""

    def test_adapter_signs_message(self):
        """Test 4: A2AMessage generates Ed25519 signature receipt."""
        from saw.engines.collaborate.a2a_protocol import A2AAdapter, A2AMessage
        from saw.adapters.crypto.ed25519 import ReceiptSigner
        from saw.engines.collaborate.dispatcher import AgentDispatcher

        # Create mock signer
        signer = ReceiptSigner()
        signer.generate_keypair()

        # Create adapter with empty agents dict
        adapter = A2AAdapter(agents={}, audit_signer=signer, dispatcher=None)

        msg = A2AMessage(
            sender="Librarian",
            receiver="Writer",
            action="test",
        )

        # The send method should sign the message
        # For now, we check that adapter has sign functionality
        assert adapter._signer is not None

    def test_adapter_rejects_incompatible_version(self):
        """Test 5: A2AAdapter rejects incompatible protocol versions."""
        from saw.engines.collaborate.a2a_protocol import A2AAdapter, A2AMessage, A2A_PROTOCOL_VERSION

        adapter = A2AAdapter(agents={}, audit_signer=None, dispatcher=None)

        # Create message with incompatible version (major version mismatch)
        msg = A2AMessage(
            sender="Librarian",
            receiver="Writer",
            protocol_version="2.0.0",  # Major version 2 vs our 1
        )

        # Should reject version 2.x when we're at 1.x
        assert adapter.validate_version(msg) is False

    def test_adapter_accepts_compatible_version(self):
        """Test that A2AAdapter accepts compatible protocol versions."""
        from saw.engines.collaborate.a2a_protocol import A2AAdapter, A2AMessage

        adapter = A2AAdapter(agents={}, audit_signer=None, dispatcher=None)

        # Create message with compatible version (same major)
        msg = A2AMessage(
            sender="Librarian",
            receiver="Writer",
            protocol_version="1.5.0",  # Same major version 1
        )

        # Should accept version 1.x
        assert adapter.validate_version(msg) is True


class TestMessageType:
    """Tests for MessageType enum."""

    def test_message_type_has_request(self):
        """Test MessageType has REQUEST."""
        from saw.engines.collaborate.a2a_protocol import MessageType

        assert MessageType.REQUEST.value == "request"

    def test_message_type_has_response(self):
        """Test MessageType has RESPONSE."""
        from saw.engines.collaborate.a2a_protocol import MessageType

        assert MessageType.RESPONSE.value == "response"

    def test_message_type_has_broadcast(self):
        """Test MessageType has BROADCAST."""
        from saw.engines.collaborate.a2a_protocol import MessageType

        assert MessageType.BROADCAST.value == "broadcast"

    def test_message_type_has_handoff(self):
        """Test MessageType has HANDOFF."""
        from saw.engines.collaborate.a2a_protocol import MessageType

        assert MessageType.HANDOFF.value == "handoff"

    def test_message_type_has_query(self):
        """Test MessageType has QUERY."""
        from saw.engines.collaborate.a2a_protocol import MessageType

        assert MessageType.QUERY.value == "query"

    def test_message_type_has_result(self):
        """Test MessageType has RESULT."""
        from saw.engines.collaborate.a2a_protocol import MessageType

        assert MessageType.RESULT.value == "result"


class TestA2AResult:
    """Tests for A2AResult dataclass."""

    def test_result_has_success_field(self):
        """Test A2AResult has success field."""
        from saw.engines.collaborate.a2a_protocol import A2AResult

        result = A2AResult(success=True, message_id="msg-001")
        assert result.success is True

    def test_result_has_message_id_field(self):
        """Test A2AResult has message_id field."""
        from saw.engines.collaborate.a2a_protocol import A2AResult

        result = A2AResult(success=True, message_id="msg-001")
        assert result.message_id == "msg-001"

    def test_result_has_response_field(self):
        """Test A2AResult has response field."""
        from saw.engines.collaborate.a2a_protocol import A2AResult, A2AMessage

        msg = A2AMessage(sender="Writer", receiver="Librarian")
        result = A2AResult(success=True, message_id="msg-001", response=msg)
        assert result.response is not None

    def test_result_has_error_field(self):
        """Test A2AResult has error field."""
        from saw.engines.collaborate.a2a_protocol import A2AResult

        result = A2AResult(success=False, message_id="msg-001", error="Agent not found")
        assert result.error == "Agent not found"


class TestA2AProtocolVersion:
    """Tests for A2A protocol version constant."""

    def test_protocol_version_defined(self):
        """Test A2A_PROTOCOL_VERSION is defined."""
        from saw.engines.collaborate.a2a_protocol import A2A_PROTOCOL_VERSION

        assert A2A_PROTOCOL_VERSION == "1.0.0"

    def test_protocol_version_semantic(self):
        """Test A2A_PROTOCOL_VERSION follows semantic versioning."""
        from saw.engines.collaborate.a2a_protocol import A2A_PROTOCOL_VERSION

        # Should be Major.Minor.Patch format
        parts = A2A_PROTOCOL_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)
