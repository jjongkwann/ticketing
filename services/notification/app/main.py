from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, EmailStr
import boto3
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service", version="1.0.0")

# AWS clients
ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-east-1'))
sns_client = boto3.client('sns', region_name=os.getenv('AWS_REGION', 'us-east-1'))

class EmailNotification(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    is_html: bool = False

class SMSNotification(BaseModel):
    phone_number: str
    message: str

async def send_email(notification: EmailNotification):
    """SES로 이메일 발송"""
    try:
        response = ses_client.send_email(
            Source=os.getenv('SES_FROM_EMAIL', 'noreply@ticketing.com'),
            Destination={'ToAddresses': [notification.to_email]},
            Message={
                'Subject': {'Data': notification.subject},
                'Body': {
                    'Html': {'Data': notification.body} if notification.is_html else {},
                    'Text': {'Data': notification.body} if not notification.is_html else {}
                }
            }
        )
        logger.info(f"Email sent to {notification.to_email}: {response['MessageId']}")
        return {"success": True, "message_id": response['MessageId']}
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"success": False, "error": str(e)}

async def send_sms(notification: SMSNotification):
    """SNS로 SMS 발송"""
    try:
        response = sns_client.publish(
            PhoneNumber=notification.phone_number,
            Message=notification.message
        )
        logger.info(f"SMS sent to {notification.phone_number}: {response['MessageId']}")
        return {"success": True, "message_id": response['MessageId']}
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return {"success": False, "error": str(e)}

@app.post("/notifications/email")
async def notify_email(notification: EmailNotification, background_tasks: BackgroundTasks):
    """이메일 알림 발송"""
    background_tasks.add_task(send_email, notification)
    return {"status": "queued", "type": "email"}

@app.post("/notifications/sms")
async def notify_sms(notification: SMSNotification, background_tasks: BackgroundTasks):
    """SMS 알림 발송"""
    background_tasks.add_task(send_sms, notification)
    return {"status": "queued", "type": "sms"}

@app.post("/notifications/booking-confirmed")
async def notify_booking_confirmed(booking_id: str, user_email: EmailStr, event_title: str, background_tasks: BackgroundTasks):
    """예약 확정 알림"""
    notification = EmailNotification(
        to_email=user_email,
        subject=f"예약 확정: {event_title}",
        body=f"예약이 확정되었습니다.\n\n예약 ID: {booking_id}\n이벤트: {event_title}\n\n감사합니다!",
        is_html=False
    )
    background_tasks.add_task(send_email, notification)
    return {"status": "queued"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification-service", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    return {"service": "Notification Service", "version": "1.0.0"}
