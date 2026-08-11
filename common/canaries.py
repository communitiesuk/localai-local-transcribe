import secrets


def generate_marker_hash() -> str:
    """Generate the canary marker used to distinguish real boundaries from injected ones."""
    return secrets.token_hex(4)


def wrap_with_canary(label: str, content: str, marker_hash: str | None = None) -> str:
    if marker_hash is None:
        marker_hash = generate_marker_hash()
    return f"BEGIN {label} {marker_hash}\n{content}\nEND {label} {marker_hash}"
