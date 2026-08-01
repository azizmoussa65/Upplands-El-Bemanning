import os

from flask import Blueprint, jsonify, request, send_from_directory
from flask_login import login_required
from werkzeug.security import generate_password_hash

from models import User, to_object_id
from db import users_col

users_bp = Blueprint("users", __name__)

AVATAR_DIR = os.path.join(os.path.dirname(__file__), "uploads", "avatars")
ALLOWED_AVATAR_EXT = {"png", "jpg", "jpeg", "webp"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2 Mo

os.makedirs(AVATAR_DIR, exist_ok=True)


@users_bp.get("")
@login_required
def list_users():
    return jsonify([u.to_dict() for u in User.list_all()])


@users_bp.post("")
@login_required
def create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip() or None
    color = (data.get("color") or "").strip() or None

    if not username or len(password) < 6:
        return jsonify({"error": "username required, password must be at least 6 characters"}), 400
    if User.find_by_username(username):
        return jsonify({"error": "username already taken"}), 400

    user = User.create(username, generate_password_hash(password), email=email, color=color)
    return jsonify(user.to_dict()), 201


@users_bp.patch("/<user_id>")
@login_required
def update_user(user_id):
    oid = to_object_id(user_id)
    if oid is None:
        return jsonify({"error": "user not found"}), 404
    user = User.find_by_id(user_id)
    if user is None:
        return jsonify({"error": "user not found"}), 404

    data = request.get_json(silent=True) or {}
    user.update_profile(email=data.get("email"), color=data.get("color"))
    return jsonify(user.to_dict())


@users_bp.delete("/<user_id>")
@login_required
def delete_user(user_id):
    user = User.find_by_id(user_id)
    if user is None:
        return jsonify({"error": "user not found"}), 404
    if users_col.count_documents({}) <= 1:
        return jsonify({"error": "cannot delete the last remaining user"}), 400
    for ext in ALLOWED_AVATAR_EXT:
        path = os.path.join(AVATAR_DIR, f"{user_id}.{ext}")
        if os.path.exists(path):
            os.remove(path)
    user.delete()
    return jsonify({"ok": True})


@users_bp.post("/<user_id>/avatar")
@login_required
def upload_avatar(user_id):
    user = User.find_by_id(user_id)
    if user is None:
        return jsonify({"error": "user not found"}), 404

    file = request.files.get("avatar")
    if not file or not file.filename:
        return jsonify({"error": "no file provided"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_AVATAR_EXT:
        return jsonify({"error": "unsupported file type (png, jpg, jpeg, webp only)"}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_AVATAR_BYTES:
        return jsonify({"error": "file too large (max 2 MB)"}), 400

    # Retire un ancien avatar avec une extension differente avant d'enregistrer le nouveau.
    for old_ext in ALLOWED_AVATAR_EXT:
        old_path = os.path.join(AVATAR_DIR, f"{user_id}.{old_ext}")
        if os.path.exists(old_path):
            os.remove(old_path)

    file.save(os.path.join(AVATAR_DIR, f"{user_id}.{ext}"))
    user.update_profile(avatar_ext=ext)
    return jsonify(user.to_dict())


@users_bp.get("/<user_id>/avatar")
def get_avatar(user_id):
    user = User.find_by_id(user_id)
    if user is None or not user.avatar_ext:
        return jsonify({"error": "no avatar"}), 404
    return send_from_directory(AVATAR_DIR, f"{user_id}.{user.avatar_ext}")
