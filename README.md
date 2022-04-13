# Book Store API

Book store api made using Fast API, SQLAlchemy and Stripe. Users are provided with a sortable catalog of e-books which
they can view, purchase and download. Authors are allowed to upload either free or priced books to the database. Payment
integration was done using Stripe

## Setup

Install all requirements

`pip install -r requirements.txt`

Start the server

`uvicorn app:app --reload`

## All Enpoints

| Endpoint                            | Auth Required | Description                                                                           | Method | Payload                                                  |
|-------------------------------------|---------------|---------------------------------------------------------------------------------------|--------|----------------------------------------------------------|
| /                                   | False         | Welcome                                                                               | GET    | None                                                     |
| /get-all-books                      | False         | Gets a list of all uploaded books                                                     | GET    | None                                                     |
| /get-all-authors                    | False         | Gets a list of all verified authors                                                   | GET    | None                                                     |
| /get-all-categories                 | False         | Gets a list of all valid book categories                                              | GET    | None                                                     |
| /get-book/{book_id}                 | False         | Gets details on a book based on its id                                                | GET    | None                                                     |
| /get-all-category-books/{category}  | False         | Gets a list of all books belonging to a specific category                             | GET    | None                                                     |
| /get-author-books/{author_username} | False         | Gets a list of all books uploaded by an author                                        | GET    | None                                                     |
| /get-book-image/{book_id}           | False         | Gets the image of a book                                                              | GET    | None                                                     |
| /get-book-pdf/{book_id}             | False         | Gets the books pdf file. If the book isnt free the user needs to be authenticated     | GET    | None                                                     |
| /register-author                    | False         | Registers Author                                                                      | POST   | email, username. password                                |
| /login-author                       | False         | Returns the authors authentication token                                              | POST   | email. password                                          |
| /add-book                           | True          | Uploads a book and its details to the database                                        | POST   | title, description, price, is_free, category, image, pdf |
| /delete-book/{book_id}              | True          | Deletes book from database                                                            | GET    | None                                                     |
| /register-user                      | False         | Registers User                                                                        | POST   | email, username. password                                |
| /login-user                         | False         | Returns the users authentication token                                                | POST   | email, password                                          |
| /purchase-book/{book_id}            | True          | Allows the user to download a book if its free, or returns a payment link if it isn't | GET    | None                                                     |
| /process-payment/{book_id}          | True          | Processes the users payment using stripe                                              | POST   | card_number, card_expiration_year, card_expiration_month |
