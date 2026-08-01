import json

import requests
from flask import Blueprint, jsonify
from flask_login import login_required

from db import companies_col
from models import company_to_dict, get_setting, to_object_id

ai_bp = Blueprint("ai", __name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _build_prompt(doc):
    return (
        "You are a B2B sales assistant for Upplands El & Bemanning, a Swedish electrical "
        "installation and staffing (recruitment/temp work) company, prospecting companies "
        "in the electrical sector to call.\n\n"
        "Here is the data for a prospect:\n"
        f"- Name: {doc.get('name')}\n"
        f"- Industry: {doc.get('industryName')}\n"
        f"- Revenue: {doc.get('revenue')}\n"
        f"- Employees: {doc.get('employees')}\n"
        f"- City/region: {doc.get('municipality')}, {doc.get('county')}\n"
        f"- Mobile found: {doc.get('mobile') or 'none'}\n"
        f"- Email found: {doc.get('bestEmail') or 'none'}\n"
        f"- Contact data confidence: {doc.get('confidence')}\n"
        f"- Current status: {doc.get('status')}\n\n"
        "Reply ONLY with valid JSON in this form:\n"
        '{"recommendation": "call" or "do not call", "score": 0-100, '
        '"reason": "short reason in English, 1-2 sentences"}'
    )


@ai_bp.post("/leads/<lead_id>/recommend")
@login_required
def recommend(lead_id):
    oid = to_object_id(lead_id)
    doc = companies_col.find_one({"_id": oid}) if oid else None
    if doc is None:
        return jsonify({"error": "lead not found"}), 404

    api_key = get_setting("groq_api_key")
    if not api_key:
        return jsonify({"error": "missing Groq API key (Settings page)"}), 400

    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": _build_prompt(doc)}],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            },
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        result = json.loads(content)
    except Exception as exc:  # noqa: BLE001 - surfaced to the frontend as-is
        return jsonify({"error": f"Groq error: {exc}"}), 502

    update = {
        "aiRecommendation": result.get("recommendation"),
        "aiScore": result.get("score"),
        "aiReason": result.get("reason"),
    }
    companies_col.update_one({"_id": oid}, {"$set": update})
    doc.update(update)

    return jsonify(company_to_dict(doc))
