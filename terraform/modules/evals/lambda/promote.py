"""Promote a clean quarantine object and start its silver transcript task.

GuardDuty invokes this function once for each scanned object, through an EventBridge
rule. The function does not download the audio. S3 copies it from quarantine to assets.
"""

import json
import os

import boto3

s3 = boto3.client("s3")
sns = boto3.client("sns")
ecs = boto3.client("ecs")

QUARANTINE_BUCKET = os.environ["QUARANTINE_BUCKET"]
ASSETS_BUCKET = os.environ["ASSETS_BUCKET"]
KMS_KEY_ARN = os.environ["KMS_KEY_ARN"]
ALERT_TOPIC_ARN = os.environ["ALERT_TOPIC_ARN"]
ECS_CLUSTER = os.environ["ECS_CLUSTER"]
SILVER_TASK_DEFINITION = os.environ["SILVER_TASK_DEFINITION"]
SILVER_SUBNET_ID = os.environ["SILVER_SUBNET_ID"]
SILVER_SECURITY_GROUP_ID = os.environ["SILVER_SECURITY_GROUP_ID"]
SILVER_CONTAINER_NAME = os.environ["SILVER_CONTAINER_NAME"]


def handler(event, _context):
    """Copy a clean object to assets, or alert when the scan did not come back clean.

    The object key and version come from the GuardDuty event. The silver transcript
    task is started with that key, so it transcribes this recording and no other.
    The quarantine version is deleted last. If the copy or the task start fails, the
    version is still in quarantine, so the automatic retry can repeat the whole
    sequence. Once the retries run out, the failure destination publishes an alert.
    """
    detail = event["detail"]
    scanned_object = detail["s3ObjectDetails"]
    object_key = scanned_object["objectKey"]
    version_id = scanned_object["versionId"]
    scan_result = detail["scanResultDetails"]["scanResultStatus"]

    if scan_result == "NO_THREATS_FOUND":
        copy_to_assets(object_key, version_id)
        start_silver_task(object_key)
        delete_quarantine_version(object_key, version_id)
        return

    alert(scan_result, object_key)


def copy_to_assets(object_key, version_id):
    """Copy one quarantine version into assets, encrypted with the evals key.

    The copy takes whatever tags the quarantine version has at that moment. GuardDuty
    may not have written its scan result tag yet, so nothing relies on that tag.
    A single copy request handles an object up to 5 GB, which is far above the length
    of a council meeting recording.
    """
    s3.copy_object(
        Bucket=ASSETS_BUCKET,
        Key=object_key,
        CopySource={"Bucket": QUARANTINE_BUCKET, "Key": object_key, "VersionId": version_id},
        ServerSideEncryption="aws:kms",
        SSEKMSKeyId=KMS_KEY_ARN,
        TaggingDirective="COPY",
    )


def delete_quarantine_version(object_key, version_id):
    """Permanently remove the scanned version from quarantine.

    Deleting by version id removes the bytes at once. It does not leave a delete
    marker or a noncurrent version. Other versions of the same key are not touched.
    """
    s3.delete_object(Bucket=QUARANTINE_BUCKET, Key=object_key, VersionId=version_id)


def start_silver_task(object_key):
    """Start the silver transcript task for this object key.

    The task definition is created by AIILG-1305 under the family named in the
    environment. A response that lists failures means the task did not start.
    """
    response = ecs.run_task(
        cluster=ECS_CLUSTER,
        taskDefinition=SILVER_TASK_DEFINITION,
        launchType="FARGATE",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": [SILVER_SUBNET_ID],
                "securityGroups": [SILVER_SECURITY_GROUP_ID],
                "assignPublicIp": "DISABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": SILVER_CONTAINER_NAME,
                    "environment": [{"name": "RECORDING_OBJECT_KEY", "value": object_key}],
                }
            ]
        },
    )
    if response["failures"]:
        raise RuntimeError(response["failures"])


def alert(scan_result, object_key):
    """Publish the scan result and the object key. The object stays in quarantine."""
    sns.publish(
        TopicArn=ALERT_TOPIC_ARN,
        Subject=f"Evals quarantine scan: {scan_result}",
        Message=json.dumps({"scan_result": scan_result, "object_key": object_key}),
    )
