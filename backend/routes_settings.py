from flask import Blueprint, jsonify, request
from flask_login import login_required

from models import get_setting, set_setting

settings_bp = Blueprint("settings", __name__)

MASK = "********"


@settings_bp.get("")
@login_required
def get_settings():
    serper = get_setting("serper_api_key")
    groq = get_setting("groq_api_key")
    brevo = get_setting("brevo_api_key")
    return jsonify(
        {
            "serperApiKey": MASK if serper else "",
            "groqApiKey": MASK if groq else "",
            "defaultIndustryCode": get_setting("default_industry_code", ""),
            "brevoApiKey": MASK if brevo else "",
            "senderEmail": get_setting("sender_email", ""),
            "senderName": get_setting("sender_name", ""),
            "publicBaseUrl": get_setting("public_base_url", ""),
            "webhookPath": f"/api/webhooks/brevo/{get_setting('webhook_secret', '')}",
        }
    )


@settings_bp.put("")
@login_required
def update_settings():
    data = request.get_json(silent=True) or {}
    if data.get("serperApiKey") and data["serperApiKey"] != MASK:
        set_setting("serper_api_key", data["serperApiKey"])
    if data.get("groqApiKey") and data["groqApiKey"] != MASK:
        set_setting("groq_api_key", data["groqApiKey"])
    if data.get("brevoApiKey") and data["brevoApiKey"] != MASK:
        set_setting("brevo_api_key", data["brevoApiKey"])
    if "defaultIndustryCode" in data:
        set_setting("default_industry_code", data["defaultIndustryCode"])
    if "senderEmail" in data:
        set_setting("sender_email", data["senderEmail"])
    if "senderName" in data:
        set_setting("sender_name", data["senderName"])
    if "publicBaseUrl" in data:
        set_setting("public_base_url", (data["publicBaseUrl"] or "").rstrip("/"))
    return jsonify({"ok": True})
