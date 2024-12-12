import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from django.conf import settings
from django.template import Template, Context

from api.datasets.exceptions import EmailException


class SendgridSender:
    client = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

    @classmethod
    def send_mail(cls, emails: list[str], subject: str, html_content: str):
        message = Mail(
            from_email=settings.SENDGRID_SENDER,
            to_emails=emails,
            subject=subject,
            html_content=html_content)

        try:
            cls.client.send(message)
        except Exception as e:
            raise EmailException(error=e)


def validate_data_fields(data: dict, fields: list[str]):
    for field in fields:
        assert field in data, f"{field} is a required field" 

    
def send_template_email(
        template_file: str, data: dict, subject: str, emails: list[str]):
    template_string = get_template(template_file) 
    template = Template(template_string)
    context = Context(data)
    html_content = template.render(context)

    sender = SendgridSender()
    sender.send_mail(emails, subject, html_content)


def send_private_data_mail(
        data:dict, emails: list[str], locale: str = "en"):

    validate_data_fields(
        data, 
        ["first_name", "email", "phone_number", 
        "reason", "industry", "share_data", "pay_for_access"])

    template_file =f"private_data_{locale}.html"
    subject = "Private data"
    send_template_email(template_file, data, subject, emails)


def send_change_password_mail(
        data:dict, emails: list, locale: str = "en"):

    validate_data_fields(data, ["email", "url"])

    template_file = f"change_password_{locale}.html"    
    subject = "Change password"
    send_template_email(template_file, data, subject, emails)


def send_activate_account_mail(
        data:dict, emails: list, locale: str = "en"):

    validate_data_fields(data, ["url"])

    template_file =f"activate_account_{locale}.html"    
    subject = "Activate account"
    send_template_email(template_file, data, subject, emails)


def get_template(filename: str):
    content = ""
    with open(f"/app/api/datasets/templates/{filename}") as file:
        content = file.read()

    return content

