import pytest
from sqlalchemy.exc import IntegrityError

import sam_invoice.models.crud_customer as crud
import sam_invoice.models.crud_product as crud_product

# === Tests CRUD Customer ===


def test_create_and_query_customer(in_memory_db):
    """Create a customer and verify it can be queried back via the CRUD API.

    This test ensures `create_customer` assigns an ID and `get_customers`
    returns the newly created entry (checked by email).
    """
    cust = crud.create_customer("Dupont", "1 rue du Vin", "dupont@example.com")
    assert cust.id is not None
    assert cust.name == "Dupont"
    customers = crud.get_customers()
    # ensure at least one customer with our email exists
    assert any(c.email == "dupont@example.com" for c in customers)


def test_search_customers(in_memory_db):
    """Verify `search_customers` finds customers by id, name, email and address.

    The test creates several customers then checks that an empty query
    returns all records and that partial and case-insensitive matches
    work for name, email and address. It also verifies exact id match.
    """
    # create several customers
    dupont = crud.create_customer("Dupont", "1 rue du Vin", "dupont@example.com")
    crud.create_customer("Martin", "2 avenue des Vignes", "martin@wine.com")
    crud.create_customer("Alice", "Chez Alice", "alice@domain.com")

    # empty query returns all customers sorted case-insensitively
    all_res = crud.search_customers("")
    names = [c.name for c in all_res]
    assert [n.lower() for n in names] == sorted([n.lower() for n in names])

    # search by exact id (string)
    res_id = crud.search_customers(str(dupont.id))
    assert any(r.id == dupont.id for r in res_id)

    # partial name (case-insensitive)
    res_name = crud.search_customers("mart")
    assert any("martin" in r.name.lower() for r in res_name)

    # partial email case-insensitive
    res_email = crud.search_customers("WINE")
    assert any("wine" in r.email.lower() for r in res_email)

    # partial address
    res_addr = crud.search_customers("rue du")
    assert any("rue du" in r.address.lower() for r in res_addr)


def test_get_customers_sorted(in_memory_db):
    """`get_customers` returns customers ordered by name case-insensitively."""
    # create several customers in arbitrary order
    crud.create_customer("dupont", "1 rue du Vin", "dupont@example.com")
    crud.create_customer("Martin", "2 avenue des Vignes", "martin@wine.com")
    crud.create_customer("Alice", "Chez Alice", "alice@domain.com")

    customers = crud.get_customers()
    names = [c.name for c in customers]
    expected = sorted(names, key=lambda s: s.lower())
    assert [n.lower() for n in names] == [n.lower() for n in expected]


def test_search_customers_sorted(in_memory_db):
    """`search_customers` returns ordered results for empty and partial queries."""
    # create several customers
    crud.create_customer("zeta", "Addr 1", "z@example.com")
    crud.create_customer("Alpha", "Addr 2", "a@example.com")
    crud.create_customer("beta", "Addr 3", "b@example.com")

    # empty search should return ordered by name
    res = crud.search_customers("")
    names = [c.name for c in res]
    assert [n.lower() for n in names] == sorted([n.lower() for n in names])

    # partial search (matches multiple) should also be ordered
    res2 = crud.search_customers("a")
    names2 = [c.name for c in res2]
    assert [n.lower() for n in names2] == sorted([n.lower() for n in names2])


def test_db_constraints_empty_name(in_memory_db):
    """Creating a customer with an empty name should violate DB constraints."""
    with pytest.raises(IntegrityError):
        crud.create_customer("", "Some address", "noone@example.com")


def test_db_constraints_empty_address(in_memory_db):
    """Creating a customer with an empty address should violate DB constraints."""
    with pytest.raises(IntegrityError):
        crud.create_customer("Nobody", "", "nobody@example.com")


def test_db_constraints_short_name(in_memory_db):
    """Creating a customer with a name shorter than 3 chars should fail."""
    with pytest.raises(IntegrityError):
        crud.create_customer("Al", "Some address", "al@example.com")


def test_db_constraints_short_address(in_memory_db):
    """Creating a customer with an address shorter than 3 chars should fail."""
    with pytest.raises(IntegrityError):
        crud.create_customer("Valid Name", "A1", "valid@example.com")


# === Tests CRUD Article ===


def test_create_and_query_article(in_memory_db):
    """Create an article and verify it can be queried back via the CRUD API."""
    art = crud_product.create_product("ART-001", "Test Article", price=25.50, stock=10, sold=5)
    assert art.id is not None
    assert art.reference == "ART-001"
    assert art.name == "Test Article"
    assert art.price == 25.50
    assert art.stock == 10
    assert art.sold == 5

    articles = crud_product.get_products()
    assert any(a.reference == "ART-001" for a in articles)


def test_search_products(in_memory_db):
    """Verify `search_products` finds articles by id, ref and description."""
    # Create several articles
    art1 = crud_product.create_product("VIN-001", "Château Margaux 2015", price=450.0, stock=24)
    crud_product.create_product("VIN-002", "Château Latour 2010", price=650.0, stock=18)
    crud_product.create_product("WINE-003", "Burgundy Special", price=85.0, stock=48)

    # Empty query returns all articles
    all_res = crud_product.search_products("")
    assert len(all_res) >= 3

    # Search by exact id (string)
    res_id = crud_product.search_products(str(art1.id))
    assert any(r.id == art1.id for r in res_id)

    # Partial ref (case-insensitive)
    res_ref = crud_product.search_products("vin")
    assert len(res_ref) >= 2
    assert any("vin" in r.reference.lower() for r in res_ref)

    # Partial description
    res_desc = crud_product.search_products("château")
    assert len(res_desc) >= 2
    assert any("château" in r.name.lower() for r in res_desc)


def test_get_products_sorted(in_memory_db):
    """`get_products` returns articles ordered by ref case-insensitively."""
    crud_product.create_product("Z-001", "Zinfandel", price=30.0)
    crud_product.create_product("a-002", "Alsace", price=25.0)
    crud_product.create_product("M-003", "Margaux", price=450.0)

    articles = crud_product.get_products()
    refs = [a.reference for a in articles]
    expected = sorted(refs, key=lambda s: s.lower())
    assert [r.lower() for r in refs] == [r.lower() for r in expected]


def test_search_products_sorted(in_memory_db):
    """`search_products` returns ordered results for empty and partial queries."""
    crud_product.create_product("Z-001", "Zinfandel", price=30.0)
    crud_product.create_product("A-002", "Alsace", price=25.0)
    crud_product.create_product("B-003", "Bordeaux", price=80.0)

    # Empty search should return ordered by ref
    res = crud_product.search_products("")
    refs = [a.reference for a in res]
    assert [r.lower() for r in refs] == sorted([r.lower() for r in refs])

    # Partial search should also be ordered
    res2 = crud_product.search_products("a")
    refs2 = [a.reference for a in res2]
    assert [r.lower() for r in refs2] == sorted([r.lower() for r in refs2])


def test_update_product(in_memory_db):
    """Verify updating an article modifies its fields correctly."""
    art = crud_product.create_product("TEST-001", "Original", price=10.0, stock=5, sold=2)
    assert art.name == "Original"

    updated = crud_product.update_product(art.id, name="Updated Description", price=15.0, stock=10)
    assert updated.name == "Updated Description"
    assert updated.price == 15.0
    assert updated.stock == 10
    assert updated.sold == 2  # Not updated


def test_delete_product(in_memory_db):
    """Verify deleting an article removes it from the database."""
    art = crud_product.create_product("DEL-001", "To Delete", price=20.0)
    art_id = art.id

    # Verify it exists
    found = crud_product.get_product_by_id(art_id)
    assert found is not None

    # Delete it
    crud_product.delete_product(art_id)

    # Verify it's gone
    found_after = crud_product.get_product_by_id(art_id)
    assert found_after is None
