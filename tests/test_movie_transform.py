from src.transforms.movie_transform import transform_movie_details

# Trimmed-down shape of a real TMDb /movie/550 response (with append_to_response).
SAMPLE_RAW = {
    "id": 550,
    "title": "Fight Club",
    "original_title": "Fight Club",
    "release_date": "1999-10-15",
    "runtime": 139,
    "budget": 63000000,
    "revenue": 100853753,
    "original_language": "en",
    "popularity": 61.416,
    "vote_average": 8.4,
    "vote_count": 26280,
    "status": "Released",
    "homepage": "http://www.foxmovies.com/movies/fight-club",
    "imdb_id": "tt0137523",
    "overview": "A ticking-time-bomb insomniac and a slippery soap salesman.",
    "genres": [{"id": 18, "name": "Drama"}],
    "production_companies": [{"id": 711, "name": "Fox 2000 Pictures"}],
    "spoken_languages": [{"iso_639_1": "en", "name": "English"}],
    "external_ids": {"imdb_id": "tt0137523", "facebook_id": "FightClub"},
}


def test_transform_returns_movie_id_and_title():
    result = transform_movie_details(SAMPLE_RAW)
    assert result["movie_id"] == 550
    assert result["title"] == "Fight Club"


def test_transform_values_are_atomic():
    result = transform_movie_details(SAMPLE_RAW)
    for key, value in result.items():
        assert not isinstance(value, (list, dict, tuple, set)), (
            f"field '{key}' should be atomic but is {type(value).__name__}"
        )
