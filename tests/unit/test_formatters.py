"""Unit tests for BillingMessageFormatter logic."""
import pytest
from lambda_function import BillingMessageFormatter, BillingInfo


@pytest.mark.unit
class TestBillingMessageFormatter:
    """Tests for BillingMessageFormatter message generation."""

    def test_format_normal_amount(self):
        """Test basic date and amount formatting."""
        formatter = BillingMessageFormatter()
        billing_info = BillingInfo(
            start='2025-11-01',
            end='2025-11-22',
            amount=123.456
        )
        
        result = formatter.format(billing_info)
        assert result == '11/01～11/21の請求額は、123.456 USDです。'

    def test_format_with_rounding(self):
        """Test rounding to 3 decimal places."""
        formatter = BillingMessageFormatter()
        billing_info = BillingInfo(
            start='2025-11-01',
            end='2025-11-15',
            amount=99.9999
        )
        
        result = formatter.format(billing_info)
        assert result == '11/01～11/14の請求額は、100.000 USDです。'

    def test_format_zero_amount(self):
        """Test edge case with zero amount."""
        formatter = BillingMessageFormatter()
        billing_info = BillingInfo(
            start='2025-11-01',
            end='2025-11-22',
            amount=0.0
        )
        
        result = formatter.format(billing_info)
        assert result == '11/01～11/21の請求額は、0.000 USDです。'

    def test_format_year_boundary(self):
        """Test date formatting across year boundary."""
        formatter = BillingMessageFormatter()
        billing_info = BillingInfo(
            start='2024-12-01',
            end='2025-01-01',
            amount=100.0
        )
        
        result = formatter.format(billing_info)
        assert result == '12/01～12/31の請求額は、100.000 USDです。'

    def test_format_invalid_date_format_returns_empty(self):
        """Test invalid date returns empty string."""
        formatter = BillingMessageFormatter()
        billing_info = BillingInfo(
            start='invalid-date',
            end='2025-11-22',
            amount=100.0
        )
        
        result = formatter.format(billing_info)
        assert result == ""
