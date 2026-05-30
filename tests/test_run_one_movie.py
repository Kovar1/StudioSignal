def test_run_one_movie_imports_cleanly():
    import src.ingestion.run_one_movie as run_one_movie

    assert hasattr(run_one_movie, "run")
