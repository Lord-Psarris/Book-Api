from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Text
from database import Base


class Author(Base):
    __tablename__ = "author"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password = Column(String)
    email = Column(String)
    auth_key = Column(String, unique=True)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password = Column(String)
    email = Column(String)
    auth_key = Column(String, unique=True)


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey(Author.id))
    description = Column(Text)
    pdf = Column(String)
    price = Column(Integer)
    is_free = Column(Boolean)
    image_path = Column(String)
    category = Column(String)


class PurchasedBooks(Base):
    __tablename__ = "purchased_books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    book_id = Column(String)


class BookPayments(Base):
    __tablename__ = "book_payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    book_id = Column(String)
    price = Column(Integer)
    ref = Column(String)
    verified = Column(Boolean)


categories = ['mystery', 'history', 'sci-fi', 'fiction', 'action', 'drama', 'horror', 'thriller']
