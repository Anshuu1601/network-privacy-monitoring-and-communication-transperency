"""Privacy score engine.

A transparent, application-defined score from 0-100 based on observable
metadata. It is NOT an industry-standard security measurement.

Factors (weights configurable via settings.SCORE_WEIGHTS):
  * encryption   — share of encrypted connections/traffic
  * protocol     — share of communication over secure protocols
  * unencrypted_penalty — penalty for plaintext traffic volume
"""
from app.config import settings


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def compute_privacy_score(*, total_connections: int,
                          encrypted_connections: int,
                          unencrypted_bytes: int,
                          total_bytes: int,
                          secure_protocol_connections: int = None) -> dict:
    """Compute the privacy score and human-readable reasons.

    All parameters derive from flow metadata only.
    """
    weights = settings.SCORE_WEIGHTS
    w_enc = weights.get("encryption", 60)
    w_proto = weights.get("protocol", 20)
    w_penalty = weights.get("unencrypted_penalty", 20)

    reasons = []
    scores = {}
    explanations = {}

    # --- Encryption component ---
    if total_connections:
        enc_pct = encrypted_connections / total_connections * 100.0
    else:
        enc_pct = 100.0
    enc_component = enc_pct
    scores["encryption"] = enc_component
    if enc_pct >= 90:
        reasons.append("+ Strong encryption usage")
        explanations["encryption"] = f"{enc_pct:.0f}% of connections use encryption"
    elif enc_pct >= 50:
        reasons.append("+ Most connections use encryption")
        explanations["encryption"] = f"{enc_pct:.0f}% of connections use encryption"
    else:
        reasons.append("- Encryption usage is low")
        explanations["encryption"] = f"{enc_pct:.0f}% of connections use encryption"

    # --- Protocol component ---
    if secure_protocol_connections is None:
        secure_protocol_connections = encrypted_connections
    if total_connections:
        proto_pct = secure_protocol_connections / total_connections * 100.0
    else:
        proto_pct = 100.0
    scores["protocol"] = proto_pct
    if proto_pct >= 80:
        reasons.append("+ Majority of connections use secure protocols")
        explanations["protocol"] = f"{proto_pct:.0f}% of connections use secure protocols"
    else:
        reasons.append("- Several connections use standard/unverified protocols")
        explanations["protocol"] = f"{proto_pct:.0f}% of connections use secure protocols"

    # --- Unencrypted traffic penalty ---
    if total_bytes:
        unenc_pct = unencrypted_bytes / total_bytes * 100.0
    else:
        unenc_pct = 0.0
    scores["unencrypted_penalty"] = 100.0 - unenc_pct
    if unenc_pct > 10:
        reasons.append(f"- {unenc_pct:.0f}% of traffic is unencrypted")
        explanations["unencrypted_penalty"] = f"{unenc_pct:.0f}% of traffic is unencrypted"
    elif unenc_pct > 0:
        reasons.append("- Some unencrypted communication observed")
        explanations["unencrypted_penalty"] = f"{unenc_pct:.0f}% of traffic is unencrypted"
    else:
        reasons.append("+ All observed traffic is encrypted")
        explanations["unencrypted_penalty"] = "No unencrypted traffic observed"

    weighted = (
        scores["encryption"] * w_enc
        + scores["protocol"] * w_proto
        + scores["unencrypted_penalty"] * w_penalty
    ) / max(w_enc + w_proto + w_penalty, 1.0)

    score = round(_clamp(weighted))

    return {
        "score": score,
        "encrypted_percentage": round(enc_pct, 1),
        "unencrypted_percentage": round(100.0 - enc_pct, 1),
        "reasons": reasons,
        "explanations": explanations,
        "weights": {k: v for k, v in weights.items()},
    }


def score_label(score: int) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Fair"
    return "Needs attention"