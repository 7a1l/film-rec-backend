from pydantic import BaseModel, Field
from typing import Optional, List

class GenreResponse(BaseModel):
    id: int = 0
    name: str

    class Config:
        from_attributes = True

class MovieResponse(BaseModel):
    id: int
    movie_external_id: int
    title: str
    title_original: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    year: Optional[int] = None
    rating_kinopoisk: Optional[float] = None
    rating_imdb: Optional[float] = None
    rating_votes: Optional[int] = None
    film_length: Optional[int] = None
    slogan: Optional[str] = None
    countries: Optional[str] = None
    film_type: Optional[str] = None
    genres: List[GenreResponse] = []

    class Config:
        from_attributes = True

class InteractionCreate(BaseModel):
    movie_id: int = Field(..., description="Внешний ID фильма")
    rating: int = Field(..., description="-1 - дизлайк, 1 - лайк", ge=-1, le=1)