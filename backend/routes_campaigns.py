from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import campaigns_col, companies_col, email_sends_col
from models import campaign_to_dict, email_send_to_dict, to_object_id, utcnow

campaigns_bp = Blueprint("campaigns", __name__)


def _recipient_query(recipient_filter):
    """Un lead n'est un destinataire valide que s'il a un email, n'a jamais ete
    appele (callLogs vide) et n'est pas desabonne — regles d'exclusion de base."""
    query = {
        "bestEmail": {"$nin": [None, ""]},
        "$or": [{"callLogs": {"$exists": False}}, {"callLogs": {"$size": 0}}],
        "emailStatus": {"$ne": "unsubscribed"},
    }
    if recipient_filter.get("county"):
        query["county"] = recipient_filter["county"]
    if recipient_filter.get("status"):
        query["status"] = recipient_filter["status"]
    if recipient_filter.get("search"):
        query["name"] = {"$regex": recipient_filter["search"], "$options": "i"}
    return query


@campaigns_bp.get("/preview-recipients")
@login_required
def preview_recipients():
    recipient_filter = {
        "county": request.args.get("county"),
        "status": request.args.get("status"),
        "search": request.args.get("search"),
    }
    count = companies_col.count_documents(_recipient_query(recipient_filter))
    return jsonify({"count": count})


@campaigns_bp.get("")
@login_required
def list_campaigns():
    docs = campaigns_col.find().sort("createdAt", -1)
    return jsonify([campaign_to_dict(d) for d in docs])


@campaigns_bp.post("")
@login_required
def create_campaign():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    subject = (data.get("subject") or "").strip()
    body = data.get("body") or ""
    if not name or not subject or not body:
        return jsonify({"error": "name, subject and body are required"}), 400

    cadence = data.get("followUpCadence") or []
    cadence = [{"afterDays": int(step.get("afterDays"))} for step in cadence if step.get("afterDays")]

    doc = {
        "name": name,
        "subject": subject,
        "body": body,
        "ownerId": to_object_id(current_user.get_id()),
        "followUpCadence": cadence,
        "recipientFilter": {
            "county": data.get("recipientFilter", {}).get("county") or None,
            "status": data.get("recipientFilter", {}).get("status") or None,
            "search": data.get("recipientFilter", {}).get("search") or None,
        },
        "status": "draft",
        "createdAt": utcnow(),
    }
    result = campaigns_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return jsonify(campaign_to_dict(doc)), 201


@campaigns_bp.get("/<campaign_id>")
@login_required
def get_campaign(campaign_id):
    oid = to_object_id(campaign_id)
    doc = campaigns_col.find_one({"_id": oid}) if oid else None
    if doc is None:
        return jsonify({"error": "campaign not found"}), 404
    return jsonify(campaign_to_dict(doc))


@campaigns_bp.delete("/<campaign_id>")
@login_required
def delete_campaign(campaign_id):
    oid = to_object_id(campaign_id)
    if oid is None:
        return jsonify({"error": "campaign not found"}), 404
    campaigns_col.delete_one({"_id": oid})
    email_sends_col.delete_many({"campaignId": campaign_id})
    return jsonify({"ok": True})


@campaigns_bp.post("/<campaign_id>/launch")
@login_required
def launch_campaign(campaign_id):
    oid = to_object_id(campaign_id)
    campaign = campaigns_col.find_one({"_id": oid}) if oid else None
    if campaign is None:
        return jsonify({"error": "campaign not found"}), 404
    if campaign.get("status") != "draft":
        return jsonify({"error": "campaign was already launched"}), 400

    recipients = list(companies_col.find(_recipient_query(campaign.get("recipientFilter") or {})))
    already_queued = {
        s["companyId"]
        for s in email_sends_col.find({"campaignId": campaign_id}, {"companyId": 1})
    }

    created = 0
    for company in recipients:
        company_id = str(company["_id"])
        if company_id in already_queued:
            continue
        email_sends_col.insert_one(
            {
                "campaignId": campaign_id,
                "companyId": company_id,
                "companyName": company.get("name"),
                "email": company.get("bestEmail"),
                "sequenceStep": 0,
                "status": "queued",
                "sentAt": None,
                "deliveredAt": None,
                "bouncedAt": None,
                "opens": 0,
                "clicks": 0,
                "firstOpenedAt": None,
                "lastOpenedAt": None,
                "firstClickedAt": None,
                "lastClickedAt": None,
                "unsubscribedAt": None,
                "providerMessageId": None,
                "createdAt": utcnow(),
            }
        )
        created += 1

    campaigns_col.update_one({"_id": oid}, {"$set": {"status": "sending"}})
    return jsonify({"ok": True, "queued": created})


@campaigns_bp.get("/<campaign_id>/sends")
@login_required
def campaign_sends(campaign_id):
    event = request.args.get("event")  # "opened" | "clicked" | None (all)
    query = {"campaignId": campaign_id}
    if event == "opened":
        query["opens"] = {"$gt": 0}
    elif event == "clicked":
        query["clicks"] = {"$gt": 0}

    docs = email_sends_col.find(query).sort("lastClickedAt", -1)
    return jsonify([email_send_to_dict(d) for d in docs])
