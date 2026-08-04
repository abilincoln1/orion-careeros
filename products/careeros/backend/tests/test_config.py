from app.core.config import Settings, get_settings


def test_settings_are_cached():
    assert get_settings() is get_settings()


def test_settings_defaults_are_overridable(monkeypatch):
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("ENVIRONMENT", "production")
    s = Settings()
    assert s.APP_NAME == "Test App"
    assert s.is_production is True
