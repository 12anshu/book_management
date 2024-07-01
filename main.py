import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, conint, condecimal
from typing import Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from datetime import date
from sqlalchemy.sql import func
app = FastAPI()

models.Base.metadata.create_all(bind=engine)

class BookModel(BaseModel):
    title: str
    author : str
    genre : str
    year_published : conint(ge=0)
    summary : str


class ReviewsModel(BaseModel):
    user_id : int
    review_text : str
    rating : condecimal(ge=0, le=5, decimal_places=1)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/books")
async def create_books(books: BookModel, db:db_dependency):
    db_book = models.Books(title=books.title, author=books.author, genre=books.genre, 
                           year_published=books.year_published, summary=books.summary)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)

@app.get("/books/")
async def read_books(db:db_dependency):
    result = db.query(models.Books)
    if not list(result):
        raise HTTPException(status_code=404, detail="Book details not found")
    return list(result)

@app.get("/books/{id}")
async def read_book(id:int, db:db_dependency):
    result = db.query(models.Books).filter(models.Books.id == id)
    if not list(result):
        raise HTTPException(status_code=404, detail="Book details not found")
    return list(result)

@app.put("/books/{id}")
async def update_book(id:int, book_details:BookModel, db:db_dependency):
    query = db.query(models.Books).filter(models.Books.id == id)
    if not list(query):
        raise HTTPException(status_code=404, detail="Book details not found")
    update_query = query.update(book_details.model_dump())
    db.commit()
    return list(query)

@app.delete("/books/{id}")
async def delete_book(id:int, db:db_dependency):
    delete_query = db.query(models.Books).filter(models.Books.id == id)
    if not list(delete_query):
        raise HTTPException(status_code=404, detail="No Book to delete")
    delete_query.delete()
    db.commit()

@app.post("/books/{id}/reviews/")
async def create_reviews(id:int, reviews:ReviewsModel, db:db_dependency):
    review_book = models.Reviews(book_id=id, user_id=reviews.user_id, review_text=reviews.review_text, 
                                 rating=reviews.rating)
    db.add(review_book)
    db.commit()
    db.refresh(review_book)
    return review_book

@app.get("/books/{id}/reviews")
async def read_reviews(id:int, db:db_dependency):
    read_review = db.query(models.Reviews).filter(models.Reviews.book_id == id)
    return list(read_review)

@app.get("/books/{id}/summary/")
async def read_summary(id:int, db:db_dependency):
    books = db.query(models.Books).filter(models.Books.id == id).first()
    rating = db.query(func.avg(models.Reviews.rating)).filter(models.Reviews.book_id == id).scalar()
    result = {
        "title" : books.title,
        "summary" : books.summary,
        "rating" : f"{rating:.2f}"
    }
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)