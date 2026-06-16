def test_module_loads(core):
    assert core.VERSION
    assert callable(core.changed_files)
