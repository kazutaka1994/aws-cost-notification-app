import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

import boto3
import requests
from aws_lambda_powertools import Logger
from boto3.dynamodb.types import TypeDeserializer

logger = Logger()

COST_METRICS_VALUE = os.getenv("COST_METRICS_VALUE")
LINE_API_URL = os.getenv("LINE_API_URL")
SETTINGS_TABLE = os.getenv("SETTINGS_TABLE")


# ========================
# Data Models
# ========================
@dataclass
class BillingInfo:
    start: str
    end: str
    amount: float


@dataclass
class LineCredentials:
    channel_id: str
    access_token: str


# ========================
# Interfaces
# ========================
class CostCalculatorBase(ABC):
    @abstractmethod
    def get_billing_info(self) -> Optional[BillingInfo]:
        pass


class TokenRepositoryBase(ABC):
    @abstractmethod
    def get_credentials(self) -> Optional[LineCredentials]:
        pass


class NotifierBase(ABC):
    @abstractmethod
    def send(self, message: str) -> bool:
        pass


class MessageFormatterBase(ABC):
    @abstractmethod
    def format(self, billing_info: BillingInfo) -> str:
        pass


# ========================
# Date Utility
# ========================
class DateHelper:
    
    @staticmethod
    def get_begin_of_month() -> str:
        return date.today().replace(day=1).isoformat()
    
    @staticmethod
    def get_today() -> str:
        return date.today().isoformat()
    
    @staticmethod
    def get_date_range() -> Tuple[str, str]:
        start_date = DateHelper.get_begin_of_month()
        end_date = DateHelper.get_today()

        if start_date == end_date:
            end_of_month = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=-1)
            begin_of_month = end_of_month.replace(day=1)
            return begin_of_month.date().isoformat(), end_date
        return start_date, end_date


# ========================
# Implementation Classes
# ========================
class AwsCostCalculator(CostCalculatorBase):
    
    def __init__(self, region: str = 'us-east-1'):
        self.client = boto3.client('ce', region_name=region)
        self.metrics_value = COST_METRICS_VALUE
    
    def get_billing_info(self) -> Optional[BillingInfo]:
        try:
            start_date, end_date = DateHelper.get_date_range()
            
            response = self.client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='MONTHLY',
                Metrics=[self.metrics_value]
            )
            
            result = response.get('ResultsByTime')[0]
            return BillingInfo(
                start=result['TimePeriod']['Start'],
                end=result['TimePeriod']['End'],
                amount=float(result['Total'][self.metrics_value]['Amount'])
            )
        except Exception as e:
            logger.exception(e)
            return None


class DynamoDbTokenRepository(TokenRepositoryBase):

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.client = boto3.client('dynamodb')
        self.deserializer = TypeDeserializer()

    def get_credentials(self) -> Optional[LineCredentials]:
        try:
            channel_id = self._get_value('line_channel_id')
            access_token = self._get_value('line_access_token')
            
            if channel_id and access_token:
                return LineCredentials(
                    channel_id=channel_id,
                    access_token=access_token
                )
            return None
        except Exception as e:
            logger.exception(e)
            return None
    
    def _get_value(self, key: str) -> Optional[str]:
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={'type': {'S': key}}
            )
            
            item = {
                k: self.deserializer.deserialize(v)
                for k, v in response['Item'].items()
            }
            return item.get('value')
        except Exception as e:
            logger.exception(e)
            return None


class BillingMessageFormatter(MessageFormatterBase):
    
    def format(self, billing_info: BillingInfo) -> str:
        try:
            start = datetime.strptime(billing_info.start, '%Y-%m-%d').strftime('%m/%d')
            end_today = datetime.strptime(billing_info.end, '%Y-%m-%d')
            end_yesterday = (end_today - timedelta(days=1)).strftime('%m/%d')
            
            total = round(billing_info.amount, 3)
            return f'{start}～{end_yesterday}の請求額は、{total:.3f} USDです。'
        except Exception as e:
            logger.exception(e)
            return ""


class LineNotifier(NotifierBase):

    def __init__(self, credentials: LineCredentials, api_url: str = LINE_API_URL):
        self.api_url = api_url
        self.credentials = credentials
    
    def send(self, message: str) -> bool:
        try:
            headers = {
                "Authorization": f"Bearer {self.credentials.access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "to": self.credentials.channel_id,
                "messages": [{"type": "text", "text": message}]
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                timeout=10,
                data=json.dumps(data)
            )
            logger.info(f'response: {response.json()}')
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.exception(e)
            return False


# ========================
# Application Service
# ========================
class CostNotificationService:
    
    def __init__(
        self,
        cost_calculator: CostCalculatorBase,
        token_repository: TokenRepositoryBase,
        message_formatter: MessageFormatterBase
    ):
        self.cost_calculator = cost_calculator
        self.token_repository = token_repository
        self.message_formatter = message_formatter
    
    def notify(self) -> bool:
        billing_info = self.cost_calculator.get_billing_info()
        if not billing_info:
            logger.error("Failed to get billing info")
            return False
        logger.info(f'billing_info: {billing_info}')
        
        message = self.message_formatter.format(billing_info)
        if not message:
            logger.error("Failed to format message")
            return False
        logger.info(f'message: {message}')

        credentials = self.token_repository.get_credentials()
        if not credentials:
            logger.error("Failed to get credentials")
            return False
        
        notifier = LineNotifier(credentials)
        success = notifier.send(message)
        logger.info(f'notification success: {success}')
        return success


# ========================
# Lambda Handler
# ========================
def lambda_handler(event, context) -> None:
    service = CostNotificationService(
        cost_calculator=AwsCostCalculator(),
        token_repository=DynamoDbTokenRepository(SETTINGS_TABLE),
        message_formatter=BillingMessageFormatter()
    )

    # 通知を実行
    service.notify()
