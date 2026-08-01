"""Boucle d'arriere-plan qui (1) envoie les emails en file d'attente via Brevo et
(2) programme les relances selon la cadence configuree par campagne, en respectant
les regles d'exclusion (appele entre-temps / a repondu / desabonne)."""

import threading
import time

from bson import ObjectId

import email_provider
from db import campaigns_col, companies_col, email_sends_col, users_col
from models import get_setting, utcnow
from routes_unsubscribe import unsubscribe_link

CHECK_INTERVAL_SECONDS = 300  # 5 minutes

_started = False


def start_scheduler(app):
    global _started
    if _started:
        return
    _started = True
    thread = threading.Thread(target=_loop, args=(app,), daemon=True)
    thread.start()


def _loop(app):
    while True:
        try:
            with app.app_context():
                _send_queued()
                _enqueue_followups()
        except Exception as exc:  # noqa: BLE001 - keep the background loop alive
            print(f"[scheduler] error: {exc}")
        time.sleep(CHECK_INTERVAL_SECONDS)


def _new_send_doc(campaign_id, company, sequence_step, email=None):
    return {
        "campaignId": campaign_id,
        "companyId": str(company["_id"]),
        "companyName": company.get("name"),
        "email": email or company.get("bestEmail"),
        "sequenceStep": sequence_step,
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


def _append_unsubscribe_footer(body, company_id):
    """Ajoute un lien de desabonnement en pied de mail, si l'app connait sa propre
    URL publique (configuree dans Settings). Sans cette URL, on ne peut pas
    construire de lien valide, donc on n'en ajoute pas."""
    base_url = get_setting("public_base_url")
    if not base_url:
        return body
    link = unsubscribe_link(company_id, base_url)
    return f'{body}<br><br><p style="font-size:11px;color:#888">' f'<a href="{link}">Unsubscribe</a></p>'


def _is_excluded(company):
    """Regles d'exclusion: deja appele, a deja repondu, ou desabonne."""
    if company.get("callLogs"):
        return True
    return company.get("emailStatus") in ("replied", "unsubscribed")


def _send_queued():
    api_key = get_setting("brevo_api_key")
    sender_email = get_setting("sender_email")
    sender_name = get_setting("sender_name")
    if not api_key or not sender_email:
        return  # pas configure, rien a envoyer

    for send_doc in list(email_sends_col.find({"status": "queued"})):
        company = companies_col.find_one({"_id": ObjectId(send_doc["companyId"])})
        if company is None:
            email_sends_col.update_one({"_id": send_doc["_id"]}, {"$set": {"status": "failed"}})
            continue

        if _is_excluded(company):
            email_sends_col.update_one({"_id": send_doc["_id"]}, {"$set": {"status": "skipped"}})
            continue

        campaign = campaigns_col.find_one({"_id": ObjectId(send_doc["campaignId"])})
        owner = users_col.find_one({"_id": campaign["ownerId"]}) if campaign and campaign.get("ownerId") else None

        subject = email_provider.render_template(campaign.get("subject") if campaign else "", company)
        body = email_provider.render_template(campaign.get("body") if campaign else "", company)
        body = _append_unsubscribe_footer(body, send_doc["companyId"])

        try:
            result = email_provider.send_email(
                api_key,
                sender_email,
                sender_name,
                send_doc["email"],
                company.get("contactPersonName"),
                subject,
                body,
                reply_to_email=(owner.get("email") if owner else None),
                tag=str(send_doc["_id"]),
            )
            email_sends_col.update_one(
                {"_id": send_doc["_id"]},
                {"$set": {"status": "sent", "sentAt": utcnow(), "providerMessageId": result.get("messageId")}},
            )
            companies_col.update_one({"_id": company["_id"]}, {"$set": {"emailStatus": "emailed"}})
        except Exception as exc:  # noqa: BLE001 - mark this one failed, keep going
            email_sends_col.update_one({"_id": send_doc["_id"]}, {"$set": {"status": "failed"}})
            print(f"[scheduler] send failed for {send_doc['email']}: {exc}")


def _enqueue_followups():
    for campaign in campaigns_col.find({"status": "sending"}):
        cadence = campaign.get("followUpCadence") or []
        if not cadence:
            continue

        sends = list(email_sends_col.find({"campaignId": str(campaign["_id"])}))
        latest_by_company = {}
        for s in sends:
            key = s["companyId"]
            if key not in latest_by_company or s["sequenceStep"] > latest_by_company[key]["sequenceStep"]:
                latest_by_company[key] = s

        for company_id, last_send in latest_by_company.items():
            if last_send["status"] not in ("sent", "delivered"):
                continue

            next_step = last_send["sequenceStep"] + 1
            if next_step > len(cadence):
                continue

            company = companies_col.find_one({"_id": ObjectId(company_id)})
            if company is None or _is_excluded(company):
                continue

            sent_at = last_send.get("sentAt")
            if sent_at is None:
                continue
            wait_days = cadence[next_step - 1]["afterDays"]
            if (utcnow() - sent_at).days < wait_days:
                continue

            email_sends_col.insert_one(_new_send_doc(str(campaign["_id"]), company, next_step, email=last_send["email"]))
