from enum import Enum
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from database import SessionLocal, engine
from models import Movies

app = FastAPI(
    title="Movie CRUD API",
    description="A simple movie api end point built with fastapi and sqlite",
    version="1.0.0",
)


class GenreEnum(str, Enum):
    ACTION = "action"
    COMEDY = "comedy"
    DRAMA = "drama"
    THRILLER = "thriller"


class MovieCreate(BaseModel):
    movie_id: int
    title: str
    director: str
    genre: GenreEnum
    duration: int
    rating: float = Field(gt=0, le=11)


class MovieUpdate(BaseModel):
    title: Optional[str] = Field(default=None)
    director: Optional[str] = Field(default=None)
    genre: Optional[GenreEnum] = Field(default=None)
    duration: Optional[int] = Field(default=None)
    rating: Optional[float] = Field(default=None, gt=0, le=11)


models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/")
def root():
    return "Welcome to Movies API"


@app.get("/movies")
def show_all_movies(db: db_dependency):
    return db.query(Movies).all()


@app.get("/movies/{movie_id}")
def show_single_movie(movie_id: int, db: db_dependency):
    single_movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()

    if single_movie is not None:
        return single_movie
    else:
        raise HTTPException(status_code=404, detail="Movie Not Found")


@app.get("/movies/sort/")
def show_sorted_movies(
    db: db_dependency,
    sort_by: str = Query(
        "rating", description="Sort on the Basis of duration or rating"
    ),
    order: str = Query("desc", description="Choose order: asc or desc"),
):
    valid_fields = ["duration", "rating"]

    if sort_by not in valid_fields:
        raise HTTPException(
            status_code=422, detail=f"Invalid Field, Select From {valid_fields}"
        )

    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=422, detail="Choose Between asc or desc")

    movieData = db.query(Movies).all()

    if order == "asc":
        sorted_data = list(movieData)
        sorted_data.sort(key=lambda x: getattr(x, sort_by))
        return sorted_data
    else:
        sorted_data = list(movieData)
        sorted_data.sort(key=lambda x: getattr(x, sort_by), reverse=True)
        return sorted_data


@app.post("/create_movies")
def create_movie(db: db_dependency, new_movie: MovieCreate):
    movie_model = Movies(**new_movie.model_dump())

    db.add(movie_model)
    db.commit()

    return JSONResponse(
        status_code=201, content={"message": "Movie Created Successfully!!"}
    )


@app.put("/movies/{movie_id}")
def edit_movie(db: db_dependency, movie_id: int, update_movie: MovieUpdate):
    edit_movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()

    if edit_movie is None:
        raise HTTPException(status_code=404, detail="Movie Not Found")

    update_data = update_movie.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(edit_movie, key, value)

    db.commit()
    return JSONResponse(
        status_code=200, content={"message": "Movie Updated Successfully!!"}
    )


@app.delete("/movies/{movie_id}")
def delete_movie(db: db_dependency, movie_id: int):
    delete_movie = db.query(Movies).filter(Movies.movie_id == movie_id).first()

    if delete_movie is None:
        raise HTTPException(status_code=404, detail="Movie Not Found")

    db.query(Movies).filter(Movies.movie_id == movie_id).delete()

    db.commit()
    return JSONResponse(
        status_code=200, content={"message": "Movie Deleted Successfully!!"}
    )
