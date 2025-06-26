import os
import requests
from tqdm import tqdm
from time import sleep

BASE = "https://kemono.su"
CREATORS_ENDPOINT = f"{BASE}/api/v1/creators/"
DOWNLOAD_ROOT = "downloads/kemono"
BATCH_SIZE = 50
ATTACHMENT_MIN_SIZE = 10 * 1024  # 10 KB
TEXT_MIN_SIZE = 512  # min post.txt size

def resolve_author_id(user_input):
    try:
        r = requests.get(CREATORS_ENDPOINT, timeout=20)
        r.raise_for_status()
        creators = r.json()
    except Exception as e:
        print(f"❌ Failed to fetch creators list: {e}")
        return None, []

    for c in creators:
        if c["name"].lower() == user_input.lower() or c["id"] == user_input:
            platforms = [entry["service"] for entry in creators if entry["id"] == c["id"]]
            return c["id"], sorted(set(platforms))
    return None, []

def fetch_all_posts(platform, author_id):
    all_posts = []
    offset = 0
    while True:
        url = f"{BASE}/api/v1/{platform}/user/{author_id}?o={offset}"
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            batch = r.json()
        except Exception as e:
            print(f"❌ Error loading posts: {e}")
            break
        if not batch:
            break
        all_posts.extend(batch)
        offset += BATCH_SIZE
        sleep(0.2)
    return all_posts

def log_skipped(path, post_id, reason):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{post_id}] Skipped: {reason}\n")

def download_post(post, folder, skip_log):
    post_id = post.get("id")
    post_folder = os.path.join(folder, post_id)
    os.makedirs(post_folder, exist_ok=True)
    post_url = f"{BASE}/{post['service']}/user/{post['user']}/post/{post_id}"
    text_path = os.path.join(post_folder, "post.txt")

    # Save text content
    if not os.path.exists(text_path) or os.path.getsize(text_path) < TEXT_MIN_SIZE:
        try:
            content = post.get("content") or ""
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(f"{post['title']}\n\n{content}\n\n{post_url}")
            if os.path.getsize(text_path) < TEXT_MIN_SIZE:
                os.remove(text_path)
                log_skipped(skip_log, post_id, "post.txt too small (<512B)")
                return "broken"
        except Exception as e:
            log_skipped(skip_log, post_id, f"post.txt error ({e})")
            return "fail"

    # Save attachments
    attachments = post.get("attachments", [])
    for att in attachments:
        url = f"{BASE}/data{att['path']}"
        name = att.get("name") or "file"
        dest = os.path.join(post_folder, name)

        if os.path.exists(dest) and os.path.getsize(dest) >= ATTACHMENT_MIN_SIZE:
            continue  # already OK

        try:
            r = requests.get(url, stream=True, timeout=20)
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            sleep(0.1)
            if os.path.getsize(dest) < ATTACHMENT_MIN_SIZE:
                os.remove(dest)
                log_skipped(skip_log, post_id, f"{name} corrupted (<10KB)")
                return "broken"
        except Exception as e:
            log_skipped(skip_log, post_id, f"{name} download error ({e})")
            return "fail"

    return "ok" if attachments else "cached"

def run(author_input, messages, lang):
    while True:
        print(f"\n🔍 {messages['input_author']}{author_input}")
        resolved_id, platforms = resolve_author_id(author_input)

        if not platforms:
            print(messages["not_found"])
            input("\n" + messages["press_enter"])
            return

        if len(platforms) == 1:
            platform = platforms[0]
            print(f"✅ {platform}")
        else:
            print("\n" + messages["found_on"])
            for i, p in enumerate(platforms, 1):
                print(f"[{i}] {p}")
            idx = input(messages["select_platform"]).strip()
            try:
                platform = platforms[int(idx)-1]
            except:
                print(messages["invalid"])
                input("\n" + messages["press_enter"])
                return

        print(f"\n📥 {platform} → {resolved_id}")
        posts = fetch_all_posts(platform, resolved_id)

        if not posts:
            print("🚫 No posts found.")
            print(f"ℹ️ Check: {BASE}/{platform}/user/{resolved_id}")
            input("\n" + messages["press_enter"])
            return

        folder = os.path.join(DOWNLOAD_ROOT, platform, resolved_id)
        os.makedirs(folder, exist_ok=True)
        skip_log = os.path.join(folder, "skipped.log")

        print(f"🔎 Found: {len(posts)} posts\n")

        ok = cached = failed = broken = 0
        for post in tqdm(posts, desc="⬇️ Downloading", unit="post"):
            result = download_post(post, folder, skip_log)
            if result == "ok":
                ok += 1
            elif result == "cached":
                cached += 1
            elif result == "broken":
                broken += 1
            elif result == "fail":
                failed += 1

        print(f"\n✅ Done!")
        print(f"📸 New posts: {ok}")
        print(f"📁 Already existed: {cached}")
        print(f"⚠️ Failed: {failed}")
        print(f"💢 Corrupted: {broken}")
        if failed or broken:
            print(f"🗒️ Log: {os.path.relpath(skip_log)}")

        print("\n" + messages["next_action"])
        print(messages["again"])
        print(messages["exit"])
        if input(messages["prompt_choice"]).strip() != "1":
            print(messages["bye"])
            break
        author_input = input(messages["input_author"]).strip()