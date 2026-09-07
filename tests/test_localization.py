import ai_usage
from ai_usage.domain.localization import _ENGLISH, _POLISH, L10nKey, Localizer
from ai_usage.domain.models import AppLanguage


def test_every_key_has_an_english_and_polish_string():
    missing_en = [k.name for k in L10nKey if k not in _ENGLISH]
    missing_pl = [k.name for k in L10nKey if k not in _POLISH]
    assert not missing_en, f"missing English: {missing_en}"
    assert not missing_pl, f"missing Polish: {missing_pl}"


def test_localizer_returns_requested_language():
    assert Localizer(AppLanguage.POLISH).text(L10nKey.NO_USAGE_DATA) == _POLISH[L10nKey.NO_USAGE_DATA]
    assert Localizer(AppLanguage.ENGLISH_US).text(L10nKey.NO_USAGE_DATA) == _ENGLISH[L10nKey.NO_USAGE_DATA]


def test_package_version_matches_setup():
    import pathlib
    import re

    setup_py = (pathlib.Path(__file__).parent.parent / "setup.py").read_text()
    setup_version = re.search(r'version="([^"]+)"', setup_py).group(1)
    assert ai_usage.__version__ == setup_version
