# Google cloud
from google.cloud import iam_admin_v1
from google.cloud import resourcemanager_v3
from google.cloud import bigquery
from google.iam.v1 import policy_pb2
from google.api_core.retry import Retry
from google.api_core.exceptions import NotFound
from google.cloud.bigquery.enums import EntityTypes
from google.api_core.exceptions import InvalidArgument

# Settings
from django.conf import settings

from .big_query_service import BigQueryService
from api.users.exceptions import InvalidEmailAddressException, AssignRoleFailedException


class GoogleServiceAccount:
    @staticmethod
    def create_account(account_id: str):
        """
        Creates a service account

        Attributes
        ----------
        account_id: str
            should be 6 to 30 characters long and have to match this pattern
            [a-zA-Z][a-zA-Z\\d\\-]*[a-zA-Z\\d]
        """
        client = iam_admin_v1.IAMClient()
        request = iam_admin_v1.CreateServiceAccountRequest(
            name=f"projects/{settings.BQ_PROJECT_ID}", account_id=account_id
        )
        response = client.create_service_account(request=request)

        service_account_name = f"projects/{settings.BQ_PROJECT_ID}/serviceAccounts/{account_id}@{settings.BQ_PROJECT_ID}.iam.gserviceaccount.com"
        retry = Retry(
            predicate=lambda exc: isinstance(exc, NotFound),  # Retry only on NotFound errors
            initial=1.0,
            maximum=10.0,
            multiplier=2.0,
            deadline=120.0
        )

        @retry
        def wait_for_service_account():
            client.get_service_account(name=service_account_name)

        wait_for_service_account()
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
            maximum=20.0,
            multiplier=2.0,
            deadline=300.0,
        )
        response = client.create_service_account_key(
            request=request, retry=retry_strategy
        )
        return response


class GoogleRole:

    @staticmethod
    def assign_user_rol(account_email: str, role: str, member_type: str):
        try:
            client = resourcemanager_v3.ProjectsClient()

            project_name = f"projects/{settings.BQ_PROJECT_ID}"
            policy = client.get_iam_policy(request={"resource": project_name})

            member = f"{member_type}:{account_email}"

            retry_strategy = Retry(
                initial=1.0,
                maximum=20.0,
                multiplier=2.0,
                deadline=300.0,
            )

            policy.bindings.append(policy_pb2.Binding(role=role, members=[member]))
            updated_policy = client.set_iam_policy(
                request={"resource": project_name, "policy": policy},
                retry=retry_strategy
            )

            return updated_policy
        except InvalidArgument as exp:
            raise InvalidEmailAddressException(error=str(exp))
        except Exception as exp:
            raise AssignRoleFailedException(error=str(exp))

    @staticmethod
    def assign_table_role(table_id: str, account_email: str):
        """
        Assign private table role

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

    @staticmethod
    def assign_dataset_role(dataset_name: str, account_email: str, role: str):
        """
        Assign dataset role

        Attributes
        ----------
        dataset_name (str): Dataset name
        account_email (str): Service account generated email
        role (str): Role name. (OWNER | WRITER | READER)
        """
        dataset_id = f"{settings.BQ_PROJECT_ID}.{dataset_name}"

        entity_type = EntityTypes.USER_BY_EMAIL

        bigquery_service = BigQueryService(user=None)
        client = bigquery_service.create_bigquery_client(project_owner=True)

        dataset = client.get_dataset(dataset_id)

        entries = list(dataset.access_entries)
        entries.append(
            bigquery.AccessEntry(
                role=role,
                entity_type=entity_type,
                entity_id=account_email,
            )
        )
        dataset.access_entries = entries

        client.update_dataset(dataset, ["access_entries"])
