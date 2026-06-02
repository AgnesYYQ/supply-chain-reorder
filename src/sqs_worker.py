import json
import logging
import os
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.multi_agent_supply_chain import MultiAgentSupplyChain


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def build_initial_state(message_body: str) -> dict:
    state = {"decision_log": []}

    try:
        payload = json.loads(message_body)
    except json.JSONDecodeError:
        logger.warning("Message is not valid JSON, using default state.")
        state["erp_alert"] = message_body
        return state

    if isinstance(payload, dict):
        for key in ["erp_alert", "sales_history", "lead_time"]:
            if key in payload:
                state[key] = payload[key]

    return state


def process_message(message: dict) -> bool:
    body = message.get("Body", "")
    state = build_initial_state(body)

    try:
        agent = MultiAgentSupplyChain()
        agent.state = state
        agent.run()
        logger.info("Agent run completed. Final state keys: %s", list(agent.state.keys()))
        return True
    except Exception:
        logger.exception("Agent run failed; leaving message in queue for retry.")
        return False


def main() -> None:
    queue_url = os.getenv("SQS_QUEUE_URL")
    if not queue_url:
        raise ValueError("SQS_QUEUE_URL is required.")

    aws_region = os.getenv("AWS_REGION", "us-east-1")
    wait_time = int(os.getenv("SQS_WAIT_TIME_SECONDS", "20"))
    visibility_timeout = int(os.getenv("SQS_VISIBILITY_TIMEOUT", "120"))
    max_messages = int(os.getenv("SQS_MAX_MESSAGES", "1"))
    sleep_seconds = int(os.getenv("SQS_IDLE_SLEEP_SECONDS", "2"))
    empty_backoff_base = int(os.getenv("SQS_EMPTY_BACKOFF_BASE_SECONDS", "1"))
    empty_backoff_max = int(os.getenv("SQS_EMPTY_BACKOFF_MAX_SECONDS", "30"))

    sqs = boto3.client("sqs", region_name=aws_region)

    logger.info("Starting SQS worker. Queue=%s Region=%s", queue_url, aws_region)
    empty_polls = 0

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time,
                VisibilityTimeout=visibility_timeout,
                MessageAttributeNames=["All"],
            )
        except (BotoCoreError, ClientError):
            logger.exception("Failed to receive message from SQS.")
            time.sleep(sleep_seconds)
            continue

        messages = response.get("Messages", [])
        if not messages:
            backoff = min(empty_backoff_max, empty_backoff_base * (2 ** empty_polls))
            logger.debug("No messages received. Sleeping %s seconds before next poll.", backoff)
            time.sleep(backoff)
            empty_polls += 1
            continue

        empty_polls = 0

        for message in messages:
            ok = process_message(message)
            if not ok:
                continue

            receipt_handle = message.get("ReceiptHandle")
            if not receipt_handle:
                logger.warning("No receipt handle on processed message; cannot delete.")
                continue

            try:
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                logger.info("Deleted processed message from queue.")
            except (BotoCoreError, ClientError):
                logger.exception("Failed to delete processed message from SQS.")


if __name__ == "__main__":
    main()
