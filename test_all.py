#name : sandy mourad
#student # : 20406862
#group 3

import pytest

#for r1
from library_service import add_book_to_catalog
from database import get_book_by_isbn

#for r2
from database import get_all_books, insert_book

#for r3
from library_service import borrow_book_by_patron
from database import get_book_by_id, get_all_books

#for r4
from library_service import return_book_by_patron, borrow_book_by_patron
from database import get_all_books, get_book_by_id

#for r5
from library_service import calculate_late_fee_for_book

#for r6
from library_service import search_books_in_catalog

#for r7
from library_service import get_patron_status_report, borrow_book_by_patron

#please ignore the multiple imports since it helped me keep track better

from database import init_database, add_sample_data

# Initialize the database and seed it before running tests
init_database()
add_sample_data()


#r1----------------------------------------------------------------------------------------------------------------------------------------

def test_valid_book_addition_persists_in_db():
    """R1: A completely valid book should be added successfully"""
    title = "SANDYS WRITINGS!"
    author = "Sandy Mourad"
    isbn = "1111111111111"
    copies = 4

    success, msg = add_book_to_catalog(title, author, isbn, copies)

    assert success is True
    assert "success" in msg.lower()

    # confirm it really exists in the DB
    book = get_book_by_isbn(isbn)
    assert book is not None
    assert book["title"] == title
    assert book["available_copies"] == copies

def test_rejects_blank_title():
    """Empty title should trigger a validation error"""
    success, msg = add_book_to_catalog("", "Author Name", "2222222222222", 2)
    assert not success
    assert "title" in msg.lower()

def test_rejects_title_exceeding_length():
    """Title >200 characters should not be allowed."""
    bad_title = "X" * 205
    success, msg = add_book_to_catalog(bad_title, "Author Name", "3333333333333", 2)
    assert not success
    assert "title" in msg.lower()

def test_rejects_invalid_isbn_length():
    """ISBN must be exactly 13 digits, shorter or longer should fail"""
    success, msg = add_book_to_catalog("Book Title", "Author Name", "12345", 2)
    assert not success
    assert "13 digits" in msg

def test_rejects_nonpositive_copies():
    """Copies must be a positive integer"""
    success, msg = add_book_to_catalog("Math Text", "Prof Author", "4444444444444", 0)
    assert not success
    assert "positive" in msg.lower()

def test_duplicate_isbn_blocked():
    """Adding a second book with the same ISBN should be rejected always"""
    add_book_to_catalog("First Entry", "Author A", "5555555555555", 2)
    success, msg = add_book_to_catalog("Second Entry", "Author B", "5555555555555", 3)
    assert not success
    assert "isbn" in msg.lower()


#r2-----------------------------------------------------------------------------------------------------------------------------------------------

def test_catalog_returns_list_of_books():
    """R2: Catalog should return a non-empty list with dictionaries for each book"""
    books = get_all_books()
    assert isinstance(books, list)
    assert all(isinstance(b, dict) for b in books)
    assert {"id", "title", "author", "isbn", "total_copies", "available_copies"} <= set(books[0].keys())

def test_newly_inserted_book_appears_in_catalog():
    """Adding a book directly should make it show up in the catalog listing."""
    isbn = "1010101010101"
    inserted = insert_book("Quantum Mechanics", "Dirac", isbn, 2, 2)
    assert inserted is True

    books = get_all_books()
    found = [b for b in books if b["isbn"] == isbn]
    assert len(found) == 1
    assert found[0]["title"] == "Quantum Mechanics"
    assert found[0]["available_copies"] == 2

def test_availability_reflects_stock_levels(monkeypatch):
    """Catalog entries must show correct available vs total copies"""
    books = get_all_books()
    chosen = books[0]
    assert chosen["available_copies"] <= chosen["total_copies"]

def test_empty_catalog_returns_empty_list(tmp_path, monkeypatch):
    """If no books exist, catalog should return an empty list"""
    import database
    monkeypatch.setattr(database, "DATABASE", str(tmp_path / "empty.db"))
    database.init_database()

    books = database.get_all_books()
    assert books == []

#r3-----------------------------------------------------------------------------------------------------------------------------------------------

def test_successful_borrow_updates_copies():
    """Borrowing a valid book with a proper patron ID should succeed and reduce availability"""
    # Find a book that has at least 1 copy available
    available_book = next(b for b in get_all_books() if b["available_copies"] > 0)
    before = get_book_by_id(available_book["id"])

    success, msg = borrow_book_by_patron("246810", available_book["id"])
    after = get_book_by_id(available_book["id"])

    assert success is True
    assert "borrowed" in msg.lower()
    assert after["available_copies"] == before["available_copies"] - 1

def test_rejects_bad_patron_id():
    """Patron ID must be exactly 6 digits"""
    book = get_all_books()[0]
    success, msg = borrow_book_by_patron("12", book["id"])
    assert success is False
    assert "patron id" in msg.lower()

def test_rejects_nonexistent_book():
    """Trying to borrow a book that does not exist should fail"""
    success, msg = borrow_book_by_patron("135791", 99999)
    assert success is False
    assert "not found" in msg.lower()

def test_cannot_borrow_unavailable_book():
    """If a book has 0 copies left, borrowing should be blocked."""
    #in the sample DB the book with id=3 ('1984') is made unavailable ??
    success, msg = borrow_book_by_patron("654321", 3)
    assert success is False
    assert "not available" in msg.lower()

def test_blocked_after_five_borrows():
    """Patron should not be able to borrow more than 5 books total."""
    patron = "777777"
    #borrow up to 5 books from the catalog
    count = 0
    for book in get_all_books():
        if book["available_copies"] > 0 and count < 5:
            ok, _ = borrow_book_by_patron(patron, book["id"])
            assert ok is True
            count += 1

    if count < 5:
        pytest.skip("Not enough books to reach the limit")

    #lets try the 6th borrow
    extra_book = next(b for b in get_all_books() if b["available_copies"] > 0)
    success, msg = borrow_book_by_patron(patron, extra_book["id"])
    assert success is False, "Spec says max 5 books; implementation may allow 6 due to a bug."
    assert "limit" in msg.lower()


#r4-----------------------------------------------------------------------------------------------------------------------------------------------
    
def test_basic_return_flow():
    """Borrow a book and attempt to return it — currently unimplemented but should return a boolean + message"""
    borrow_book_by_patron("101010", 1)
    success, msg = return_book_by_patron("101010", 1)
    assert isinstance(success, bool)
    assert isinstance(msg, str)

def test_return_without_prior_borrow():
    """If a patron never borrowed the book, return should fail"""
    success, msg = return_book_by_patron("202020", 2)
    assert success is False

def test_double_return_attempt():
    """Once a book is returned, trying to return it again should not be allowed"""
    borrow_book_by_patron("303030", 1)
    return_book_by_patron("303030", 1)  # first return
    success, msg = return_book_by_patron("303030", 1)  # second return attempt
    assert success is False

def test_return_invalid_book_identifier():
    """Supplying a non-existent book ID should produce a failure"""
    success, msg = return_book_by_patron("404040", 9999)
    assert success is False


#r5-----------------------------------------------------------------------------------------------------------------------------------------------

def test_on_time_return_fee_is_zero():
    """If a book is returned before or on the due date, the fee should be zero (not implemented yet)"""
    outcome = calculate_late_fee_for_book("111111", 1)
    assert isinstance(outcome, dict)
    assert "fee_amount" in outcome

def test_fee_for_short_overdue_period():
    """A few days overdue (≤7) should generate a small charge"""
    outcome = calculate_late_fee_for_book("111111", 1)
    assert "fee_amount" in outcome

def test_fee_for_extended_overdue():
    """Overdue more than a week should accumulate larger fees"""
    outcome = calculate_late_fee_for_book("111111", 1)
    assert "fee_amount" in outcome

def test_fee_does_not_exceed_cap():
    """The maximum fee per book must be limited to $15 regardless of delay length"""
    outcome = calculate_late_fee_for_book("111111", 1)
    assert "fee_amount" in outcome

#r6-----------------------------------------------------------------------------------------------------------------------------------------------

def test_title_search_finds_partial_match():
    """Looking up part of a book title should return a list (not implemented yet)"""
    output = search_books_in_catalog("gatsby", "title")
    assert isinstance(output, list)

def test_author_search_finds_partial_match():
    """Searching with part of an author's name should work (case-insensitive)"""
    output = search_books_in_catalog("lee", "author")
    assert isinstance(output, list)

def test_isbn_search_requires_exact_match():
    """Searching by ISBN should only succeed on exact matches"""
    output = search_books_in_catalog("9780743273565", "isbn")
    assert isinstance(output, list)

def test_search_returns_empty_for_invalid_term():
    """If no book matches the query, the result should be an empty list"""
    output = search_books_in_catalog("xyznotfound", "title")
    assert output == []

#r7-----------------------------------------------------------------------------------------------------------------------------------------------

def test_status_returns_dictionary():
    """The status report call should always return a dict (currently unimplemented)"""
    report = get_patron_status_report("111111")
    assert isinstance(report, dict)

def test_status_for_patron_with_no_activity():
    """A patron who never borrowed should get an empty borrowed list"""
    report = get_patron_status_report("222222")
    assert isinstance(report, dict)

def test_status_reflects_active_borrow():
    """Borrowing a book should make it appear in the patron's status"""
    borrow_book_by_patron("333333", 1)
    report = get_patron_status_report("333333")
    assert isinstance(report, dict)

def test_status_contains_fee_information():
    """Eventually the report should include outstanding late fee totals"""
    report = get_patron_status_report("444444")
    assert isinstance(report, dict)

def test_status_includes_history_field():
    """Borrowing history should be part of the status structure"""
    report = get_patron_status_report("555555")
    assert isinstance(report, dict)

#done