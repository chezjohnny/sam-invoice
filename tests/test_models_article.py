import sam_invoice.models.crud_article as crud


def test_create_and_query_article(in_memory_db):
    """Create an article and verify it can be queried back via the CRUD API."""
    art = crud.create_article("ART-001", "Test Article", prix=25.50, stock=10, vendu=5)
    assert art.id is not None
    assert art.ref == "ART-001"
    assert art.desc == "Test Article"
    assert art.prix == 25.50
    assert art.stock == 10
    assert art.vendu == 5

    articles = crud.get_articles()
    assert any(a.ref == "ART-001" for a in articles)


def test_search_articles(in_memory_db):
    """Verify `search_articles` finds articles by id, ref and description."""
    # Create several articles
    art1 = crud.create_article("VIN-001", "Château Margaux 2015", prix=450.0, stock=24)
    crud.create_article("VIN-002", "Château Latour 2010", prix=650.0, stock=18)
    crud.create_article("WINE-003", "Burgundy Special", prix=85.0, stock=48)

    # Empty query returns all articles
    all_res = crud.search_articles("")
    assert len(all_res) >= 3

    # Search by exact id (string)
    res_id = crud.search_articles(str(art1.id))
    assert any(r.id == art1.id for r in res_id)

    # Partial ref (case-insensitive)
    res_ref = crud.search_articles("vin")
    assert len(res_ref) >= 2
    assert any("vin" in r.ref.lower() for r in res_ref)

    # Partial description
    res_desc = crud.search_articles("château")
    assert len(res_desc) >= 2
    assert any("château" in r.desc.lower() for r in res_desc)


def test_get_articles_sorted(in_memory_db):
    """`get_articles` returns articles ordered by ref case-insensitively."""
    crud.create_article("Z-001", "Zinfandel", prix=30.0)
    crud.create_article("a-002", "Alsace", prix=25.0)
    crud.create_article("M-003", "Margaux", prix=450.0)

    articles = crud.get_articles()
    refs = [a.ref for a in articles]
    expected = sorted(refs, key=lambda s: s.lower())
    assert [r.lower() for r in refs] == [r.lower() for r in expected]


def test_search_articles_sorted(in_memory_db):
    """`search_articles` returns ordered results for empty and partial queries."""
    crud.create_article("Z-001", "Zinfandel", prix=30.0)
    crud.create_article("A-002", "Alsace", prix=25.0)
    crud.create_article("B-003", "Bordeaux", prix=80.0)

    # Empty search should return ordered by ref
    res = crud.search_articles("")
    refs = [a.ref for a in res]
    assert [r.lower() for r in refs] == sorted([r.lower() for r in refs])

    # Partial search should also be ordered
    res2 = crud.search_articles("a")
    refs2 = [a.ref for a in res2]
    assert [r.lower() for r in refs2] == sorted([r.lower() for r in refs2])


def test_update_article(in_memory_db):
    """Verify updating an article modifies its fields correctly."""
    art = crud.create_article("TEST-001", "Original", prix=10.0, stock=5, vendu=2)
    assert art.desc == "Original"

    updated = crud.update_article(art.id, desc="Updated Description", prix=15.0, stock=10)
    assert updated.desc == "Updated Description"
    assert updated.prix == 15.0
    assert updated.stock == 10
    assert updated.vendu == 2  # Not updated


def test_delete_article(in_memory_db):
    """Verify deleting an article removes it from the database."""
    art = crud.create_article("DEL-001", "To Delete", prix=20.0)
    art_id = art.id

    # Verify it exists
    found = crud.get_article_by_id(art_id)
    assert found is not None

    # Delete it
    crud.delete_article(art_id)

    # Verify it's gone
    found_after = crud.get_article_by_id(art_id)
    assert found_after is None
