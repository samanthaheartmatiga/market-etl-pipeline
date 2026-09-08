import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")

STATUS_ICONS = {
    "SUCCESS": ":white_check_mark:",
    "DATA QUALITY WARNING": ":warning:",
    "CRITICAL FAILURE": ":rotating_light:"
}

def send_alert(status: str, message: str):
    """Sends structured alerts to Slack via Block Kit, falling back to console logging."""
    if not WEBHOOK_URL or "hooks.slack.com" not in WEBHOOK_URL:
        logging.info(f"[ALERT FALLBACK] {status}: {message}")
        return

    icon = STATUS_ICONS.get(status, ":information_source:")
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{icon} Pipeline Alert: {status}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "*Environment:* Production-Local | *Service:* Crypto Market ETL"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        response.raise_for_status()
    except Exception as err:
        logging.error(f"Failed to post alert to Slack: {err}")