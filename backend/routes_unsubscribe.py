import hashlib
import hmac

from flask import Blueprint, Response

from db import companies_col
from models import get_setting, to_object_id

unsubscribe_bp = Blueprint("unsubscribe", __name__)


def unsubscribe_token(company_id):
    secret = get_setting("webhook_secret", "")
    return hmac.new(secret.encode(), company_id.encode(), hashlib.sha256).hexdigest()[:16]


def unsubscribe_link(company_id, base_url):
    return f"{base_url}/api/unsubscribe/{company_id}/{unsubscribe_token(company_id)}"


@unsubscribe_bp.get("/<company_id>/<token>")
def unsubscribe(company_id, token):
    if not hmac.compare_digest(token, unsubscribe_token(company_id)):
        return Response("Invalid link.", status=400)

    oid = to_object_id(company_id)
    if oid is None:
        return Response("Invalid link.", status=400)

    companies_col.update_one({"_id": oid}, {"$set": {"emailStatus": "unsubscribed"}})
    return Response(
        "<html><body style='font-family:sans-serif;padding:40px;text-align:center'>"
        "<h2>You have been unsubscribed.</h2><p>You will not receive further emails from us.</p>"
        "</body></html>",
        mimetype="text/html",
    )
