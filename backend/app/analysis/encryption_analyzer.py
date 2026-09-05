"""Encryption analysis: reports *observable* encryption characteristics only.

The system never decrypts traffic, never intercepts TLS and never bypasses
certificate validation. We only report whether encryption is observable from
protocol/flow metadata.
"""

ENC_LABEL_DETECTED = "Encryption detected"
ENC_LABEL_NOT_DETECTED = "Encryption not detected"
ENC_LABEL_UNKNOWN = "Standard/Unknown"

# Protocols that are commonly plaintext on standard ports; used only to report
# "Encryption not detected" from observable metadata.
_PLAINTEXT_PROTOCOLS = {"TCP", "UDP", "ICMP", "HTTP", "DNS", "FTP", "TELNET", "SMTP", "POP3", "IMAP", "SSH"}


def encryption_label(encrypted: bool, protocol: str = "") -> str:
    if encrypted:
        return ENC_LABEL_DETECTED
    if protocol and protocol.upper() in _PLAINTEXT_PROTOCOLS:
        return ENC_LABEL_NOT_DETECTED
    return ENC_LABEL_UNKNOWN


def short_encryption_label(encrypted: bool) -> str:
    return "Encrypted" if encrypted else "Unencrypted"


def is_plaintext_service(service: str, protocol: str, port: int) -> bool:
    """Heuristic used only to decide alert severity, never as an attack claim."""
    if service in ("HTTP", "DNS", "FTP", "Telnet", "SMTP", "POP3", "IMAP"):
        return True
    return False