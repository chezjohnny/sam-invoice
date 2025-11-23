import sam_invoice.models.crud_product as crud


def test_create_and_query_article(in_memory_db):
    """Create an article and verify it can be queried back via the CRUD API."""
    art = crud.create_product("ART-001", "Test Article", price=25.50, stock=10, sold=5)
    assert art.id is not None
    assert art.reference == "ART-001"
    assert art.name == "Test Article"
    assert art.price == 25.50
    assert art.stock == 10
    assert art.sold == 5

    articles = crud.get_products()
    assert any(a.reference == "ART-001" for a in articles)


def test_search_products(in_memory_db):
    """Verify `search_products` finds articles by id, ref and description."""
    # Create several articles
    art1 = crud.create_product("VIN-001", "Château Margaux 2015", price=450.0, stock=24)
    crud.create_product("VIN-002", "Château Latour 2010", price=650.0, stock=18)
    crud.create_product("WINE-003", "Burgundy Special", price=85.0, stock=48)

    # Empty query returns all articles
    all_res = crud.search_products("")
    assert len(all_res) >= 3

    # Search by exact id (string)
    res_id = crud.search_products(str(art1.id))
    assert any(r.id == art1.id for r in res_id)

    # Partial ref (case-insensitive)
    res_ref = crud.search_products("vin")
    assert len(res_ref) >= 2
    assert any("vin" in r.reference.lower() for r in res_ref)

    # Partial description
    res_desc = crud.search_products("château")
    assert len(res_desc) >= 2
    assert any("château" in r.name.lower() for r in res_desc)


def test_get_products_sorted(in_memory_db):
    """`get_products` returns articles ordered by ref case-insensitively."""
    crud.create_product("Z-001", "Zinfandel", price=30.0)
    crud.create_product("a-002", "Alsace", price=25.0)
    crud.create_product("M-003", "Margaux", price=450.0)

    articles = crud.get_products()
    refs = [a.reference for a in articles]
    expected = sorted(refs, key=lambda s: s.lower())
    assert [r.lower() for r in refs] == [r.lower() for r in expected]


def test_search_products_sorted(in_memory_db):
    """`search_products` returns ordered results for empty and partial queries."""
    crud.create_product("Z-001", "Zinfandel", price=30.0)
    crud.create_product("A-002", "Alsace", price=25.0)
    crud.create_product("B-003", "Bordeaux", price=80.0)

    # Empty search should return ordered by ref
    res = crud.search_products("")
    refs = [a.reference for a in res]
    assert [r.lower() for r in refs] == sorted([r.lower() for r in refs])

    # Partial search should also be ordered
    res2 = crud.search_products("a")
    refs2 = [a.reference for a in res2]
    assert [r.lower() for r in refs2] == sorted([r.lower() for r in refs2])


def test_update_product(in_memory_db):
    """Verify updating an article modifies its fields correctly."""
    art = crud.create_product("TEST-001", "Original", price=10.0, stock=5, sold=2)
    assert art.name == "Original"

    updated = crud.update_product(art.id, name="Updated Description", price=15.0, stock=10)
    assert updated.name == "Updated Description"
    assert updated.price == 15.0
    assert updated.stock == 10
    assert updated.sold == 2  # Not updated


def test_delete_product(in_memory_db):
    """Verify deleting an article removes it from the database."""
    art = crud.create_product("DEL-001", "To Delete", price=20.0)
    art_id = art.id

    # Verify it exists
    found = crud.get_product_by_id(art_id)
    assert found is not None

    # Delete it
    crud.delete_product(art_id)

    # Verify it's gone
    found_after = crud.get_product_by_id(art_id)
    assert found_after is None
