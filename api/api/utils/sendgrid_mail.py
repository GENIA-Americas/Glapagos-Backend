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
            EmailException(error=e)


def send_private_data_mail(
        data:dict, emails: list):

    template_string = get_template("private_data.html") 
    template = Template(template_string)
    context = Context(data)
    html_content = template.render(context)

    sender = SendgridSender()
    subject = "Private access data"
    sender.send_mail(emails, subject, html_content)


def get_template(filename: str):
    content = ""
    with open(f"/app/api/datasets/templates/{filename}") as file:
        content = file.read()

    return content

