import config


def test_reuse_imports_resolve():
    config.ensure_reuse_on_path()
    import pandasta_data, pandasta_registry, stats, pandasta_set_search  # noqa: F401
    assert "^GSPC" in pandasta_data.UNIVERSE
    assert config.HORIZON == 5
