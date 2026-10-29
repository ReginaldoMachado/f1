import pytest

from f1.utils.config import Settings


def test_settings_load_defaults_and_custom_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENF1_BASE_URL", "https://example.test/v1/")
    monkeypatch.setenv("OPENF1_TIMEOUT", "15.5")
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = Settings.from_env()

    assert settings.openf1_base_url == "https://example.test/v1"
    assert settings.openf1_timeout == 15.5
    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("OPENF1_BASE_URL", "not-a-url", "absolute HTTP"),
        ("OPENF1_TIMEOUT", "fast", "must be a number"),
        ("OPENF1_TIMEOUT", "0", "greater than zero"),
        ("ENVIRONMENT", "test", "ENVIRONMENT must be one of"),
        ("LOG_LEVEL", "VERBOSE", "standard logging level"),
    ],
)
def test_settings_reject_invalid_values(
    monkeypatch,
    name: str,
    value: str,
    message: str,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match=message):
        Settings.from_env()
