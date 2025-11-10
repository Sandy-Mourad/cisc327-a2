import pytest
from unittest.mock import Mock
from services.payment_service import PaymentGateway
from services.library_services import pay_late_fees, refund_late_fee_payment



# Tests for pay_late_fees()


def test_pay_late_fees_successful_payment(mocker):
    """checks that a valid late fee triggers a successful mock payment"""
    # Patch where they're USED: services.library_services
    mocker.patch("services.library_services.calculate_late_fee_for_book",
                 return_value={"fee_amount": 7.5})
    mocker.patch("services.library_services.get_book_by_id",
                 return_value={"id": 1, "title": "1984"})

    # Mock the external payment system
    fake_gateway = Mock(spec=PaymentGateway)
    fake_gateway.process_payment.return_value = (True, "txn_123", "Payment accepted")

    ok, msg, txn = pay_late_fees("123456", 1, fake_gateway)

    assert ok is True
    assert "payment successful" in msg.lower()
    assert txn == "txn_123"
    fake_gateway.process_payment.assert_called_once_with(
        patron_id="123456", amount=7.5, description="Late fees for '1984'"
    )


def test_pay_late_fees_decline_message(mocker):
    """if thee mock gateway declines, the payment should fail gracefully."""
    mocker.patch("services.library_services.calculate_late_fee_for_book",
                 return_value={"fee_amount": 5.0})
    mocker.patch("services.library_services.get_book_by_id",
                 return_value={"id": 1, "title": "Gatsby"})

    gateway = Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (False, None, "Card declined")

    ok, msg, txn = pay_late_fees("123456", 1, gateway)

    assert not ok
    assert "failed" in msg.lower()
    assert "declined" in msg.lower()
    assert txn is None
    gateway.process_payment.assert_called_once_with(
        patron_id="123456", amount=5.0, description="Late fees for 'Gatsby'"
    )


def test_invalid_patron_id_skips_gateway():
    """Gateway should not run for an invalid patron ID."""
    gateway = Mock(spec=PaymentGateway)

    ok, msg, txn = pay_late_fees("12x456", 1, gateway)

    assert not ok
    assert txn is None
    assert "invalid patron id" in msg.lower()
    gateway.process_payment.assert_not_called()


def test_zero_fee_no_gateway_call(mocker):
    """If no fee exists it should exit early and not charge anything."""
    mocker.patch("services.library_services.calculate_late_fee_for_book",
                 return_value={"fee_amount": 0.0})

    gateway = Mock(spec=PaymentGateway)

    ok, msg, txn = pay_late_fees("123456", 1, gateway)

    assert not ok
    assert "no late fees" in msg.lower()
    gateway.process_payment.assert_not_called()


def test_book_not_found_no_payment(mocker):
    """if the book ID isn’t found no payment should happen."""
    mocker.patch("services.library_services.calculate_late_fee_for_book",
                 return_value={"fee_amount": 2.0})
    mocker.patch("services.library_services.get_book_by_id",
                 return_value=None)

    gateway = Mock(spec=PaymentGateway)

    ok, msg, txn = pay_late_fees("123456", 1, gateway)

    assert not ok
    assert "book not found" in msg.lower()
    gateway.process_payment.assert_not_called()


def test_gateway_exception_is_handled(mocker):
    """if our gateway crashes, the function should still return a proper message."""
    mocker.patch("services.library_services.calculate_late_fee_for_book",
                 return_value={"fee_amount": 4.0})
    mocker.patch("services.library_services.get_book_by_id",
                 return_value={"id": 1, "title": "Mock Book"})

    gateway = Mock(spec=PaymentGateway)
    gateway.process_payment.side_effect = RuntimeError("network failure")

    ok, msg, txn = pay_late_fees("123456", 1, gateway)

    assert not ok
    assert txn is None
    assert "processing error" in msg.lower()



# Tests for refund_late_fee_payment()


def test_refund_successful_case():
    """happy path, so refund goes through successfully."""
    gateway = Mock(spec=PaymentGateway)
    gateway.refund_payment.return_value = (True, "Refund complete")

    ok, msg = refund_late_fee_payment("txn_999", 6.0, gateway)

    assert ok
    assert "refund" in msg.lower()
    gateway.refund_payment.assert_called_once_with("txn_999", 6.0)


@pytest.mark.parametrize("tid", ["", "abc", "tx_", None])
def test_refund_invalid_txid_no_call(tid):
    """invalid transaction IDs should be caught immediately."""
    gateway = Mock(spec=PaymentGateway)

    ok, msg = refund_late_fee_payment(tid, 4.0, gateway)

    assert not ok
    assert "invalid transaction id" in msg.lower()
    gateway.refund_payment.assert_not_called()


def test_refund_amount_zero_not_allowed():
    """refunds cant be 0!"""
    gateway = Mock(spec=PaymentGateway)
    ok, msg = refund_late_fee_payment("txn_001", 0, gateway)
    assert not ok
    assert "greater than 0" in msg.lower()
    gateway.refund_payment.assert_not_called()


def test_refund_negative_amount_not_allowed():
    """refunds cant be negative"""
    gateway = Mock(spec=PaymentGateway)
    ok, msg = refund_late_fee_payment("txn_001", -5, gateway)
    assert not ok
    assert "greater than 0" in msg.lower()
    gateway.refund_payment.assert_not_called()


def test_refund_amount_too_high_blocked():
    """refunds above $15 should be rejected."""
    gateway = Mock(spec=PaymentGateway)

    ok, msg = refund_late_fee_payment("txn_001", 15.5, gateway)

    assert not ok
    assert "exceeds" in msg.lower()
    gateway.refund_payment.assert_not_called()


def test_refund_gateway_failure_message():
    """if gateway returns a fail we should see its message."""
    gateway = Mock(spec=PaymentGateway)
    gateway.refund_payment.return_value = (False, "Gateway error")

    ok, msg = refund_late_fee_payment("txn_888", 9.0, gateway)

    assert not ok
    assert "refund failed" in msg.lower()
    gateway.refund_payment.assert_called_once_with("txn_888", 9.0)


def test_refund_gateway_exception_handled():
    """if the gateway throws it should be handled cleanly."""
    gateway = Mock(spec=PaymentGateway)
    gateway.refund_payment.side_effect = RuntimeError("timeout")

    ok, msg = refund_late_fee_payment("txn_222", 8.0, gateway)

    assert not ok
    assert "processing error" in msg.lower()
    gateway.refund_payment.assert_called_once_with("txn_222", 8.0)




#i made some extra paymentGateway tests to increase overall coverage
    
def test_pg_process_payment_success(mocker):
    """direct happy path: valid patron + amount -> success."""
    mocker.patch("services.payment_service.time.sleep", return_value=None)
    gw = PaymentGateway()
    ok, txn, msg = gw.process_payment("123456", 20.0, "Late fees")
    assert ok is True
    assert txn.startswith("txn_123456_")
    assert "processed successfully" in msg.lower()


def test_pg_process_payment_invalid_amount_zero(mocker):
    """amount <= 0 should be rejected."""
    mocker.patch("services.payment_service.time.sleep", return_value=None)
    gw = PaymentGateway()
    ok, txn, msg = gw.process_payment("123456", 0.0, "x")
    assert ok is False
    assert txn == ""
    assert "invalid amount" in msg.lower()


def test_pg_process_payment_exceeds_limit(mocker):
    """large amounts should be declined by the gateway."""
    mocker.patch("services.payment_service.time.sleep", return_value=None)
    gw = PaymentGateway()
    ok, txn, msg = gw.process_payment("123456", 2000.0, "x")
    assert ok is False
    assert txn == ""
    assert "exceeds limit" in msg.lower()


def test_pg_refund_payment_success(mocker):
    """refund path success."""
    mocker.patch("services.payment_service.time.sleep", return_value=None)
    gw = PaymentGateway()
    ok, msg = gw.refund_payment("txn_123456_1700000000", 5.0)
    assert ok is True
    assert "refund of $5.00 processed successfully" in msg.lower()


def test_pg_verify_payment_status_invalid(mocker):
    """bad transaction id returns not_found."""
    mocker.patch("services.payment_service.time.sleep", return_value=None)
    gw = PaymentGateway()
    res = gw.verify_payment_status("bad")
    assert res["status"] == "not_found"