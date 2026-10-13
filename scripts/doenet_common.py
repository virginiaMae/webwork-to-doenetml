"""Shared helpers for syncing folders in this repo with Doenet.org.

A "synced folder" is any directory in this repo that contains a
doenet-sync.json naming the Doenet.org folder it mirrors:

    {"folderId": "kP4hWuV6gEEfpWrhmVjEYa", "ownerId": "pcKKBXm3cunporFKSGZD5D"}

Loads DOENET_SESSION_COOKIE from a local .env (never committed), talks to
the Doenet API, and reads/writes the small "Doenet-Sync-*" metadata block
that doenet_pull.py embeds at the top of each .doenetml file so
doenet_push.py can find its way back to the right activity.
"""

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

BASE = "https://doenet.org/api"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(REPO_ROOT, ".env")
SYNC_CONFIG_NAME = "doenet-sync.json"

# Not searched for synced folders: separate checkouts and tooling dirs.
SKIP_DIRS = {".git", "scripts", "__pycache__", "node_modules"}

# A dedicated, self-contained comment block prepended to the file (not
# merged into the activity's own Title/Author comment). Anchored at the
# very start of the file and matched byte-for-byte, so stripping it always
# restores the exact original content -- no whitespace-reconstruction
# guesswork, so hashes computed before/after a round trip always agree.
SYNC_BLOCK_RE = re.compile(
    r"\A<!-- Doenet-Sync\n"
    r"Doenet-Sync-ID: (?P<id>\S+)\n"
    r"Doenet-Sync-Version: (?P<version>\S+)\n"
    r"Doenet-Sync-NumVariants: (?P<numvariants>\d+)\n"
    r"Doenet-Sync-Hash: (?P<hash>\S+)\n"
    r"-->\n"
)


def load_env():
    """Minimal .env loader (no external dependency). Sets os.environ."""
    if not os.path.exists(ENV_PATH):
        return
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def get_cookie():
    load_env()
    cookie = os.environ.get("DOENET_SESSION_COOKIE")
    if not cookie:
        raise SystemExit(
            "DOENET_SESSION_COOKIE is not set. Copy .env.example to .env "
            "and fill in a fresh connect.sid cookie value (see README.md)."
        )
    return cookie


def load_sync_config(folder):
    with open(os.path.join(folder, SYNC_CONFIG_NAME), "r", encoding="utf-8") as f:
        config = json.load(f)
    for key in ("folderId", "ownerId"):
        if key not in config:
            raise SystemExit(f"{SYNC_CONFIG_NAME} in {folder} is missing {key!r}")
    return config


def find_synced_folders(root=None):
    """Return absolute paths of synced folders.

    With `root`, that folder alone (it must have a doenet-sync.json);
    otherwise every folder in the repo that has one.
    """
    if root:
        root = os.path.abspath(root)
        if not os.path.exists(os.path.join(root, SYNC_CONFIG_NAME)):
            raise SystemExit(f"No {SYNC_CONFIG_NAME} in {root}")
        return [root]
    found = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in SKIP_DIRS
            and not os.path.exists(os.path.join(dirpath, d, ".git"))
        )
        if SYNC_CONFIG_NAME in filenames:
            found.append(dirpath)
            dirnames[:] = []  # a synced folder's subfolders belong to it
    return found


def find_doenetml_files(folder):
    paths = []
    for dirpath, _dirnames, filenames in os.walk(folder):
        for fn in filenames:
            if fn.endswith(".doenetml"):
                paths.append(os.path.join(dirpath, fn))
    return sorted(paths)


def _request(method, path, cookie, payload=None):
    url = f"{BASE}/{path}"
    headers = {"Cookie": f"connect.sid={cookie}"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)

    def _parse(text):
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, _parse(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, _parse(e.read().decode("utf-8", errors="replace"))


def get(path, cookie):
    status, body = _request("GET", path, cookie)
    return body


def post(path, payload, cookie):
    return _request("POST", path, cookie, payload)


def get_folder_contents(owner_id, folder_id, cookie):
    data = get(f"contentList/getMyContent/{owner_id}/{folder_id}", cookie)
    if data.get("notMe"):
        raise RuntimeError(
            f"notMe for folder {folder_id} -- cookie is invalid/expired, "
            "or this account doesn't own that folder."
        )
    return data.get("content", [])


def walk_folder(owner_id, folder_id, cookie, on_folder=None):
    """Yield (path_parts, item) for every item under a Doenet.org folder,
    recursing into subfolders (not into problem sets).

    path_parts is the list of ancestor folder names below the top folder,
    NOT including the item's own name.
    """

    def _walk(fid, path_parts):
        time.sleep(0.1)
        items = get_folder_contents(owner_id, fid, cookie)
        if on_folder:
            on_folder(path_parts)
        for item in items:
            if item.get("type") == "folder":
                yield from _walk(item["contentId"], path_parts + [item["name"]])
            else:
                yield path_parts, item

    yield from _walk(folder_id, [])


SAFE_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_path_component(name):
    name = SAFE_CHARS_RE.sub("_", name).strip().rstrip(".")
    if len(name) > 150:
        name = name[:150].rstrip()
    return name or "untitled"


def body_hash(body_text):
    return hashlib.sha256(body_text.encode("utf-8")).hexdigest()[:16]


def split_sync_header(doenetml_text):
    """Return (sync_fields_or_None, body_text).

    body_text is the full file content with the dedicated Doenet-Sync
    comment block removed, so hashing/comparison is stable regardless of
    metadata churn.
    """
    m = SYNC_BLOCK_RE.search(doenetml_text)
    if not m:
        return None, doenetml_text
    fields = {
        "id": m.group("id"),
        "version": m.group("version"),
        "numvariants": m.group("numvariants"),
        "hash": m.group("hash"),
    }
    body = doenetml_text[: m.start()] + doenetml_text[m.end():]
    return fields, body


def render_sync_block(content_id, version, num_variants, hash_value):
    return (
        f"<!-- Doenet-Sync\n"
        f"Doenet-Sync-ID: {content_id}\n"
        f"Doenet-Sync-Version: {version}\n"
        f"Doenet-Sync-NumVariants: {num_variants}\n"
        f"Doenet-Sync-Hash: {hash_value}\n"
        f"-->\n"
    )


def insert_or_update_sync_block(doenetml_text, content_id, version, num_variants, hash_value):
    """Prepend/replace the dedicated Doenet-Sync comment block. Stripping it
    back off (split_sync_header) always restores doenetml_text exactly."""
    _existing_fields, stripped_body = split_sync_header(doenetml_text)
    return render_sync_block(content_id, version, num_variants, hash_value) + stripped_body
