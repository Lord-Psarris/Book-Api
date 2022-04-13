from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Text
from database import Base


class Author(Base):
    __tablename__ = "author"

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


categories = ['mystery', 'history', 'sci-fi', 'fiction', 'action', 'drama', 'horror', 'thriller']
