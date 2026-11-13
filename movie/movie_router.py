from fastapi import APIRouter, status, Depends, HTTPException, Query
from movie import movie_controller, movie_schemas, movie_repository
from user import user_jwt
from typing import Optional, List
router = APIRouter(prefix="", tags=["Movies"]) # Убрали /movies из prefix, так как пути в таблице разные
@router.get("/movies", response_model=list[movie_schemas.MovieResponse])
async def get_movies(
    search: Optional[str] = Query(None, description="Поиск по названию"),
    genre: Optional[List[str]] = Query(None, description="Фильтрация по списку жанров"),
    page: int = Query(1, description="Номер страницы"),
    limit: int = Query(10, description="Количество на странице")
):
    return await movie_controller.get_movies(search, genre, page, limit)


@router.get("/genres")
async def get_genres():
    return await movie_repository.get_all_genres()

@router.get("/movies/{movie_id}", response_model=movie_schemas.MovieResponse)
async def get_movie(movie_id: int):
    # Вызываем новую функцию, которая ходит в API
    return await movie_controller.get_movie_details(movie_id)

@router.post("/interactions", status_code=status.HTTP_201_CREATED)
async def create_interaction(
    interaction: movie_schemas.InteractionCreate,
    payload_token: dict = Depends(user_jwt.decode_access_token)
):
    user_id = payload_token["id"]
    return await movie_controller.create_interaction(user_id, interaction)

@router.get("/recommendations")
async def get_recommendations(
    limit: int = Query(10, description="Количество рекомендаций"),
    payload_token: dict = Depends(user_jwt.decode_access_token) # Требуется JWT
):
    user_id = payload_token["id"]
    return await movie_repository.get_recommendations(user_id, limit)



@router.get("/interactions/likes", response_model=list[movie_schemas.MovieResponse])
async def get_liked_movies(
    payload_token: dict = Depends(user_jwt.decode_access_token)
):
    user_id = payload_token["id"]
    return await movie_controller.get_liked_movies(user_id)


@router.delete("/interactions/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interaction(
    movie_id: int,
    payload_token: dict = Depends(user_jwt.decode_access_token)
):
    user_id = payload_token["id"]
    await movie_controller.delete_interaction(user_id, movie_id)
    return None