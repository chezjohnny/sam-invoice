from sam_invoice.models.crud_product import product_crud


def test_create_and_query_product(in_memory_db):
    """Create a product and verify it can be queried back via the CRUD API."""
    prod = product_crud.create("ART-001", "Test Product", price=25.50, stock=10, sold=5)
    assert prod.reference == "ART-001"
    assert prod.name == "Test Product"
    assert prod.price == 25.50
    assert prod.stock == 10
    assert prod.sold == 5

    products = product_crud.get_all()
    assert any(p.reference == "ART-001" for p in products)


def test_search_products(in_memory_db):
    """Verify `search_products` finds products by id, ref and description."""
    # Create several products
    prod1 = product_crud.create("VIN-001", "Château Margaux 2015", price=450.0, stock=24)
    product_crud.create("VIN-002", "Château Latour 2010", price=650.0, stock=18)
    product_crud.create("WINE-003", "Burgundy Special", price=85.0, stock=48)

    # Empty query returns all products
    all_res = product_crud.search("")
    assert len(all_res) >= 3

    # Search by exact id (string)
    # Search by exact reference
    res_ref = product_crud.search(prod1.reference)
    assert any(r.reference == prod1.reference for r in res_ref)

    # Partial ref (case-insensitive)
    res_ref = product_crud.search("vin")
    assert len(res_ref) >= 2
    assert any("vin" in r.reference.lower() for r in res_ref)

    # Partial description
    res_desc = product_crud.search("château")
    assert len(res_desc) >= 2
    assert any("château" in r.name.lower() for r in res_desc)


def test_get_products_sorted(in_memory_db):
    """`get_products` returns products ordered by ref case-insensitively."""
    product_crud.create("Z-001", "Zinfandel", price=30.0)
    product_crud.create("a-002", "Alsace", price=25.0)
    product_crud.create("M-003", "Margaux", price=450.0)

    products = product_crud.get_all()
    refs = [p.reference for p in products]
    expected = sorted(refs, key=lambda s: s.lower())
    assert [r.lower() for r in refs] == [r.lower() for r in expected]


def test_search_products_sorted(in_memory_db):
    """`search_products` returns ordered results for empty and partial queries."""
    product_crud.create("Z-001", "Zinfandel", price=30.0)
    product_crud.create("A-002", "Alsace", price=25.0)
    product_crud.create("B-003", "Bordeaux", price=80.0)

    # Empty search should return ordered by ref
    res = product_crud.search("")
    refs = [a.reference for a in res]
    assert [r.lower() for r in refs] == sorted([r.lower() for r in refs])

    # Partial search should also be ordered
    res2 = product_crud.search("a")
    refs2 = [a.reference for a in res2]
    assert [r.lower() for r in refs2] == sorted([r.lower() for r in refs2])


def test_update_product(in_memory_db):
    """Verify updating a product modifies its fields correctly."""
    art = product_crud.create("TEST-001", "Original", price=10.0, stock=5, sold=2)
    assert art.name == "Original"

    updated = product_crud.update(art.reference, name="Updated Description", price=15.0, stock=10)
    assert updated.name == "Updated Description"
    assert updated.price == 15.0
    assert updated.stock == 10
    assert updated.sold == 2  # Not updated


def test_delete_product(in_memory_db):
    """Verify deleting a product removes it from the database."""
    art = product_crud.create("DEL-001", "To Delete", price=20.0)

    # Verify it exists
    found = product_crud.get_by_id(art.id)
    assert found is not None

    # Delete it
    product_crud.delete(art.id)

    # Verify it's gone
    found_after = product_crud.get_by_id(art.id)
    assert found_after is None
