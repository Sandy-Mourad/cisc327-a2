"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_patron_borrowed_books, get_db_connection
)

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed >= 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    
    TODO: Implement R4 as per requirements
    we gon put this right here
    return False, "Book return functionality is not yet implemented."
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID."

    # Check if book exists
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."

    # Check if this patron actually borrowed the book
    borrowed_books = get_patron_borrowed_books(patron_id)
    borrowed_ids = [b['book_id'] for b in borrowed_books]
    if book_id not in borrowed_ids:
        return False, "You did not borrow this book."

    # Update return date
    if not update_borrow_record_return_date(patron_id, book_id, datetime.now()):
        return False, "Failed to update return record."

    # Increment availability
    if not update_book_availability(book_id, 1):
        return False, "Failed to update book availability."

    return True, f'Book "{book["title"]}" returned successfully.'

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
    
    TODO: Implement R5 as per requirements 
    
    
    return { // return the calculated values
        'fee_amount': 0.00,
        'days_overdue': 0,
        'status': 'Late fee calculation not implemented'
    }
    """
    conn = get_db_connection()
    record = conn.execute('''
        SELECT * FROM borrow_records 
        WHERE patron_id = ? AND book_id = ? 
        ORDER BY borrow_date DESC
        LIMIT 1
    ''', (patron_id, book_id)).fetchone()
    conn.close()

    if not record:
        return {"fee_amount": 0.0, "days_overdue": 0, "status": "No record"}

    due_date = datetime.fromisoformat(record["due_date"])
    return_date = record["return_date"]
    if return_date:
        return_date = datetime.fromisoformat(return_date)
    else:
        return_date = datetime.now()

    days_overdue = (return_date - due_date).days
    if days_overdue <= 0:
        return {"fee_amount": 0.0, "days_overdue": 0, "status": "On time"}

    fee = min(days_overdue * 0.50, 15.00)
    return {"fee_amount": round(fee, 2), "days_overdue": days_overdue, "status": "Overdue"}

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    
    TODO: Implement R6 as per requirements
    """
    if not search_term or not search_type:
        return []

    search_term = search_term.lower()
    all_books = get_all_books()
    results = []

    for book in all_books:
        if search_type == "title" and search_term in book["title"].lower():
            results.append(book)
        elif search_type == "author" and search_term in book["author"].lower():
            results.append(book)
        elif search_type == "isbn" and search_term == book["isbn"]:
            results.append(book)

    return results

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.
    
    TODO: Implement R7 as per requirements
    """
    report = {
        "patron_id": patron_id,
        "borrowed_books": [],
        "outstanding_fees": 0.0,
        "history": []
    }

    # Current active borrows
    borrowed_books = get_patron_borrowed_books(patron_id)
    report["borrowed_books"] = borrowed_books

    # Calculate total fees for active borrows
    total_fees = 0.0
    for b in borrowed_books:
        fee_info = calculate_late_fee_for_book(patron_id, b["book_id"])
        total_fees += fee_info["fee_amount"]
    report["outstanding_fees"] = round(total_fees, 2)

    # Borrow history (returned or active)
    conn = get_db_connection()
    records = conn.execute('''
        SELECT br.*, b.title, b.author 
        FROM borrow_records br
        JOIN books b ON br.book_id = b.id
        WHERE br.patron_id = ?
        ORDER BY br.borrow_date DESC
    ''', (patron_id,)).fetchall()
    conn.close()

    history_list = []
    for r in records:
        history_list.append({
            "book_id": r["book_id"],
            "title": r["title"],
            "borrow_date": r["borrow_date"],
            "return_date": r["return_date"],
            "due_date": r["due_date"]
        })
    report["history"] = history_list

    return report
