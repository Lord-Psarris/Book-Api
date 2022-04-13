import re

from fastapi import FastAPI, Depends, Form, HTTPException, UploadFile, File
from pydantic import BaseModel
from starlette.requests import Request
from sqlalchemy.orm import Session

import models
from database import SessionLocal, engine
from auth import AuthHandler
from schemas import RegistrationAuthDetails, LoginAuthDetails, BookDetails

auth_handler = AuthHandler()
images_url = 'images/'
pdfs_url = 'pdfs/'

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AnyForm:
    def __init__(self, any_param: str = Form(...), any_other_param: int = Form(1)):
        self.any_param = any_param
        self.any_other_param = any_other_param

    def __str__(self):
        return "AnyForm " + str(self.__dict__)


# regular user requests
@app.get("/")
def home():
    return {'Welcome': 'This is the ebook api'}


@app.get("/get-all-books")
def get_all_books(db: Session = Depends(get_db)):
    all_books = db.query(models.Book).all()
    books = []

    for book in all_books:
        book_item = {
            'id': book.id,
            'title': book.title,
            'description': book.description,
            'category': book.category,
            'price': book.price,
            'is_free': book.is_free
        }
        books.append(book_item)
    return {'books': books}


@app.get("/get-all-authors")
def get_all_authors(request: Request, db: Session = Depends(get_db)):
    all_authors = db.query(models.Author).all()
    authors = [i.username for i in all_authors]

    return {'data': authors}


@app.get("/get-all-categories")
def get_all_categories(request: Request, db: Session = Depends(get_db)):
    return {'data': models.categories}


@app.get("/get-book/{book_id}")
def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter_by(id=book_id).first()
    if book is None:
        raise HTTPException(status_code=400, detail='Book does not exist')
    author = db.query(models.Author).filter_by(id=book.author_id).first()

    book_data = {
        'author': author.username,
        'id': book.id,
        'title': book.title,
        'description': book.description,
        'category': book.category,
        'price': book.price,
        'is_free': book.is_free
    }

    return {'book': book_data}


@app.get("/get-category-books/{category}")
def get_all_category_books(request: Request, category: str, db: Session = Depends(get_db)):
    if category not in models.categories:
        raise HTTPException(status_code=400, detail='invalid category')

    all_books = db.query(models.Book).filter_by(category=category).all()
    books = []

    for book in all_books:
        book_item = {
            'id': book.id,
            'title': book.title,
            'description': book.description,
            'category': book.category,
            'price': book.price,
            'is_free': book.is_free
        }
        books.append(book_item)
    return {'books': books}


@app.get("/get-author-books/{author_username}")
def get_all_author_books(author_username: str, db: Session = Depends(get_db)):
    author = db.query(models.Author).filter_by(username=author_username).first()
    if author is None:
        raise HTTPException(status_code=400, detail='Author does not exist')

    author_books = db.query(models.Book).filter_by(author_id=author.id).all()
    books = []

    for book in author_books:
        book_item = {
            'id': book.id,
            'title': book.title,
            'description': book.description,
            'category': book.category,
            'price': book.price,
            'is_free': book.is_free
        }
        books.append(book_item)
    return {'books': books}


@app.post("/register-author")
def register_author(email: str = Form(...), password: str = Form(...), username: str = Form(...),
                    db: Session = Depends(get_db)):
    # regex for email validation
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if not (re.fullmatch(regex, email)):
        raise HTTPException(status_code=400, detail='Email is invalid')

    author_email_exists = db.query(models.Author).filter_by(email=email).first()
    author_username_exists = db.query(models.Author).filter_by(username=username).first()
    if author_email_exists is not None or author_username_exists is not None:
        raise HTTPException(status_code=400, detail='User already exists')

    hashed_password = auth_handler.get_password_hash(password)

    new_author = models.Author(username=username, email=email, password=hashed_password)
    db.add(new_author)
    db.commit()

    return {'username': username, 'message': 'Registration was successful'}


@app.post("/login-author")
async def login_author(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    author = db.query(models.Author).filter_by(email=email).first()

    if (author is None) or (not auth_handler.verify_password(password, author.password)):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')

    token = auth_handler.encode_token(author.email)
    return {'message': 'Login details verified, here is your authentication token', 'token': token}


@app.post("/add-books")
async def add_books(title: str = Form(...), description: str = Form(...), price: int = Form(...),
                    is_free: bool = Form(...), category: str = Form(...), image: UploadFile = File(...),
                    pdf: UploadFile = File(...), db: Session = Depends(get_db),
                    email=Depends(auth_handler.auth_wrapper)):
    category = category.lower()

    if category.lower() not in models.categories:
        return {'data': 'Invalid Category'}

    if not image or not pdf:
        raise HTTPException(status_code=406, detail='Please attach required files to form')

    if image.content_type not in ['image/jpeg', 'image/png']:
        raise HTTPException(status_code=406, detail="Please upload only .jpeg/.png files for the image")

    if pdf.content_type != 'application/pdf':
        raise HTTPException(status_code=406, detail="Please upload only .pdf files for the pdf")

    book_exists = db.query(models.Book).filter_by(title=title).first()
    if book_exists is not None:
        raise HTTPException(status_code=406, detail="This book already exists")

    author = db.query(models.Author).filter_by(email=email).first()
    author_id = author.id

    image_data = await image.read()
    image_name = image.filename
    image_file_path = images_url + image_name

    saved_image = open(image_file_path, "wb")
    saved_image.write(image_data)
    saved_image.close()

    pdf_data = await pdf.read()
    pdf_name = pdf.filename
    pdf_file_path = pdfs_url + pdf_name

    saved_pdf = open(pdf_file_path, "wb")
    saved_pdf.write(pdf_data)
    saved_pdf.close()

    new_book = models.Book(title=title, description=description, price=price, is_free=is_free, category=category,
                           author_id=author_id, pdf=pdf_file_path, image_path=image_file_path)
    db.add(new_book)
    db.commit()

    return {"message": "Book uploaded successfully", "book_name": title}


@app.post("/purchase-book/{book_id}")
def purchase_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter_by(id=book_id).first()
    return_data = {}

    if book is None:
        raise HTTPException(status_code=400, detail='Book does not exist')

    if book.is_free:
        # add download link
        pass
    else:
        pass
        # add payment link
    return {}
