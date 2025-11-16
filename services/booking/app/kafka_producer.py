from aiokafka import AIOKafkaProducer
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Kafka producer for publishing booking events"""

    def __init__(self):
        self.bootstrap_servers = os.getenv('MSK_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        """Start Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            self.producer = None

    async def stop(self):
        """Stop Kafka producer"""
        if self.producer:
            await self.producer.stop()

    async def publish_event(self, topic: str, event: dict):
        """Publish event to Kafka"""
        if not self.producer:
            logger.warning("Kafka producer not available, skipping event publish")
            return

        try:
            await self.producer.send_and_wait(topic, event)
            logger.info(f"Published event to {topic}: {event.get('event_type')}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    async def publish_booking_created(self, booking: dict):
        """Publish booking created event"""
        event = {
            'event_type': 'booking.created',
            'booking_id': booking['booking_id'],
            'event_id': booking['event_id'],
            'user_id': booking['user_id'],
            'seat_number': booking['seat_number'],
            'timestamp': booking['created_at'].isoformat()
        }
        await self.publish_event('booking.created', event)

    async def publish_booking_confirmed(self, booking: dict):
        """Publish booking confirmed event"""
        event = {
            'event_type': 'booking.confirmed',
            'booking_id': booking['booking_id'],
            'payment_id': booking.get('payment_id'),
            'user_id': booking['user_id'],
            'timestamp': booking.get('confirmed_at', booking['created_at']).isoformat()
        }
        await self.publish_event('booking.confirmed', event)


# Global instance
_kafka_producer: Optional[KafkaProducer] = None


def get_kafka_producer() -> KafkaProducer:
    """Get Kafka producer instance"""
    global _kafka_producer

    if _kafka_producer is None:
        _kafka_producer = KafkaProducer()

    return _kafka_producer
