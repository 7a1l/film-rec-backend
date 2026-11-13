import os
import httpx
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from movie import movie_repository
from movie.movie_schemas import InteractionCreate
from typing import Optional, List

KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY")
EXTERNAL_API_URL = "https://kinopoiskapiunofficial.tech"

LAST_SYNC_TIME = None
SYNC_INTERVAL = timedelta(hours=24)
PAGES_TO_DOWNLOAD = 100


async def sync_movies_from_api() -> bool:
    global LAST_SYNC_TIME
    now = datetime.now(timezone.utc)

    if LAST_SYNC_TIME and (now - LAST_SYNC_TIME) < SYNC_INTERVAL:
        return True

    if not KINOPOISK_API_KEY:
        print("⚠️ KINOPOISK_API_KEY не задан, пропускаем синхронизацию.")
        return False

    headers = {"X-API-KEY": KINOPOISK_API_KEY, "Content-Type": "application/json"}
    added_count = 0

    try:
        async with httpx.AsyncClient() as client:
            for page in range(1, PAGES_TO_DOWNLOAD + 1):
                params = {"order": "NUM_VOTE", "type": "FILM", "page": page}
                response = await client.get(EXTERNAL_API_URL, headers=headers, params=params, timeout=15.0)

                # Проверяем статус и наличие тела ответа перед парсингом JSON
                if response.status_code != 200 or not response.content:
                    print(f"⚠️ API Кинопоиска вернуло статус {response.status_code} или пустой ответ.")
                    break

                data = response.json()
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    ext_id = item["kinopoiskId"]
                    existing_movie = await movie_repository.get_movie_by_external_id(ext_id)

                    countries_list = [c["country"] for c in item.get("countries", [])]
                    countries_str = ", ".join(countries_list) if countries_list else None

                    movie_data = {
                        "title": item["nameRu"] or item["nameEn"],
                        "description": item.get("description", "Описание отсутствует"),
                        "poster_url": item.get("posterUrl"),
                        "year": item.get("year"),
                        "rating_kinopoisk": item.get("ratingKinopoisk"),
                        "rating_imdb": item.get("ratingImdb"),
                        "rating_votes": item.get("ratingKinopoiskVoteCount"),
                        "countries": countries_str,
                    }

                    if existing_movie:
                        await movie_repository.update_movie(existing_movie["id"], movie_data)
                        db_movie_id = existing_movie["id"]
                    else:
                        movie_data["movie_external_id"] = ext_id
                        created = await movie_repository.create_movie(movie_data)
                        db_movie_id = created["id"]
                        added_count += 1

                    for g in item.get("genres", []):
                        genre_name = g.get("genre")
                        if genre_name:
                            genre_id = await movie_repository.get_or_create_genre(genre_name)
                            await movie_repository.link_movie_genre(genre_id, db_movie_id)

        LAST_SYNC_TIME = now
        return True

    except Exception as e:
        print(f"⚠️ Ошибка при синхронизации с Кинопоиском (отдаем кэш из БД): {e}")
        # Ставим метку времени, чтобы не долбить упавшее API при каждом клике пользователя
        LAST_SYNC_TIME = now
        return False



async def get_movie_details(ext_id: int) -> dict:
    movie = await movie_repository.get_movie_by_external_id(ext_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Фильм не найден в каталоге")

    headers = {"X-API-KEY": KINOPOISK_API_KEY, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{EXTERNAL_API_URL}/{ext_id}", headers=headers, timeout=10.0)
            if response.status_code == 200:
                details = response.json()

                movie["title_original"] = details.get("nameOriginal")
                desc = details.get("description") or details.get("shortDescription")
                movie["description"] = desc if desc else "Описание отсутствует"
                movie["film_length"] = details.get("filmLength")
                movie["slogan"] = details.get("slogan")
                movie["film_type"] = details.get("type")

                genres = []
                for g in details.get("genres", []):
                    genres.append({"id": 0, "name": g["genre"]})
                movie["genres"] = genres

    except Exception:
        pass

    return movie


async def get_movies(search: Optional[str], genres: Optional[List[str]], page: int, limit: int) -> list[dict]:
    await sync_movies_from_api()
    return await movie_repository.get_movies_filtered(search, genres, page, limit)


async def create_interaction(user_id: int, interaction: InteractionCreate) -> dict:
    movie = await movie_repository.get_movie_by_external_id(interaction.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Фильм не найден в базе")

    if interaction.rating not in (-1, 1):
        raise HTTPException(status_code=400, detail="Рейтинг должен быть 1 (лайк) или -1 (дизлайк)")

    return await movie_repository.create_interaction(
        user_id=user_id,
        movie_id=movie["id"],
        rating=interaction.rating
    )


async def get_liked_movies(user_id: int) -> list[dict]:
    return await movie_repository.get_liked_movies(user_id)


async def delete_interaction(user_id: int, ext_movie_id: int) -> None:
    movie = await movie_repository.get_movie_by_external_id(ext_movie_id)
    if movie:
        await movie_repository.delete_interaction(user_id, movie["id"])
