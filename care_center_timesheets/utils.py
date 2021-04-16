from datetime import timedelta


def get_factored_duration(hours, invoice_factor):
    """
    Return discounted duration based on invoice_factor
    """
    if invoice_factor:
        factor_decimal_val = round(invoice_factor.factor / 100, 2)
        hours = ((1 - factor_decimal_val) * hours)
    hours = hours if hours > 0.0 else 0.0

    return hours


def round_timedelta(td, period):
    """
    Rounds the given timedelta up to the given timedelta period
    :param td: `timedelta` to round
    :param period: `timedelta` period to round by.
    """
    period_seconds = period.total_seconds()
    try:
        remainder = td.total_seconds() % period_seconds
    except ZeroDivisionError:
        remainder = 0
    if not remainder:
        return td
    return timedelta(seconds=td.total_seconds() + (period_seconds - remainder))
