from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from movie import movie_router
from user import user_repository, user_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация единого асинхронного клиента Supabase
    await user_repository.init_supabase()
    yield

app = FastAPI(lifespan=lifespan, title="Movie Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movie_router.router)
app.include_router(user_router.router)

@app.get("/")
def read_root():
    return {"message": "API работает! Документация на /docs"}