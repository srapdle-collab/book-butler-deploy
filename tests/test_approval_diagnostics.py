from lib import approval_diagnostics


def test_fingerprint_is_stable_for_same_server_and_hides_raw_target():
    identity = ("postgres", "library", "10.22.33.44", "5432", "16384")
    first = approval_diagnostics.fingerprint_identity(identity)
    assert first == approval_diagnostics.fingerprint_identity(identity)
    assert len(first) == 16
    assert "10.22.33.44" not in first
    assert first != approval_diagnostics.fingerprint_identity(
        ("postgres", "library", "10.22.33.45", "5432", "16384"))


def test_target_status_reports_same_only_for_expected_postgres_fingerprint():
    expected = approval_diagnostics.fingerprint_identity(
        ("postgres", "library", "10.22.33.44", "5432", "16384"))
    assert approval_diagnostics.compare_target("postgres", expected, expected)["same_as_m1"] == "YES"
    assert approval_diagnostics.compare_target("postgres", "0000000000000000", expected)["same_as_m1"] == "NO"
    assert approval_diagnostics.compare_target("sqlite", "0000000000000000", expected)["same_as_m1"] == "NO"
    assert approval_diagnostics.compare_target("sqlite", None, expected)["same_as_m1"] == "NO"
    assert approval_diagnostics.compare_target("postgres", None, expected)["same_as_m1"] == "UNKNOWN"
