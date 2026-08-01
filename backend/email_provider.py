"""Thin wrapper around Brevo's transactional email REST API (send + template
variable substitution). No SDK dependency, same style as the raw `requests` calls
already used for Serper/Groq in this project."""

import requests

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"

TEMPLATE_VARS = {
    "{{name}}": "contactPersonName",
    "{{company}}": "name",
    "{{county}}": "county",
    "{{municipality}}": "municipality",
}


def render_template(text, company):
    """Remplace les variables {{name}}, {{company}}, ... par les donnees de l'entreprise."""
    if not text:
        return text
    for token, field in TEMPLATE_VARS.items():
        text = text.replace(token, company.get(field) or "")
    return text


def send_email(api_key, sender_email, sender_name, to_email, to_name, subject, html_body, reply_to_email=None, tag=None):
    """Envoie un email transactionnel via Brevo. Renvoie la reponse JSON de Brevo
    (contient notamment 'messageId'). Leve une exception si l'envoi echoue."""
    payload = {
        "sender": {"name": sender_name or to_email, "email": sender_email},
        "to": [{"email": to_email, "name": to_name or to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }
    if reply_to_email:
        payload["replyTo"] = {"email": reply_to_email}
    if tag:
        payload["tags"] = [tag]

    resp = requests.post(
        BREVO_SEND_URL,
        headers={"api-key": api_key, "Content-Type": "application/json", "Accept": "application/json"},
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()
