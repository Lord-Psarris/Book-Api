import os
import re

import stripe
from fastapi import FastAPI, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import FileResponse

import models
from auth import AuthHandler
from database import SessionLocal, engine

auth_handler = AuthHandler()
app = FastAPI()

stripe.api_key = 'sk_test_4eC39HqLyjWDarjtT1zdp7dc'
models.Base.metadata.create_all(bind=engine)

images_url = 'images/'
pdfs_url = 'pdfs/'


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
        'is_free': book.is_free,
        'image': f'localhost:8000/get-book-image/{book.id}'
    }

    return {'book': book_data}


@app.get("/get-all-category-books/{category}")
def get_books_by_category(request: Request, category: str, db: Session = Depends(get_db)):
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


@app.get("/get-book-image/{book_id}")
def get_book_image(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter_by(id=book_id).first()
    if book is None:
        raise HTTPException(status_code=400, detail='Book does not exist')

    file_path = os.path.join(os.getcwd(), book.image_path)
    return FileResponse(file_path)


@app.get("/get-book-pdf/{book_id}")
def get_book_pdf(request: Request, book_id: int, db: Session = Depends(get_db)):
    """
    this function first validates the book exists. then if the book is free it return the pdf file
    If the book isn't free then we get the authentication token to verify the user. if the user has purchased the book
    then the book is return else an error is raised

    :param request:
    :param book_id:
    :param db:
    :return: dict
    """
    book = db.query(models.Book).filter_by(id=book_id).first()
    if book is None:
        raise HTTPException(status_code=400, detail='Book does not exist')

    if book.is_free:
        file_path = os.path.join(os.getcwd(), book.pdf)
        return FileResponse(file_path, media_type='application/octet-stream', filename=book.pdf.split('/')[1])

    auth_key = request.headers.get('Authorization')
    if auth_key is None:
        raise HTTPException(status_code=400, detail='You are not registered as a user')

    email = auth_handler.decode_token(auth_key.replace('Bearer ', ''))
    user = db.query(models.User).filter_by(email=email).first()
    if user is None:
        raise HTTPException(status_code=400, detail='You are not registered as a user')

    user_id = user.id
    purchased_book = db.query(models.PurchasedBooks).filter_by(user_id=user_id, book_id=book.id).first()
    if purchased_book is None:
        raise HTTPException(status_code=400, detail='You have not purchased this book')

    file_path = os.path.join(os.getcwd(), book.pdf)
    return FileResponse(file_path, media_type='application/octet-stream', filename=book.pdf.split('/')[1])


@app.post("/register-author")
def register_author(email: str = Form(...), password: str = Form(...), username: str = Form(...),
                    db: Session = Depends(get_db)):
    # regex for email validation
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if not (re.fullmatch(regex, email)):
        raise HTTPException(status_code=400, detail='Email is invalid')

    # ensure username and email are unique
    author_email_exists = db.query(models.Author).filter_by(email=email).first()
    author_username_exists = db.query(models.Author).filter_by(username=username).first()
    if author_email_exists is not None or author_username_exists is not None:
        raise HTTPException(status_code=400, detail='Author already exists')

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


@app.post("/add-book")
async def add_book(title: str = Form(...), description: str = Form(...), price: int = Form(...),
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


@app.get("/delete-book/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db), email=Depends(auth_handler.auth_wrapper)):
    author = db.query(models.Author).filter_by(email=email).first()
    if author is None:
        raise HTTPException(status_code=401, detail='Unauthorized')

    author_id = author.id
    book = db.query(models.Book).filter_by(author_id=author_id, id=book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail='Book not found')

    db.delete(book)
    db.commit()

    return {'message': 'book deleted successfully'}


@app.post("/register-user")
def register_user(email: str = Form(...), password: str = Form(...), username: str = Form(...),
                  db: Session = Depends(get_db)):
    # regex for email validation
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if not (re.fullmatch(regex, email)):
        raise HTTPException(status_code=400, detail='Email is invalid')

    user_email_exists = db.query(models.User).filter_by(email=email).first()
    user_username_exists = db.query(models.User).filter_by(username=username).first()
    if user_email_exists is not None or user_username_exists is not None:
        raise HTTPException(status_code=400, detail='User already exists')

    hashed_password = auth_handler.get_password_hash(password)

    new_user = models.User(username=username, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()

    return {'username': username, 'message': 'Registration was successful'}


@app.post("/login-user")
async def login_user(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(email=email).first()

    if (user is None) or (not auth_handler.verify_password(password, user.password)):
        raise HTTPException(status_code=401, detail='Invalid username and/or password')

    token = auth_handler.encode_token(user.email)
    return {'message': 'Login details verified. Here is your authentication token', 'token': token}


@app.get("/purchase-book/{book_id}")
def purchase_book(request: Request, book_id: int, db: Session = Depends(get_db),
                  email=Depends(auth_handler.auth_wrapper)):
    book = db.query(models.Book).filter_by(id=book_id).first()

    if book is None:
        raise HTTPException(status_code=400, detail='Book does not exist')

    user = db.query(models.User).filter_by(email=email).first()
    if user is None:
        raise HTTPException(status_code=400, detail='You are not registered as a user')

    if book.is_free:
        return {
            'message': 'This book is free',
            'title': book.title,
            'pdf': f'localhost:8000/get-book-pdf/{book.id}',
            'image': f'localhost:8000/get-book-image/{book.id}'
        }

    user_id = user.id
    purchased_book = db.query(models.PurchasedBooks).filter_by(user_id=user_id, book_id=book.id).first()
    if purchased_book is not None:
        return {
            'message': 'You have purchased this book',
            'title': book.title,
            'pdf': f'localhost:8000/get-book-pdf/{book.id}',
            'image': f'localhost:8000/get-pdf/{book.id}'
        }

    new_payment = models.BookPayments(book_id=book.id, user_id=user.id, verified=False, price=book.price, ref='')
    db.add(new_payment)
    db.commit()

    return {
        'message': 'Post your card_number, card_name, card_expiration_month, and card_expiration_year to the url',
        'url': f'localhost:8000/process-payment/{book_id}'
    }


@app.post('/process-payment/{book_id}')
def process_payment(book_id: int, card_number: int = Form(...), card_expiration_year: str = Form(...),
                    card_expiration_month: str = Form(...), db: Session = Depends(get_db),
                    email=Depends(auth_handler.auth_wrapper)):
    book = db.query(models.Book).filter_by(id=book_id).first()
    user = db.query(models.User).filter_by(email=email).first()

    if user is None:
        raise HTTPException(status_code=400, detail='You are not registered as a user')

    if book is None:
        raise HTTPException(status_code=400, detail='Book does not exist')

    # create customer
    stripe_customer = stripe.Customer.create(
        description=f"Customer: {user.username}, paying for {book.title} ",
    )
    stripe_customer_id = stripe_customer.id

    # create card
    stripe_card = stripe.Customer.create_source(
        stripe_customer_id,
        source={
            'object': 'card',
            'number': card_number,
            'exp_month': card_expiration_month,
            'exp_year': card_expiration_year,
        }
    )
    stripe_card_id = stripe_card.id

    # create charge
    stripe_charge = stripe.Charge.create(
        customer=stripe_customer_id,
        amount=book.price,
        currency="usd",
        source=stripe_card_id,
        description=f"Customer: {user.username}, paying for {book.title} ",
    )
    stripe_charge_id = stripe_charge.id

    if not stripe_charge['paid']:
        raise HTTPException(status_code=500, detail='Payment Unsuccessful')

    # save payment data
    book_payment = db.query(models.BookPayments).filter_by(user_id=user.id, book_id=book.id).first()
    book_payment.ref = stripe_charge_id
    book_payment.verified = True

    # save book purchase
    new_book_purchased = models.PurchasedBooks(book_id=book.id, user_id=user.id)
    db.add(new_book_purchased)
    db.commit()

    return {
        'message': 'Payment was successful, return back to the url',
        'url': f'localhost:8000/purchase-book/{book_id}'
    }
