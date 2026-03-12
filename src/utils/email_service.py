"""
Email Service for Investment Scout

Delivers newsletters and trading alerts via SendGrid with retry logic.
Implements exponential backoff retry strategy and delivery time constraints.
"""

import logging
import time
from typing import List, Optional
from datetime import datetime, time as dt_time
import pytz
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from src.models.investment_scout_models import Newsletter, TradingAlert
from src.utils.credential_manager import CredentialManager


logger = logging.getLogger(__name__)


class EmailService:
    """
    Email delivery service using SendGrid free tier.
    
    Implements retry logic with exponential backoff (5s, 15s, 45s) and
    ensures newsletters are delivered before 9:00 AM ET and alerts within 30 seconds.
    """
    
    def __init__(self, credential_manager: CredentialManager):
        """
        Initialize email service.
        
        Args:
            credential_manager: Credential manager for API keys
        """
        self.credential_manager = credential_manager
        self.sendgrid_api_key = credential_manager.get_credential('sendgrid_api_key')
        self.from_email = credential_manager.get_credential('user_email')
        self.client = SendGridAPIClient(self.sendgrid_api_key)
        
        logger.info("EmailService initialized")
    
    def send_newsletter(
        self,
        html_content: str,
        plain_text_content: str,
        recipients: List[str],
        subject: str
    ) -> bool:
        """
        Send newsletter email with delivery before 9:00 AM ET requirement.
        
        Args:
            html_content: HTML formatted newsletter content
            plain_text_content: Plain text newsletter content
            recipients: List of recipient email addresses
            subject: Email subject line
            
        Returns:
            True if delivery successful, False otherwise
        """
        logger.info(f"Sending newsletter to {len(recipients)} recipients")
        
        # Check if we're within delivery window (before 9:00 AM ET)
        et_tz = pytz.timezone('US/Eastern')
        current_time_et = datetime.now(et_tz).time()
        deadline = dt_time(9, 0)  # 9:00 AM
        
        if current_time_et >= deadline:
            logger.warning(
                f"Newsletter delivery attempted after 9:00 AM ET deadline. "
                f"Current time: {current_time_et}"
            )
        
        # Send with retry logic
        success = self.send_with_retry(
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text_content,
            recipients=recipients,
            max_retries=3
        )
        
        if not success:
            # Send system alert if newsletter fails after all retries
            logger.critical("Newsletter delivery failed after all retries - sending system alert")
            self._send_system_alert(
                "Newsletter Delivery Failure",
                f"Failed to deliver newsletter to {len(recipients)} recipients after 3 retry attempts"
            )
        
        return success
    
    def send_alert(
        self,
        html_content: str,
        plain_text_content: str,
        recipients: List[str],
        subject: str
    ) -> bool:
        """
        Send trading alert email with 30-second delivery requirement.
        
        Args:
            html_content: HTML formatted alert content
            plain_text_content: Plain text alert content
            recipients: List of recipient email addresses
            subject: Email subject line
            
        Returns:
            True if delivery successful, False otherwise
        """
        start_time = time.time()
        logger.info(f"Sending trading alert to {len(recipients)} recipients")
        
        # Send with retry logic (fewer retries for time-sensitive alerts)
        success = self.send_with_retry(
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text_content,
            recipients=recipients,
            max_retries=3
        )
        
        elapsed_time = time.time() - start_time
        
        if elapsed_time > 30:
            logger.warning(
                f"Alert delivery took {elapsed_time:.2f} seconds, "
                f"exceeding 30-second requirement"
            )
        else:
            logger.info(f"Alert delivered in {elapsed_time:.2f} seconds")
        
        if not success:
            logger.error("Trading alert delivery failed after all retries")
        
        return success
    
    def send_with_retry(
        self,
        subject: str,
        html_content: str,
        plain_text_content: str,
        recipients: List[str],
        max_retries: int = 3
    ) -> bool:
        """
        Send email with exponential backoff retry logic.
        
        Retry delays: 5s, 15s, 45s
        
        Args:
            subject: Email subject line
            html_content: HTML email content
            plain_text_content: Plain text email content
            recipients: List of recipient email addresses
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            True if delivery successful, False if all retries exhausted
        """
        retry_delays = [5, 15, 45]  # Exponential backoff in seconds
        
        for attempt in range(max_retries + 1):
            try:
                # Log delivery attempt
                logger.info(
                    f"Email delivery attempt {attempt + 1}/{max_retries + 1}",
                    extra={
                        "attempt": attempt + 1,
                        "max_attempts": max_retries + 1,
                        "recipients_count": len(recipients),
                        "subject": subject
                    }
                )
                
                # Create message
                message = Mail(
                    from_email=Email(self.from_email),
                    to_emails=[To(email) for email in recipients],
                    subject=subject,
                    plain_text_content=Content("text/plain", plain_text_content),
                    html_content=Content("text/html", html_content)
                )
                
                # Send via SendGrid
                response = self.client.send(message)
                
                # Log successful delivery
                logger.info(
                    f"Email delivered successfully on attempt {attempt + 1}",
                    extra={
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                        "recipients_count": len(recipients)
                    }
                )
                
                return True
                
            except Exception as e:
                logger.error(
                    f"Email delivery attempt {attempt + 1} failed: {str(e)}",
                    extra={
                        "attempt": attempt + 1,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    },
                    exc_info=True
                )
                
                # If not the last attempt, wait before retrying
                if attempt < max_retries:
                    delay = retry_delays[attempt]
                    logger.info(f"Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                else:
                    # All retries exhausted
                    logger.error(
                        f"Email delivery failed after {max_retries + 1} attempts",
                        extra={
                            "total_attempts": max_retries + 1,
                            "final_error": str(e)
                        }
                    )
        
        return False
    
    def _send_system_alert(self, alert_title: str, alert_message: str) -> None:
        """
        Send system alert for critical failures.
        
        Args:
            alert_title: Alert title
            alert_message: Alert message
        """
        try:
            subject = f"🚨 Investment Scout System Alert: {alert_title}"
            
            html_content = f"""
            <html>
            <body>
                <h2 style="color: #d32f2f;">System Alert</h2>
                <h3>{alert_title}</h3>
                <p>{alert_message}</p>
                <p><strong>Timestamp:</strong> {datetime.now().isoformat()}</p>
            </body>
            </html>
            """
            
            plain_text_content = f"""
            SYSTEM ALERT
            
            {alert_title}
            
            {alert_message}
            
            Timestamp: {datetime.now().isoformat()}
            """
            
            # Send to system admin (using from_email as admin email)
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=[To(self.from_email)],
                subject=subject,
                plain_text_content=Content("text/plain", plain_text_content),
                html_content=Content("text/html", html_content)
            )
            
            self.client.send(message)
            logger.info(f"System alert sent: {alert_title}")
            
        except Exception as e:
            logger.error(f"Failed to send system alert: {str(e)}", exc_info=True)
