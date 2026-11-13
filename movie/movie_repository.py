from user import user_repository
from typing import Optional, List


async def get_all_movies() -> list[dict]:
    response = await user_repository.supabase.table("movie_cache").select("*").execute()
    return response.data


async def get_movie_by_external_id(external_id: int) -> dict | None:
    response = await user_repository.supabase.table("movie_cache") \
        .select("*, genres:genre(*)") \
        .eq("movie_external_id", external_id) \
        .execute()
    return response.data[0] if response.data else None


async def create_movie(movie_data: dict) -> dict:
    response = await user_repository.supabase.table("movie_cache").insert(movie_data).execute()
    return response.data[0]


async def update_movie(movie_id: int, movie_data: dict) -> dict:
    response = await user_repository.supabase.table("movie_cache") \
        .update(movie_data) \
        .eq("id", movie_id) \
        .execute()
    return response.data[0]


async def get_movies_filtered(
    search: Optional[str],
    genres: Optional[List[str]],
    page: int,
    limit: int
) -> list[dict]:
    if genres:
        query = user_repository.supabase.table("movie_cache").select("*, genres:genre!inner(*)")
        query = query.in_("genre.name", genres)
    else:
        query = user_repository.supabase.table("movie_cache").select("*, genres:genre(*)")

    if search:
        query = query.ilike("title", f"%{search}%")

    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1)
    response = await query.execute()
    return response.data


async def create_interaction(user_id: int, movie_id: int, rating: int) -> dict:
    existing = await user_repository.supabase.table("interaction") \
        .select("id") \
        .eq("user_id", user_id) \
        .eq("movie_id", movie_id) \
        .execute()

    if existing.data:
        response = await user_repository.supabase.table("interaction") \
            .update({"rating": rating}) \
            .eq("id", existing.data[0]["id"]) \
            .execute()
        return response.data[0]

    response = await user_repository.supabase.table("interaction").insert({
        "user_id": user_id,
        "movie_id": movie_id,
        "rating": rating
    }).execute()
    return response.data[0]


async def get_liked_movies(user_id: int) -> list[dict]:
    inter_resp = await user_repository.supabase.table("interaction") \
        .select("movie_id") \
        .eq("user_id", user_id) \
        .eq("rating", 1) \
        .execute()

    if not inter_resp.data:
        return []

    liked_ids = [row["movie_id"] for row in inter_resp.data]

    movies_resp = await user_repository.supabase.table("movie_cache") \
        .select("*, genres:genre(*)") \
        .in_("id", liked_ids) \
        .execute()

    return movies_resp.data


async def delete_interaction(user_id: int, movie_id: int) -> None:
    await user_repository.supabase.table("interaction") \
        .delete() \
        .eq("user_id", user_id) \
        .eq("movie_id", movie_id) \
        .execute()


async def get_recommendations(user_id: int, limit: int = 10) -> list[dict]:
    response = await user_repository.supabase.table("recommendation_cache") \
        .select("rank, movie_cache(*, genres:genre(*))") \
        .eq("user_id", user_id) \
        .order("rank") \
        .limit(limit) \
        .execute()
    return [row["movie_cache"] for row in response.data if row.get("movie_cache")]


async def get_all_genres() -> list[dict]:
    response = await user_repository.supabase.table("genre").select("*").execute()
    return response.data


async def get_or_create_genre(genre_name: str) -> int:
    response = await user_repository.supabase.table("genre").select("id").eq("name", genre_name).execute()

    if response.data:
        return response.data[0]["id"]

    new_genre = await user_repository.supabase.table("genre").insert({"name": genre_name}).execute()
    return new_genre.data[0]["id"]


async def link_movie_genre(genre_id: int, movie_id: int) -> None:
    await user_repository.supabase.table("genre_movie").upsert({
        "genre_id": genre_id,
        "movie_cache_id": movie_id
    }).execute()
