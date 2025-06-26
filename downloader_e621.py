import os
import json
import base64
import requests
from time import sleep
from tqdm import tqdm

LIMIT = 320
MIN_SIZE = 10 * 1024  # 10 KB

AUTH_FILE = ".auth_e621.json"
DOWNLOAD_ROOT = "downloads/e621"

def load_auth(messages):
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "r") as f:
            return json.load(f)
    print("\n🔐 e621 API credentials:")
    print("🌐 https://e621.net/users/home (scroll to bottom)")
    username = input("👤 Username: ").strip()
    api_key = input("🔑 API Key: ").strip()
    creds = {"username": username, "api_key": api_key}
    with open(AUTH_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    return creds

def build_headers(username, api_key):
    token = base64.b64encode(f"{username}:{api_key}".encode()).decode()
    return {
        "User-Agent": f"e621_downloader/1.0 (by {username})",
        "Authorization": f"Basic {token}"
    }

def build_query(config):
    tags = config["base_tag"].split()
    tags += [f"-{t}" for t in config["exclude_tags"]]
    if config["rating"]:
        tags.append(config["rating"])
    return " ".join(tags)

def fetch_posts(query, headers, max_pages):
    posts = []
    for page in range(1, max_pages + 1):
        url = "https://e621.net/posts.json"
        params = {"tags": query, "limit": LIMIT, "page": page}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=20)
            r.raise_for_status()
            batch = r.json().get("posts", [])
            if not batch:
                break
            posts.extend(batch)
            if len(batch) < LIMIT:
                break
        except Exception as e:
            print(f"❌ {e}")
            break
    return posts

def log_skipped(path, post_id, reason):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{post_id}] Skipped: {reason}\n")

def download_post(post, folder, headers, skip_log):
    post_id = str(post["id"])
    file = post.get("file", {})
    url = file.get("url")
    ext = file.get("ext", "jpg")

    if not url:
        log_skipped(skip_log, post_id, "missing url")
        return "skip"

    filename = f"{post_id}.{ext}"
    path = os.path.join(folder, filename)

    def try_download():
        try:
            r = requests.get(url, headers=headers, stream=True, timeout=20)
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return True
        except Exception as e:
            log_skipped(skip_log, post_id, f"download error ({e})")
            return False

    if os.path.exists(path):
        if os.path.getsize(path) < MIN_SIZE:
            os.remove(path)
            if try_download() and os.path.getsize(path) >= MIN_SIZE:
                return "ok"
            log_skipped(skip_log, post_id, "corrupted file (<10KB)")
            return "broken"
        return "cached"

    if try_download():
        if os.path.getsize(path) < MIN_SIZE:
            os.remove(path)
            log_skipped(skip_log, post_id, "corrupted file (<10KB)")
            return "broken"
        return "ok"
    return "fail"

def run(config, messages, lang):
    auth = load_auth(messages)
    headers = build_headers(auth["username"], auth["api_key"])
    query = build_query(config)

    folder_name = "_".join(query.replace(":", "").replace("-", "not").split())
    folder = os.path.join(DOWNLOAD_ROOT, folder_name)
    os.makedirs(folder, exist_ok=True)
    skip_log = os.path.join(folder, "skipped.log")

    print(f"\n📥 {query}")
    posts = fetch_posts(query, headers, config["pages"])

    print(f"\n🔎 Found: {len(posts)} posts\n")

    ok = cached = skip = fail = broken = 0
    for post in tqdm(posts, desc="⬇️ Downloading", unit="file"):
        result = download_post(post, folder, headers, skip_log)
        if result == "ok":
            ok += 1
        elif result == "cached":
            cached += 1
        elif result == "fail":
            fail += 1
        elif result == "broken":
            broken += 1
        else:
            skip += 1

    print(f"\n✅ Done!")
    print(f"📸 New: {ok}")
    print(f"📁 Already existed: {cached}")
    print(f"⚠️ Skipped: {skip + fail}")
    print(f"💢 Corrupted: {broken}")
    print(f"🗒️ Log: {os.path.relpath(skip_log)}")

    input("\n" + messages["press_enter"])