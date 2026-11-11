from sqlalchemy import create_engine

from app.db import load_entries, save_entries
from app.store import StoreEntry


def _engine():
    return create_engine("sqlite:///:memory:")


def test_load_entries_returns_what_save_entries_persisted():
    engine = _engine()
    entry = StoreEntry(
        id="gid://shopify/Product/1",
        kind="product",
        handle="classic-cotton-t-shirt",
        text="A breathable cotton t-shirt.",
        embedding=[0.1, 0.2, 0.3],
    )

    save_entries(engine, [entry])

    assert load_entries(engine) == [entry]


def test_save_entries_wipes_previously_saved_entries():
    engine = _engine()
    stale = StoreEntry(id="old", kind="product", handle="old", text="stale", embedding=[0.0])
    save_entries(engine, [stale])

    fresh = StoreEntry(id="new", kind="product", handle="new", text="fresh", embedding=[1.0])
    save_entries(engine, [fresh])

    assert load_entries(engine) == [fresh]
