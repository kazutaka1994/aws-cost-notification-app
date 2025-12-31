"""Unit tests for DateHelper date range calculation logic."""
import pytest
from freezegun import freeze_time

from lambda_function import DateHelper


@pytest.mark.unit
class TestDateHelper:
    """Tests for DateHelper date range calculation."""

    @freeze_time("2025-11-21")
    def test_get_date_range_normal(self):
        """Test normal date range (mid-month)."""
        start, end = DateHelper.get_date_range()
        assert start == '2025-11-01'
        assert end == '2025-11-21'

    @freeze_time("2025-11-01")
    def test_get_date_range_on_first_day(self):
        """Test first day of month returns previous month."""
        start, end = DateHelper.get_date_range()
        assert start == '2025-10-01'
        assert end == '2025-11-01'

    @freeze_time("2025-01-01")
    def test_get_date_range_on_january_first(self):
        """Test January 1st returns previous year December."""
        start, end = DateHelper.get_date_range()
        assert start == '2024-12-01'
        assert end == '2025-01-01'

    @freeze_time("2025-11-30")
    def test_get_date_range_on_month_end(self):
        """Test last day of month."""
        start, end = DateHelper.get_date_range()
        assert start == '2025-11-01'
        assert end == '2025-11-30'

    @freeze_time("2025-02-28")
    def test_get_date_range_february_non_leap_year(self):
        """Test February end in non-leap year."""
        start, end = DateHelper.get_date_range()
        assert start == '2025-02-01'
        assert end == '2025-02-28'

    @freeze_time("2024-02-29")
    def test_get_date_range_february_leap_year(self):
        """Test February end in leap year."""
        start, end = DateHelper.get_date_range()
        assert start == '2024-02-01'
        assert end == '2024-02-29'
