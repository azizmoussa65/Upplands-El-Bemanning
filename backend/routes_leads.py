from datetime import datetime

from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required

from db import companies_col, email_sends_col
from models import call_log_to_dict, company_to_dict, to_object_id, utcnow
from scraping import get_job, start_scrape_job

leads_bp = Blueprint("leads", __name__)

OUTCOME_TO_STATUS = {
    "interesse": "interesse",
    "pas_interesse": "pas_interesse",
    "a_rappeler": "a_appeler",
    "gagne": "gagne",
}


@leads_bp.get("")
@login_required
def list_leads():
    query = {}

    status = request.args.get("status")
    county = request.args.get("county")
    industry_code = request.args.get("industryCode")
    search = request.args.get("search")
    has_mobile = request.args.get("hasMobile")
    has_contact = request.args.get("hasContact")

    if status:
        query["status"] = status
    if county:
        query["county"] = county
    if industry_code:
        query["industryCode"] = industry_code
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    if has_mobile == "true":
        query["mobile"] = {"$nin": [None, ""]}
    if has_contact == "true":
        # Meme regle que le KPI "withContact" du dashboard: email OU telephone.
        query["$or"] = [{"bestEmail": {"$nin": [None, ""]}}, {"bestPhone": {"$nin": [None, ""]}}]

    docs = companies_col.find(query).sort("createdAt", -1)
    return jsonify([company_to_dict(d) for d in docs])


@leads_bp.get("/counties")
@login_required
def list_counties():
    counties = [c for c in companies_col.distinct("county") if c]
    return jsonify(sorted(counties))


@leads_bp.get("/<lead_id>")
@login_required
def get_lead(lead_id):
    oid = to_object_id(lead_id)
    doc = companies_col.find_one({"_id": oid}) if oid else None
    if doc is None:
        return jsonify({"error": "lead not found"}), 404
    return jsonify(company_to_dict(doc, include_call_logs=True))


@leads_bp.patch("/<lead_id>")
@login_required
def update_lead(lead_id):
    oid = to_object_id(lead_id)
    if oid is None:
        return jsonify({"error": "lead not found"}), 404

    data = request.get_json(silent=True) or {}
    update = {}
    if "status" in data:
        update["status"] = data["status"]
    if "assignedUserId" in data:
        update["assignedUserId"] = data["assignedUserId"]
    if update:
        companies_col.update_one({"_id": oid}, {"$set": update})

    doc = companies_col.find_one({"_id": oid})
    if doc is None:
        return jsonify({"error": "lead not found"}), 404
    return jsonify(company_to_dict(doc))


@leads_bp.post("/<lead_id>/notes")
@login_required
def add_note(lead_id):
    oid = to_object_id(lead_id)
    doc = companies_col.find_one({"_id": oid}) if oid else None
    if doc is None:
        return jsonify({"error": "lead not found"}), 404

    data = request.get_json(silent=True) or {}
    raw_date = data.get("callDate")
    try:
        call_date = datetime.fromisoformat(raw_date) if raw_date else utcnow()
    except ValueError:
        call_date = utcnow()

    outcome = data.get("outcome")
    log = {
        "id": str(ObjectId()),
        "companyId": lead_id,
        "note": data.get("note"),
        "outcome": outcome,
        "callDate": call_date,
        "createdAt": utcnow(),
    }

    update = {"$push": {"callLogs": log}}
    if outcome in OUTCOME_TO_STATUS:
        update["$set"] = {"status": OUTCOME_TO_STATUS[outcome]}
    elif doc.get("status") == "nouveau":
        update["$set"] = {"status": "appele"}

    companies_col.update_one({"_id": oid}, update)
    return jsonify(call_log_to_dict(log))


@leads_bp.post("/<lead_id>/mark-replied")
@login_required
def mark_replied(lead_id):
    oid = to_object_id(lead_id)
    doc = companies_col.find_one({"_id": oid}) if oid else None
    if doc is None:
        return jsonify({"error": "lead not found"}), 404

    companies_col.update_one({"_id": oid}, {"$set": {"emailStatus": "replied"}})
    # Stoppe la sequence de relances: tout envoi encore en file d'attente pour ce
    # lead est annule, quelle que soit la campagne.
    email_sends_col.update_many(
        {"companyId": lead_id, "status": "queued"}, {"$set": {"status": "cancelled"}}
    )

    updated = companies_col.find_one({"_id": oid})
    return jsonify(company_to_dict(updated))


@leads_bp.post("/scrape")
@login_required
def scrape():
    params = request.get_json(silent=True) or {}
    if not params.get("industryCode") and not params.get("query"):
        return jsonify({"error": "industryCode or query is required"}), 400

    app = current_app._get_current_object()
    job_id = start_scrape_job(app, params)
    return jsonify({"jobId": job_id})


@leads_bp.get("/scrape/status/<job_id>")
@login_required
def scrape_status(job_id):
    job = get_job(job_id)
    if job is None:
        return jsonify({"error": "unknown job"}), 404
    return jsonify(job)
