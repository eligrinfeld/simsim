def test_data_api_import():
    # Importing the module should succeed in the venv; skip if yfinance missing
    import importlib.util

    try:
        import yfinance  # noqa: F401
    except Exception:
        return
    spec = importlib.util.spec_from_file_location(
        "data_app", "services/data_api/app.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    assert hasattr(mod, "app")
