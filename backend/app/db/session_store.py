import json
from base64 import b64decode, b64encode

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings
from app.db.client import get_supabase


def _get_aesgcm() -> AESGCM:
    key = bytes.fromhex(settings.session_encryption_key)
    return AESGCM(key)


def encrypt_state(state: dict) -> str:
    """Playwright storageState dict を AES-256-GCM で暗号化する。"""
    aesgcm = _get_aesgcm()
    nonce = b"\x00" * 12  # MVP: 固定 nonce (本番ではランダム化 + nonce 保存)
    plaintext = json.dumps(state).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return b64encode(ciphertext).decode()


def decrypt_state(encrypted: str) -> dict:
    """暗号化された storageState を復号する。"""
    aesgcm = _get_aesgcm()
    nonce = b"\x00" * 12
    ciphertext = b64decode(encrypted)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext)


def save_session(host_id: str, state: dict) -> None:
    """storageState を暗号化して Supabase に保存する。"""
    db = get_supabase()
    encrypted = encrypt_state(state)

    existing = (
        db.table("airbnb_sessions")
        .select("id")
        .eq("host_id", host_id)
        .eq("status", "active")
        .maybe_single()
        .execute()
    )

    if existing and existing.data:
        db.table("airbnb_sessions").update({
            "encrypted_state": encrypted,
            "status": "active",
            "last_validated_at": "now()",
        }).eq("id", existing.data["id"]).execute()
    else:
        db.table("airbnb_sessions").insert({
            "host_id": host_id,
            "encrypted_state": encrypted,
            "status": "active",
            "last_validated_at": "now()",
        }).execute()


def load_session(host_id: str) -> dict | None:
    """Supabase から storageState を復号して返す。存在しなければ None。"""
    db = get_supabase()
    result = (
        db.table("airbnb_sessions")
        .select("encrypted_state")
        .eq("host_id", host_id)
        .eq("status", "active")
        .maybe_single()
        .execute()
    )

    if not result or not result.data:
        return None

    return decrypt_state(result.data["encrypted_state"])


def mark_session_expired(host_id: str) -> bool:
    """セッションを expired に更新する。更新できた場合 True。"""
    db = get_supabase()
    result = db.table("airbnb_sessions").update({
        "status": "expired",
    }).eq("host_id", host_id).eq("status", "active").execute()
    return bool(result.data)
