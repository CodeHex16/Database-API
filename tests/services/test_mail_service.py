import pytest
from app.service.email_service import EmailService
from fastapi_mail import FastMail
from unittest.mock import AsyncMock, patch

@pytest.fixture
def valid_env(monkeypatch):
    monkeypatch.setenv("MAIL_ADDRESS", "test@example.com")
    monkeypatch.setenv("MAIL_PASSWORD", "password")
    monkeypatch.setenv("MAIL_USERNAME", "Tester")
    monkeypatch.setenv("MAIL_PORT", "587")
    monkeypatch.setenv("MAIL_SERVER", "smtp.example.com")
    monkeypatch.setenv("MAIL_STARTTLS", "true")
    monkeypatch.setenv("MAIL_USE_CREDENTIALS", "true")
    monkeypatch.setenv("USE_CREDENTIALS", "true")
    monkeypatch.setenv("VALIDATE_CERTS", "true")

@pytest.mark.asyncio
async def test__unit_test__send_email_calls_fastmail_send(valid_env):
    service = EmailService()

    # Patch FastMail.send_message
    with patch.object(FastMail, "send_message", new_callable=AsyncMock) as mock_send:
        await service.send_email(["recipient@example.com"], "Test Subject", "Hello!")
        mock_send.assert_awaited_once()

@pytest.mark.asyncio
async def test__unit_test__send_email_raises_when_config_invalid():
    service = EmailService()
    
    service.conf.MAIL_USERNAME = None

    with pytest.raises(ValueError, match="Email configuration is not valid"):
        await service.send_email(["recipient@example.com"], "Subject", "Body")

def test__unit_test__is_configuration_valid_returns_false_when_missing_value(valid_env):
    service = EmailService()
    service.conf.MAIL_PASSWORD = None
    assert not service.is_configuration_valid()
