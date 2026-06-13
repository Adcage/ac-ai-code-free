from app.grpc_client import channel


def test_internal_metadata_is_empty_without_secret(monkeypatch):
    monkeypatch.setattr(channel.settings, "agent_internal_secret", "")

    assert channel.get_internal_metadata() is None


def test_internal_metadata_uses_expected_header(monkeypatch):
    monkeypatch.setattr(channel.settings, "agent_internal_secret", "secret-value")

    assert channel.get_internal_metadata() == (("x-internal-secret", "secret-value"),)
