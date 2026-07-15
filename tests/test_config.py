import config


def test_reuse_imports_resolve():
    config.ensure_reuse_on_path()
    import pandasta_data, pandasta_registry, stats  # noqa: F401  (vendored, self-contained)
    assert "^GSPC" in pandasta_data.UNIVERSE
    assert config.HORIZON == 5
    assert config.TA_FLAT_DIR.endswith("vendor")     # points at the vendored dir, not the sibling
