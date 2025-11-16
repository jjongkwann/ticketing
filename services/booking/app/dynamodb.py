import boto3
from botocore.exceptions import ClientError
import os
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DynamoDBRepository:
    """DynamoDB repository for bookings"""

    def __init__(self):
        self.client = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.table_name = os.getenv('DYNAMODB_BOOKINGS_TABLE', 'ticketing-bookings-prod')

    async def create_booking(self, booking_data: dict) -> dict:
        """Create a booking in DynamoDB"""
        try:
            item = {
                'booking_id': {'S': booking_data['booking_id']},
                'event_id': {'S': booking_data['event_id']},
                'seat_number': {'S': booking_data['seat_number']},
                'user_id': {'S': booking_data['user_id']},
                'status': {'S': booking_data['status']},
                'price': {'N': str(booking_data['price'])},
                'created_at': {'N': str(int(datetime.utcnow().timestamp()))},
            }

            if 'reservation_id' in booking_data:
                item['reservation_id'] = {'S': booking_data['reservation_id']}

            if 'payment_id' in booking_data:
                item['payment_id'] = {'S': booking_data['payment_id']}

            if 'confirmed_at' in booking_data:
                item['confirmed_at'] = {'N': str(int(booking_data['confirmed_at'].timestamp()))}

            self.client.put_item(
                TableName=self.table_name,
                Item=item
            )

            return booking_data

        except ClientError as e:
            logger.error(f"Failed to create booking: {e}")
            raise

    async def get_booking(self, booking_id: str) -> Optional[dict]:
        """Get booking by ID"""
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={'booking_id': {'S': booking_id}}
            )

            if 'Item' not in response:
                return None

            return self._deserialize_item(response['Item'])

        except ClientError as e:
            logger.error(f"Failed to get booking: {e}")
            raise

    async def update_booking_status(self, booking_id: str, status: str, payment_id: Optional[str] = None) -> dict:
        """Update booking status"""
        try:
            update_expression = "SET #status = :status, confirmed_at = :confirmed_at"
            expression_values = {
                ':status': {'S': status},
                ':confirmed_at': {'N': str(int(datetime.utcnow().timestamp()))}
            }

            if payment_id:
                update_expression += ", payment_id = :payment_id"
                expression_values[':payment_id'] = {'S': payment_id}

            self.client.update_item(
                TableName=self.table_name,
                Key={'booking_id': {'S': booking_id}},
                UpdateExpression=update_expression,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=expression_values
            )

            return await self.get_booking(booking_id)

        except ClientError as e:
            logger.error(f"Failed to update booking: {e}")
            raise

    async def list_user_bookings(self, user_id: str) -> List[dict]:
        """List bookings for a user (using GSI)"""
        try:
            response = self.client.query(
                TableName=self.table_name,
                IndexName='user-index',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={
                    ':user_id': {'S': user_id}
                }
            )

            return [self._deserialize_item(item) for item in response.get('Items', [])]

        except ClientError as e:
            logger.error(f"Failed to list user bookings: {e}")
            raise

    def _deserialize_item(self, item: dict) -> dict:
        """Convert DynamoDB item to dict"""
        return {
            'booking_id': item['booking_id']['S'],
            'event_id': item['event_id']['S'],
            'seat_number': item['seat_number']['S'],
            'user_id': item['user_id']['S'],
            'status': item['status']['S'],
            'price': float(item['price']['N']),
            'reservation_id': item.get('reservation_id', {}).get('S'),
            'payment_id': item.get('payment_id', {}).get('S'),
            'created_at': datetime.fromtimestamp(int(item['created_at']['N'])),
            'confirmed_at': datetime.fromtimestamp(int(item['confirmed_at']['N'])) if 'confirmed_at' in item else None,
        }


# Global instance
_dynamodb_repo: Optional[DynamoDBRepository] = None


def get_dynamodb_repo() -> DynamoDBRepository:
    """Get DynamoDB repository instance"""
    global _dynamodb_repo

    if _dynamodb_repo is None:
        _dynamodb_repo = DynamoDBRepository()

    return _dynamodb_repo
