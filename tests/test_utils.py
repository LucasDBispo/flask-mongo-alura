from app.utils import format_currency


def test_format_currency_with_decimal():
    input_value = 1234.56
    result = format_currency(input_value)

    assert result == "1234,56"


def test_format_currency_with_integer():

    assert format_currency(943) == "943,00"


def test_format_currency_with_zero():

    assert format_currency(0) == "0,00"
