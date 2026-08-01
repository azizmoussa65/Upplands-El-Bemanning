from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask_login import UserMixin

from db import campaigns_col, companies_col, email_sends_col, settings_col, users_col


def to_object_id(raw_id):
    try:
        return ObjectId(raw_id)
    except (InvalidId, TypeError):
        return None


DEFAULT_USER_COLOR = "#4f52e5"


class User(UserMixin):
    def __init__(self, doc):
        self._id = doc["_id"]
        self.username = doc["username"]
        self.password_hash = doc["password_hash"]
        self.email = doc.get("email")
        self.color = doc.get("color") or DEFAULT_USER_COLOR
        self.avatar_ext = doc.get("avatarExt")

    def get_id(self):
        return str(self._id)

    def to_dict(self):
        return {
            "id": str(self._id),
            "username": self.username,
            "email": self.email,
            "color": self.color,
            "avatarUrl": f"/api/users/{self._id}/avatar" if self.avatar_ext else None,
        }

    def set_password_hash(self, password_hash):
        users_col.update_one({"_id": self._id}, {"$set": {"password_hash": password_hash}})
        self.password_hash = password_hash

    @staticmethod
    def find_by_username(username):
        doc = users_col.find_one({"username": username})
        return User(doc) if doc else None

    @staticmethod
    def find_by_id(user_id):
        oid = to_object_id(user_id)
        if oid is None:
            return None
        doc = users_col.find_one({"_id": oid})
        return User(doc) if doc else None

    @staticmethod
    def list_all():
        return [User(doc) for doc in users_col.find().sort("username", 1)]

    @staticmethod
    def create(username, password_hash, email=None, color=None):
        result = users_col.insert_one(
            {
                "username": username,
                "password_hash": password_hash,
                "email": email,
                "color": color or DEFAULT_USER_COLOR,
            }
        )
        return User.find_by_id(result.inserted_id)

    def update_profile(self, email=None, color=None, avatar_ext=None):
        update = {}
        if email is not None:
            update["email"] = email
            self.email = email
        if color is not None:
            update["color"] = color
            self.color = color
        if avatar_ext is not None:
            update["avatarExt"] = avatar_ext
            self.avatar_ext = avatar_ext
        if update:
            users_col.update_one({"_id": self._id}, {"$set": update})

    def delete(self):
        users_col.delete_one({"_id": self._id})


def _iso(value):
    return value.isoformat() if isinstance(value, datetime) else None


def call_log_to_dict(log):
    return {
        "id": log.get("id"),
        "companyId": log.get("companyId"),
        "note": log.get("note"),
        "outcome": log.get("outcome"),
        "callDate": _iso(log.get("callDate")),
        "createdAt": _iso(log.get("createdAt")),
    }


def company_to_dict(doc, include_call_logs=False):
    if doc is None:
        return None
    data = {
        "id": str(doc["_id"]),
        "orgnr": doc.get("orgnr"),
        "name": doc.get("name"),
        "contactPersonName": doc.get("contactPersonName"),
        "contactPersonRole": doc.get("contactPersonRole"),
        "revenue": doc.get("revenue"),
        "employees": doc.get("employees"),
        "county": doc.get("county"),
        "municipality": doc.get("municipality"),
        "bestEmail": doc.get("bestEmail"),
        "bestPhone": doc.get("bestPhone"),
        "mobile": doc.get("mobile"),
        "foundWebsite": doc.get("foundWebsite"),
        "confidence": doc.get("confidence"),
        "industryCode": doc.get("industryCode"),
        "industryName": doc.get("industryName"),
        "sniCode": doc.get("sniCode"),
        "sniName": doc.get("sniName"),
        "financials": doc.get("financials"),
        "keyFigures": doc.get("keyFigures"),
        "status": doc.get("status", "nouveau"),
        "emailStatus": doc.get("emailStatus", "not_contacted"),
        "assignedUserId": doc.get("assignedUserId"),
        "aiRecommendation": doc.get("aiRecommendation"),
        "aiScore": doc.get("aiScore"),
        "aiReason": doc.get("aiReason"),
        "createdAt": _iso(doc.get("createdAt")),
    }
    if include_call_logs:
        logs = doc.get("callLogs") or []
        logs = sorted(logs, key=lambda log: log.get("callDate") or datetime.min.replace(tzinfo=None), reverse=True)
        data["callLogs"] = [call_log_to_dict(log) for log in logs]
    return data


def campaign_stats(campaign_id):
    sends = list(email_sends_col.find({"campaignId": str(campaign_id)}))
    return {
        "sent": sum(1 for s in sends if s.get("sentAt")),
        "delivered": sum(1 for s in sends if s.get("deliveredAt")),
        "bounced": sum(1 for s in sends if s.get("bouncedAt")),
        "opened": sum(1 for s in sends if s.get("opens")),
        "clicked": sum(1 for s in sends if s.get("clicks")),
        "unsubscribed": sum(1 for s in sends if s.get("unsubscribedAt")),
    }


def campaign_to_dict(doc, include_stats=True):
    if doc is None:
        return None
    owner = users_col.find_one({"_id": doc.get("ownerId")}) if doc.get("ownerId") else None
    data = {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "subject": doc.get("subject"),
        "body": doc.get("body"),
        "ownerId": str(doc["ownerId"]) if doc.get("ownerId") else None,
        "ownerUsername": owner.get("username") if owner else None,
        "ownerColor": (owner.get("color") or DEFAULT_USER_COLOR) if owner else None,
        "followUpCadence": doc.get("followUpCadence") or [],
        "recipientFilter": doc.get("recipientFilter") or {},
        "status": doc.get("status", "draft"),
        "createdAt": _iso(doc.get("createdAt")),
    }
    if include_stats:
        data["stats"] = campaign_stats(doc["_id"])
    return data


def email_send_to_dict(doc):
    return {
        "id": str(doc["_id"]),
        "companyId": doc.get("companyId"),
        "companyName": doc.get("companyName"),
        "email": doc.get("email"),
        "opens": doc.get("opens", 0),
        "clicks": doc.get("clicks", 0),
        "lastEventAt": _iso(doc.get("lastClickedAt") or doc.get("lastOpenedAt") or doc.get("deliveredAt") or doc.get("sentAt")),
    }


def utcnow():
    return datetime.now(timezone.utc)


def get_setting(key, default=None):
    doc = settings_col.find_one({"_id": key})
    return doc["value"] if doc and doc.get("value") else default


def set_setting(key, value):
    settings_col.update_one({"_id": key}, {"$set": {"value": value}}, upsert=True)


__all__ = [
    "User",
    "to_object_id",
    "call_log_to_dict",
    "company_to_dict",
    "campaign_to_dict",
    "campaign_stats",
    "email_send_to_dict",
    "utcnow",
    "get_setting",
    "set_setting",
    "companies_col",
]
