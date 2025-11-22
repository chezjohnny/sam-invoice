def validate_customer_fields(name: str, address: str) -> tuple[bool, str | None]:
    """Helper function for testing validation logic."""
    name = (name or "").strip()
    address = (address or "").strip()

    if not name:
        return False, "Name is required"
    if not address:
        return False, "Address is required"
    if len(name) < 3:
        return False, "Name must be at least 3 characters"
    if len(address) < 3:
        return False, "Address must be at least 3 characters"

    return True, None


def test_validate_empty_name():
    valid, msg = validate_customer_fields("", "Some address")
    assert not valid
    assert msg is not None and "Name" in msg


def test_validate_empty_address():
    valid, msg = validate_customer_fields("Bob", "")
    assert not valid
    assert msg is not None and "Address" in msg


def test_validate_ok():
    valid, msg = validate_customer_fields("Bob", "1 Wine St")
    assert valid
    assert msg is None

    # New validation tests for minimum length


def test_validate_short_name():
    valid, msg = validate_customer_fields("Al", "Some address")
    assert not valid
    assert msg is not None and "at least 3" in msg


def test_validate_short_address():
    valid, msg = validate_customer_fields("Bob", "A1")
    assert not valid
    assert msg is not None and "at least 3" in msg
