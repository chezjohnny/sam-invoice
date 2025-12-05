import pytest
from sqlalchemy.exc import IntegrityError

from sam_invoice.models.crud_customer import customer_crud


def test_create_and_query_customer(in_memory_db):
    """Create a customer and verify it can be queried back via the CRUD API.

    This test ensures `create_customer` assigns an ID and `get_customers`
    returns the newly created entry (checked by email).
    """
    cust = customer_crud.create("Dupont", "1 rue du Vin", "dupont@example.com")
    assert cust.id is not None
    assert cust.name == "Dupont"
    customers = customer_crud.get_all()
    # ensure at least one customer with our email exists
    assert any(c.email == "dupont@example.com" for c in customers)


def test_search_customers(in_memory_db):
    """Verify `search_customers` finds customers by id, name, email and address.

    The test creates several customers then checks that an empty query
    returns all records and that partial and case-insensitive matches
    work for name, email and address. It also verifies exact id match.
    """
    # create several customers
    dupont = customer_crud.create("Dupont", "1 rue du Vin", "dupont@example.com")
    customer_crud.create("Martin", "2 avenue des Vignes", "martin@wine.com")
    customer_crud.create("Alice", "Chez Alice", "alice@domain.com")

    # empty query returns all customers sorted case-insensitively
    all_res = customer_crud.search("")
    names = [c.name for c in all_res]
    assert [n.lower() for n in names] == sorted([n.lower() for n in names])

    # search by exact id (string)
    res_id = customer_crud.search(str(dupont.id))
    assert any(r.id == dupont.id for r in res_id)

    # partial name (case-insensitive)
    res_name = customer_crud.search("mart")
    assert any("martin" in r.name.lower() for r in res_name)

    # partial email case-insensitive
    res_email = customer_crud.search("WINE")
    assert any("wine" in r.email.lower() for r in res_email)

    # partial address
    res_addr = customer_crud.search("rue du")
    assert any("rue du" in r.address.lower() for r in res_addr)


def test_get_customers_sorted(in_memory_db):
    """`get_customers` returns customers ordered by name case-insensitively."""
    # create several customers in arbitrary order
    customer_crud.create("dupont", "1 rue du Vin", "dupont@example.com")
    customer_crud.create("Martin", "2 avenue des Vignes", "martin@wine.com")
    customer_crud.create("Alice", "Chez Alice", "alice@domain.com")

    customers = customer_crud.get_all()
    names = [c.name for c in customers]
    expected = sorted(names, key=lambda s: s.lower())
    assert [n.lower() for n in names] == [n.lower() for n in expected]


def test_search_customers_sorted(in_memory_db):
    """`search_customers` returns ordered results for empty and partial queries."""
    # create several customers
    customer_crud.create("zeta", "Addr 1", "z@example.com")
    customer_crud.create("Alpha", "Addr 2", "a@example.com")
    customer_crud.create("beta", "Addr 3", "b@example.com")

    # empty search should return ordered by name
    res = customer_crud.search("")
    names = [c.name for c in res]
    assert [n.lower() for n in names] == sorted([n.lower() for n in names])

    # partial search (matches multiple) should also be ordered
    res2 = customer_crud.search("a")
    names2 = [c.name for c in res2]
    assert [n.lower() for n in names2] == sorted([n.lower() for n in names2])


def test_db_constraints_empty_name(in_memory_db):
    """Creating a customer with an empty name should violate DB constraints."""
    with pytest.raises(IntegrityError):
        customer_crud.create("", "Some address", "noone@example.com")


def test_db_constraints_empty_address(in_memory_db):
    """Creating a customer with an empty address should violate DB constraints."""
    with pytest.raises(IntegrityError):
        customer_crud.create("Nobody", "", "nobody@example.com")


def test_db_constraints_short_name(in_memory_db):
    """Creating a customer with a name shorter than 3 chars should fail."""
    with pytest.raises(IntegrityError):
        customer_crud.create("Al", "Some address", "al@example.com")


def test_db_constraints_short_address(in_memory_db):
    """Creating a customer with an address shorter than 3 chars should fail."""
    with pytest.raises(IntegrityError):
        customer_crud.create("Valid Name", "A1", "valid@example.com")
