"""Privacy score engine tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.analysis.privacy_score import compute_privacy_score  # noqa: E402


class TestPrivacyScore:
    def test_fully_encrypted(self):
        result = compute_privacy_score(
            total_connections=100,
            encrypted_connections=100,
            unencrypted_bytes=0,
            total_bytes=10_000_000,
        )
        assert result["score"] == 100
        assert result["encrypted_percentage"] == 100.0
        assert any("encryption" in r for r in result["reasons"])

    def test_fully_unencrypted(self):
        result = compute_privacy_score(
            total_connections=100,
            encrypted_connections=0,
            unencrypted_bytes=10_000_000,
            total_bytes=10_000_000,
        )
        assert result["score"] == 0
        assert result["encrypted_percentage"] == 0.0
        assert result["unencrypted_percentage"] == 100.0

    def test_mixed_traffic(self):
        result = compute_privacy_score(
            total_connections=100,
            encrypted_connections=80,
            unencrypted_bytes=2_000_000,
            total_bytes=10_000_000,
        )
        assert 0 < result["score"] < 100
        assert result["encrypted_percentage"] == 80.0

    def test_empty_network_gets_neutral_score(self):
        result = compute_privacy_score(
            total_connections=0,
            encrypted_connections=0,
            unencrypted_bytes=0,
            total_bytes=0,
        )
        assert result["score"] == 100

    def test_score_within_bounds(self):
        for i in range(101):
            result = compute_privacy_score(
                total_connections=100,
                encrypted_connections=i,
                unencrypted_bytes=(100 - i) * 1000,
                total_bytes=100_000,
            )
            assert 0 <= result["score"] <= 100