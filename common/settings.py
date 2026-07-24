import logging
from typing import Literal

import dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

DOT_ENV_PATH = ".env"

dotenv_detected = dotenv.load_dotenv(dotenv_path=DOT_ENV_PATH)
if dotenv_detected:
    logger.info("A .env file was detected and loaded. Values from it will override environment variables")
else:
    logger.info("No .env file was detected. Using environment variables as is")


class Settings(BaseSettings):
    POSTGRES_HOST: str = Field(description="PostgreSQL database host")
    POSTGRES_PORT: int = Field(description="PostgreSQL database port")
    POSTGRES_DB: str = Field(description="PostgreSQL database name")
    POSTGRES_USER: str | None = Field(description="PostgreSQL database user", default=None)
    POSTGRES_PASSWORD: str | None = Field(description="PostgreSQL database password", default=None)
    RDS_CA_BUNDLE_PATH: str = Field(
        description="Path to the Amazon RDS CA certificate bundle",
        default="/app/config/rds-ca-bundle.pem",
    )
    DB_SECRET_ARN: str | None = Field(
        description="Arn of secret which contains the current database credentials", default=None
    )

    APP_URL: str = Field(description="used for CORS origin validation")

    # if using AWS
    AWS_ACCOUNT_ID: str | None = Field(description="AWS account ID", default=None)
    AWS_REGION: str | None = Field(description="AWS region", default=None)
    ALB_ARN: str | None = Field(description="ARN of the ALB, used to validate the JWT signer claim", default=None)
    OIDC_ISSUER: str | None = Field(description="OIDC issuer URL, used to validate the JWT issuer claim", default=None)
    OIDC_CLIENT_ID: str | None = Field(
        description="OIDC client ID, used to validate the JWT audience claim", default=None
    )

    ENVIRONMENT: str = "local"
    SENTRY_DSN: str | None = Field(description="Sentry DSN if using Sentry for telemetry", default=None)

    TRANSCRIPTION_QUEUE_NAME: str = Field(description="queue name to use for SQS/Azure Service Bus queues")
    TRANSCRIPTION_DEADLETTER_QUEUE_NAME: str = Field(
        description="deadletter queue name to use for SQS. Ignored if using Azure Service Bus "
    )
    LLM_QUEUE_NAME: str = Field(description="queue name to use for SQS/Azure Service Bus queues")
    LLM_DEADLETTER_QUEUE_NAME: str = Field(
        description="deadletter queue name to use for SQS. Ignored if using Azure Service Bus "
    )

    MAX_TRANSCRIPTION_PROCESSES: int = Field(description="the number of transcription workers per node", default=1)
    MAX_LLM_PROCESSES: int = Field(description="the number of LLM workers per node", default=1)

    # if using Azure OpenAI
    AZURE_DEPLOYMENT: str | None = Field(description="Azure deployment for openAI", default=None)
    AZURE_OPENAI_API_KEY: str | None = Field(description="Azure API key for openAI", default=None)
    AZURE_OPENAI_ENDPOINT: str | None = Field(description="Azure OpenAI service endpoint URL", default=None)
    AZURE_OPENAI_API_VERSION: str | None = Field(description="Azure OpenAI API version", default=None)
    AZURE_AUDIO_DEPLOYMENT: str | None = Field(description="Azure deployment for audio (Whisper)", default=None)

    # if using Azure APIM
    AZURE_APIM_URL: str | None = Field(description="Base URL for Minute's Azure APIM LLM.", default=None)
    AZURE_APIM_API_VERSION: str | None = Field(description="Azure APIM API version, <yyyy-mm-dd>", default=None)
    AZURE_APIM_SUBSCRIPTION_KEY: str | None = Field(description="Subscription key for Azure APIM", default=None)
    AZURE_APIM_AUTH_METHOD: Literal["client_secret", "static_token"] | None = Field(
        description="APIM auth method: 'client_secret' or 'static_token'", default=None
    )
    # if using 'client_secret' for AZURE_APIM_AUTH_METHOD
    AZURE_APIM_TENANT_ID: str | None = Field(description="Azure tenant ID for APIM client secret auth", default=None)
    AZURE_APIM_CLIENT_ID: str | None = Field(description="Azure client ID for APIM client secret auth", default=None)
    AZURE_APIM_CLIENT_SECRET: str | None = Field(
        description="Azure client secret for APIM client secret auth", default=None
    )
    AZURE_APIM_SCOPE: str | None = Field(description="OAuth scope for APIM client secret auth", default=None)
    # if using 'static_token' for AZURE_APIM_AUTH_METHOD
    AZURE_APIM_ACCESS_TOKEN: str | None = Field(description="Access token for Azure APIM", default=None)
    # if using Gemini
    GOOGLE_APPLICATION_CREDENTIALS: str | None = Field(
        description="Path to Google Cloud service account credentials JSON file", default=None
    )
    GOOGLE_CLOUD_PROJECT: str | None = Field(description="Google Cloud project ID", default=None)
    GOOGLE_CLOUD_LOCATION: str | None = Field(description="Google Cloud region/location", default=None)

    # ELASTICMQ for development
    USE_ELASTICMQ: bool = Field(description="Use ElasticMQ for local AWS SQS emulation in dev", default=True)
    ELASTICMQ_URL: str = Field(
        description="ELASTICMQ service URL for local AWS services emulation", default="http://localhost:9324"
    )

    TRANSCRIPTION_SERVICES: list[str] = Field(
        description="List of service names to use for transcription. See backend/services/transcription_services",
        default_factory=list,
    )

    FAST_LLM_PROVIDER: str = Field(
        description="Fast LLM provider to use. Currently 'openai', 'azure_apim', and 'gemini' are supported. Note that "
        "this should be used for low complexity LLM tasks, like AI edits.",
        default="azure_apim",
    )
    FAST_LLM_MODEL_NAME: str = Field(
        description="Fast LLM model name to use. Note that this should be used for low complexity LLM tasks.",
        default="gpt-5-nano",
    )
    BEST_LLM_PROVIDER: str = Field(
        description="Best LLM provider to use. Currently 'openai', 'azure_apim', and 'gemini' are supported. Note that "
        "this should be used for higher complexity LLM tasks, like initial minute generation.",
        default="azure_apim",
    )
    BEST_LLM_MODEL_NAME: str = Field(
        description="Best LLM model name to use. Note that this should be used for higher complexity LLM tasks, like "
        "initial minute generation.",
        default="gpt5-1",
    )

    STORAGE_SERVICE_NAME: str = Field(
        description="Storage service type to use for file uploads. Currently supported are: s3, azure-blob",
        default="s3",
    )
    # if using s3
    DATA_S3_BUCKET: str | None = Field(description="S3 bucket name for data storage", default=None)
    # if using Azure blob
    AZURE_BLOB_CONNECTION_STRING: str | None = Field(description="Azure Blob Storage connection string", default=None)
    AZURE_UPLOADS_CONTAINER_NAME: str | None = Field(
        description="Azure container name for uploaded files", default=None
    )
    # if using azure_stt_batch
    AZURE_TRANSCRIPTION_CONTAINER_NAME: str | None = Field(
        description="Azure container name for transcription result files. Note that Azure Batch transcription requires "
        "this.",
        default=None,
    )
    # Evals summarisation blob storage (Entra ID auth, no account key).
    AZURE_EVALS_STORAGE_ACCOUNT_URL: str | None = Field(
        description="Blob endpoint of the evals storage account, e.g. https://<account>.blob.core.windows.net",
        default=None,
    )

    QUEUE_SERVICE_NAME: str = Field(
        description="Queue service type to communicate with worker. Currently supported are: sqs, azure-service-bus",
        default="sqs",
    )
    # if using azure-service-bus
    AZURE_SB_CONNECTION_STRING: str | None = Field(description="Azure service bus connection string", default=None)

    EMAIL_SERVICE: Literal["local", "gov_notify"] = Field(
        description="An emailing service provider. Supports either 'local' or 'gov_notify'.", default="local"
    )

    # if using gov notify
    GOVNOTIFY_API_KEY: str | None = Field(
        description="Generate a key for this project on the GovNotify website.", default=None
    )
    GOVNOTIFY_INVITE_TEMPLATE_ID: str | None = Field(
        description="Use the GovNotify website to create an email template and copy in the template ID.", default=None
    )

    @model_validator(mode="after")
    def validate_govnotify(self) -> "Settings":
        if self.EMAIL_SERVICE == "gov_notify":
            if not self.GOVNOTIFY_API_KEY:
                error_text = "GOVNOTIFY_API_KEY must be set when EMAIL_SERVICE='gov_notify'"
                raise ValueError(error_text)
            if not self.GOVNOTIFY_INVITE_TEMPLATE_ID:
                error_text = "GOVNOTIFY_INVITE_TEMPLATE_ID must be set when EMAIL_SERVICE='gov_notify'"
                raise ValueError(error_text)
        return self

    # if running the worker inside a docker container (use "0.0.0.0" )
    RAY_DASHBOARD_HOST: str = Field(description="Ray dashboard host IP address", default="127.0.0.1")

    BETA_TEMPLATE_NAMES: list[str] = Field(
        description="List of template names available in beta. These are currently made available via a Posthog feature"
        " flag",
        default_factory=list,
    )

    # if using posthog
    POSTHOG_API_KEY: str | None = Field(description="PostHog API key for analytics", default=None)
    POSTHOG_HOST: str = Field(description="PostHog service host URL", default="https://eu.i.posthog.com")

    GUARDRAIL_THRESHOLD: float = Field(
        default=0.7,
        description="Guardrail threshold for LLM responses",
    )

    MIN_WORD_COUNT_FOR_SUMMARY: int = Field(
        default=50,
        description="Transcript must have at least this many words to be passed to summary stage",
    )

    MIN_WORD_COUNT_FOR_FULL_SUMMARY: int = Field(
        default=200,
        description="Transcript must have at least this many words to be passed to full summary stage",
    )

    LOCAL_STORAGE_PATH: str = Field(
        default="/tmp",  # noqa: S108
        description="The folder where the data directory is mounted for the local storage service.",
    )
    LOCAL_STORAGE_BASE_URL: str = Field(
        default="http://localhost:8080",
        description="Browser-accessible backend URL for generating direct upload URLs in local storage.",
    )

    # use a dotenv file for local development
    if dotenv_detected:
        model_config = SettingsConfigDict(env_file=DOT_ENV_PATH, extra="ignore")


def get_settings() -> Settings:
    return Settings()  # type: ignore  # noqa: PGH003
