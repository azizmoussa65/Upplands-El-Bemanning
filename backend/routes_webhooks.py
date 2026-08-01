from flask import Blueprint, jsonify, request

from db import companies_col, email_sends_col
from models import get_setting, to_object_id, utcnow

webhooks_bp = Blueprint("webhooks", __name__)

BOUNCE_EVENTS = {"hard_bounce", "soft_bounce", "blocked", "invalid_email"}


@webhooks_bp.post("/brevo/<secret>")
def brevo_webhook(secret):
    """Recoit les evenements de tracking Brevo (delivered/opened/click/bounce/
    unsubscribed) pour un envoi transactionnel. Le secret dans l'URL evite que
    n'importe qui puisse falsifier des evenements (pas d'auth de session ici,
    c'est Brevo qui appelle cette route directement)."""
    if secret != get_setting("webhook_secret"):
        return jsonify({"error": "invalid webhook secret"}), 403

    event = request.get_json(silent=True) or {}
    event_type = event.get("event")
    tag = event.get("tag")

    send_doc = None
    if tag:
        oid = to_object_id(tag)
        if oid:
            send_doc = email_sends_col.find_one({"_id": oid})
    if send_doc is None:
        message_id = event.get("message-id")
        if message_id:
            send_doc = email_sends_col.find_one({"providerMessageId": message_id})
    if send_doc is None:
        return jsonify({"ok": True, "matched": False})

    now = utcnow()
    update = {}

    if event_type == "delivered":
        update = {"deliveredAt": now, "status": "delivered"}
    elif event_type == "opened" or event_type == "unique_opened":
        inc_update = {"$inc": {"opens": 1}, "$set": {"lastOpenedAt": now}}
        email_sends_col.update_one(
            {"_id": send_doc["_id"], "firstOpenedAt": None}, {"$set": {"firstOpenedAt": now}}
        )
        email_sends_col.update_one({"_id": send_doc["_id"]}, inc_update)
    elif event_type == "click":
        inc_update = {"$inc": {"clicks": 1}, "$set": {"lastClickedAt": now}}
        email_sends_col.update_one(
            {"_id": send_doc["_id"], "firstClickedAt": None}, {"$set": {"firstClickedAt": now}}
        )
        email_sends_col.update_one({"_id": send_doc["_id"]}, inc_update)
    elif event_type in BOUNCE_EVENTS:
        update = {"bouncedAt": now, "status": "bounced"}
    elif event_type == "unsubscribed":
        update = {"unsubscribedAt": now}
        companies_col.update_one({"_id": to_object_id(send_doc["companyId"])}, {"$set": {"emailStatus": "unsubscribed"}})

    if update:
        email_sends_col.update_one({"_id": send_doc["_id"]}, {"$set": update})

    return jsonify({"ok": True, "matched": True})
