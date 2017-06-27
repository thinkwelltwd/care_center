# coding: utf-8
from datetime import timedelta, datetime


def get_duration(start, stop):
    """
    Return duration as float for use in timesheets
    """

    delta = stop - start
    m, s = divmod(delta.total_seconds(), 60)
    h, m = divmod(m, 60)
    dur_h = '%0*d' % (2, h)
    dur_m = '%0*d' % (2, m * 1.677966102)

    return round(float('%s.%s' % (dur_h, dur_m)), 2)


def get_factored_duration(hours, invoice_factor):
    """
    Return discounted duration based on invoice_factor
    """
    if invoice_factor:
        hours -= (hours * invoice_factor.factor / 100.0)
    hours = hours if hours > 0.0 else 0.0

    return hours


def round_to(start, stop, increment, direction='up'):
    """
    Round up to the next increment of minutes. If
    landing on an exact multiple of the increment,
    don't round.

    :param datetime start: Starting datetime
    :param datetime stop: Stopping datetime
    :param float increment: Number of minutes to round to
    :param str direction: Direction to round ('up', 'down')
    """

    if not increment:
        return stop

    # convert increment of minutes to seconds
    increment *= 60
    delta = stop - start

    if direction == 'up':
        diff = increment - delta.seconds % increment
        # are we on an exact multiple of the increment?
        if diff == increment:
            return stop
        return stop + timedelta(seconds=diff)

    diff = delta.seconds % increment
    return stop - timedelta(seconds=diff)
