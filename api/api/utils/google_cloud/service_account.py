import json

from google.oauth2 import service_account

from api.users.models import User


def get_account_credentials(user: User):
    account = user.service_account
    content = json.loads(account.key.private_key_data)
    credentials = service_account.Credentials.from_service_account_info(content)
    return credentials
