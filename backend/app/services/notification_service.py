"""
Notification service for email and SMS alerts on status changes.

Requirements: 4.3, 4.4, 5.4
"""
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications.
    In production: integrates with SMTP and Twilio.
    Currently stubs that log notifications for testability.
    """

    def __init__(self):
        self.sent_notifications: List[dict] = []

    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send email notification. Returns True on success."""
        try:
            logger.info("Email to=%s subject=%s", to, subject)
            self.sent_notifications.append({
                "type": "email",
                "to": to,
                "subject": subject,
                "body": body,
            })
            return True
        except Exception as e:
            logger.error("Email failed to=%s: %s", to, e)
            return False

    def send_sms(self, to: str, message: str) -> bool:
        """Send SMS notification. Returns True on success."""
        try:
            logger.info("SMS to=%s", to)
            self.sent_notifications.append({
                "type": "sms",
                "to": to,
                "message": message,
            })
            return True
        except Exception as e:
            logger.error("SMS failed to=%s: %s", to, e)
            return False

    def notify_status_change(
        self,
        report_id: str,
        new_status: str,
        submitter_email: str,
        submitter_phone: Optional[str],
        upvoter_emails: Optional[List[str]] = None,
        upvoter_phones: Optional[List[str]] = None,
    ) -> None:
        """
        Send notifications to report submitter and upvoters on status change.
        Property 13: Status Change Notifications
        Requirements: 4.3, 4.4, 5.4
        """
        subject = f"CivicPulse: Report status updated to {new_status}"
        body = f"Your report {report_id} has been updated to: {new_status}"

        # Notify submitter
        self.send_email(submitter_email, subject, body)
        if submitter_phone:
            self.send_sms(submitter_phone, body)

        # Notify upvoters (Req 5.4)
        if upvoter_emails:
            for email in upvoter_emails:
                self.send_email(email, subject, body)
        if upvoter_phones:
            for phone in upvoter_phones:
                self.send_sms(phone, body)
