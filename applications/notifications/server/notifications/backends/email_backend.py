import smtplib

from cloudharness import log as logger
from cloudharness.utils.config import CloudharnessConfig as conf
from cloudharness.utils.secrets import get_secret, SecretNotFound
from email.message import EmailMessage
from notifications.backends.base_backend import NotificationBaseBackend


def get_secret_or_empty(name):
    try:
        return get_secret(name)
    except SecretNotFound:
        return ""


class NotificationEmailBackend(NotificationBaseBackend):
    def __init__(self, email_from=None, email_to=None, subject=None, message=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_from = email_from
        self.email_to = email_to
        self.subject = subject
        self.message = message

    def send(self):
        logger.info(f"Sending notification email to {self.email_to}")
        msg = EmailMessage()
        msg['Subject'] = self.subject
        msg['From'] = self.email_from
        msg['To'] = self.email_to
        msg.set_content(self.message, subtype='html')

        email_user = get_secret_or_empty('email-user')
        email_pass = get_secret_or_empty('email-password')
        email_host = conf.get_configuration()["smtp"]["host"]
        email_port = conf.get_configuration()["smtp"]["port"]
        email_tls = conf.get_configuration()["smtp"].get("use_tls")

        smtp = smtplib.SMTP(email_host, email_port)
        if email_user or email_pass:
            smtp.login(email_user, email_pass)
        if email_tls:
            smtp.starttls()
        smtp.send_message(msg)
