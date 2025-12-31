"""Unit tests for CostNotificationService business logic."""
import pytest
from unittest.mock import Mock
from lambda_function import (
    CostNotificationService,
    BillingInfo,
    LineCredentials,
    CostCalculatorBase,
    TokenRepositoryBase,
    MessageFormatterBase,
    LineNotifier
)


@pytest.mark.unit
class TestCostNotificationService:
    """Tests for CostNotificationService business logic."""

    def test_notify_success_flow(self, mocker):
        """Test successful notification flow."""
        # Arrange
        mock_calculator = Mock(spec=CostCalculatorBase)
        mock_calculator.get_billing_info.return_value = BillingInfo(
            start='2025-11-01',
            end='2025-11-22',
            amount=123.456
        )
        
        mock_repository = Mock(spec=TokenRepositoryBase)
        mock_repository.get_credentials.return_value = LineCredentials(
            channel_id='test_channel',
            access_token='test_token'
        )
        
        mock_formatter = Mock(spec=MessageFormatterBase)
        mock_formatter.format.return_value = 'テストメッセージ'
        
        # LineNotifier.sendをモック
        mock_send = mocker.patch.object(LineNotifier, 'send', return_value=True)
        
        service = CostNotificationService(
            cost_calculator=mock_calculator,
            token_repository=mock_repository,
            message_formatter=mock_formatter
        )
        
        # Act
        result = service.notify()
        
        # Assert
        assert result is True
        mock_calculator.get_billing_info.assert_called_once()
        mock_formatter.format.assert_called_once()
        mock_repository.get_credentials.assert_called_once()
        mock_send.assert_called_once_with('テストメッセージ')

    def test_notify_fails_when_billing_info_is_none(self):
        """Test failure when billing info is None."""
        mock_calculator = Mock(spec=CostCalculatorBase)
        mock_calculator.get_billing_info.return_value = None
        
        mock_repository = Mock(spec=TokenRepositoryBase)
        mock_formatter = Mock(spec=MessageFormatterBase)
        
        service = CostNotificationService(
            cost_calculator=mock_calculator,
            token_repository=mock_repository,
            message_formatter=mock_formatter
        )
        
        result = service.notify()
        
        assert result is False
        mock_calculator.get_billing_info.assert_called_once()
        mock_formatter.format.assert_not_called()
        mock_repository.get_credentials.assert_not_called()

    def test_notify_fails_when_message_is_empty(self):
        """Test failure when message is empty."""
        mock_calculator = Mock(spec=CostCalculatorBase)
        mock_calculator.get_billing_info.return_value = BillingInfo(
            start='2025-11-01',
            end='2025-11-22',
            amount=123.456
        )
        
        mock_repository = Mock(spec=TokenRepositoryBase)
        
        mock_formatter = Mock(spec=MessageFormatterBase)
        mock_formatter.format.return_value = ""
        
        service = CostNotificationService(
            cost_calculator=mock_calculator,
            token_repository=mock_repository,
            message_formatter=mock_formatter
        )
        
        result = service.notify()
        
        assert result is False
        mock_calculator.get_billing_info.assert_called_once()
        mock_formatter.format.assert_called_once()
        mock_repository.get_credentials.assert_not_called()

    def test_notify_fails_when_credentials_is_none(self):
        """Test failure when credentials are None."""
        mock_calculator = Mock(spec=CostCalculatorBase)
        mock_calculator.get_billing_info.return_value = BillingInfo(
            start='2025-11-01',
            end='2025-11-22',
            amount=123.456
        )
        
        mock_repository = Mock(spec=TokenRepositoryBase)
        mock_repository.get_credentials.return_value = None
        
        mock_formatter = Mock(spec=MessageFormatterBase)
        mock_formatter.format.return_value = 'テストメッセージ'
        
        service = CostNotificationService(
            cost_calculator=mock_calculator,
            token_repository=mock_repository,
            message_formatter=mock_formatter
        )
        
        result = service.notify()
        
        assert result is False
        mock_repository.get_credentials.assert_called_once()

    def test_notify_fails_when_line_notifier_fails(self, mocker):
        """Test failure when LINE notification fails."""
        mock_calculator = Mock(spec=CostCalculatorBase)
        mock_calculator.get_billing_info.return_value = BillingInfo(
            start='2025-11-01',
            end='2025-11-22',
            amount=123.456
        )
        
        mock_repository = Mock(spec=TokenRepositoryBase)
        mock_repository.get_credentials.return_value = LineCredentials(
            channel_id='test_channel',
            access_token='test_token'
        )
        
        mock_formatter = Mock(spec=MessageFormatterBase)
        mock_formatter.format.return_value = 'テストメッセージ'
        
        # LineNotifier.send fails
        mocker.patch.object(LineNotifier, 'send', return_value=False)
        
        service = CostNotificationService(
            cost_calculator=mock_calculator,
            token_repository=mock_repository,
            message_formatter=mock_formatter
        )
        
        result = service.notify()
        
        assert result is False

    def test_notify_with_zero_amount(self, mocker):
        """Test edge case with zero billing amount."""
        mock_calculator = Mock(spec=CostCalculatorBase)
        mock_calculator.get_billing_info.return_value = BillingInfo(
            start='2025-11-01',
            end='2025-11-22',
            amount=0.0
        )
        
        mock_repository = Mock(spec=TokenRepositoryBase)
        mock_repository.get_credentials.return_value = LineCredentials(
            channel_id='test_channel',
            access_token='test_token'
        )
        
        mock_formatter = Mock(spec=MessageFormatterBase)
        mock_formatter.format.return_value = '請求額は0円です'
        
        mocker.patch.object(LineNotifier, 'send', return_value=True)
        
        service = CostNotificationService(
            cost_calculator=mock_calculator,
            token_repository=mock_repository,
            message_formatter=mock_formatter
        )
        
        result = service.notify()
        
        assert result is True
        # Verify zero amount is handled correctly
        mock_formatter.format.assert_called_once()
