# Google cloud
from google.cloud import iam_admin_v1
from google.cloud import resourcemanager_v3
from google.cloud import bigquery
from google.iam.v1 import policy_pb2
from google.api_core.retry import Retry

# Settings
from django.conf import settings


class GoogleServiceAccount:
    @staticmethod
    def create_account(account_id: str):
        """
        Creates a service account

        Attributes
        ----------
        account_id: str
            should be 6 to 30 caracteres long and have to match this pattern
            [a-zA-Z][a-zA-Z\\d\\-]*[a-zA-Z\\d]
        """
        client = iam_admin_v1.IAMClient()
        request = iam_admin_v1.CreateServiceAccountRequest(
            name=f"projects/{settings.BQ_PROJECT_ID}", account_id=account_id
        )
        response = client.create_service_account(request=request)
        return response

    @staticmethod
    def create_key(unique_id: str):
        """
        Creates a service account access key

        Attributes
        ----------
        unique_id: str
            unique id from the service account
        """
        client = iam_admin_v1.IAMClient()
        request = iam_admin_v1.CreateServiceAccountKeyRequest(
            name=f"projects/{settings.BQ_PROJECT_ID}/serviceAccounts/{unique_id}",
        )
        # needed because sometimes the account creation is not
        # ready when this function is called
        retry_strategy = Retry(
            initial=1.0,
            maximum=60.0,
            multiplier=2.0,
            deadline=10.0,
        )
        response = client.create_service_account_key(
            request=request, retry=retry_strategy
        )
        return response


class GoogleRole:

    @staticmethod
    def assign_user_rol(account_email: str):
        client = resourcemanager_v3.ProjectsClient()

        project_name = f"projects/{settings.BQ_PROJECT_ID}"
        policy = client.get_iam_policy(request={"resource": project_name})

        role = "roles/bigquery.jobUser"
        member = f"serviceAccount:{account_email}"

        policy.bindings.append(policy_pb2.Binding(role=role, members=[member]))
        updated_policy = client.set_iam_policy(
            request={"resource": project_name, "policy": policy}
        )

        return updated_policy

    @staticmethod
    def assign_table_role(table_id: str, account_email: str):
        """
        Assing private table role

        Attributes
        ----------
        table_id: str
            Must be the full table path in this format project.dataset.table_id
        account_email: str
            Service account generated email
        """
        client = bigquery.Client(project=settings.BQ_PROJECT_ID)

        policy = client.get_iam_policy(table_id)
        role = "roles/bigquery.dataOwner"
        member = f"serviceAccount:{account_email}"

        policy.bindings.append(dict(role=role, members=[member]))
        updated_policy = client.set_iam_policy(table_id, policy)

        return updated_policy
