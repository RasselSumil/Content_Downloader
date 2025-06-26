import downloader_e621
import downloader_kemono
import requests
import json
import os

def load_language():
    print("🌐 Select language / Выберите язык:")
    print("[1] Русский")
    print("[2] English")
    choice = input("👉 ").strip()
    lang = "ru" if choice == "1" else "en"
    path = f"lang_{lang}.json"
    if not os.path.exists(path):
        print(f"⚠️ Language file not found: {path}")
        return {}, lang
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), lang

def check_e621_tag_exists(author):
    url = "https://e621.net/tags.json"
    headers = {
        "User-Agent": f"e621_downloader/1.0 (by {author})"
    }
    try:
        r = requests.get(url, params={"search[name_matches]": author}, headers=headers, timeout=10)
        r.raise_for_status()
        tags = r.json()
        return any(tag["name"] == author for tag in tags)
    except:
        return False

def check_kemono_creator_exists(author):
    url = "https://kemono.su/api/v1/creators/"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        return any(c["name"].lower() == author.lower() or c["id"] == author for c in data)
    except:
        return False

def prompt_tag_config(base_tag, messages, auto_pages=False):
    exclude = input(messages["exclude_tags"]).strip().split()

    print(messages["select_rating"])
    print(messages["rating_all"])
    print(messages["rating_s"])
    print(messages["rating_q"])
    print(messages["rating_e"])
    r_map = {"1": "rating:s", "2": "rating:q", "3": "rating:e"}
    rating = r_map.get(input("👉 ").strip(), "")

    if auto_pages:
        pages = 9999
    else:
        try:
            pages = int(input(messages["pages"]).strip())
        except:
            pages = 3

    return {
        "base_tag": base_tag,
        "exclude_tags": exclude,
        "rating": rating,
        "pages": pages
    }

def main():
    messages, lang = load_language()
    if not messages:
        return

    while True:
        print("\n" + messages["select_mode"])
        print(messages["by_author"])
        print(messages["by_tag"])
        choice = input(messages["prompt_choice"]).strip()

        if choice == "1":
            author = input(messages["input_author"]).strip()
            platforms = []

            print(messages["searching"])

            if check_e621_tag_exists(author):
                platforms.append("e621.net")
            if check_kemono_creator_exists(author):
                platforms.append("kemono.su")

            if not platforms:
                print(messages["not_found"])
                input("\n" + messages["press_enter"])
                continue

            print(messages["found_on"])
            for i, p in enumerate(platforms, 1):
                print(f"[{i}] {p}")
            idx = input(messages["select_platform"]).strip()
            try:
                platform = platforms[int(idx)-1]
            except:
                print(messages["invalid"])
                input("\n" + messages["press_enter"])
                continue

            if platform == "e621.net":
                config = prompt_tag_config(author, messages, auto_pages=True)
                downloader_e621.run(config, messages, lang)
            elif platform == "kemono.su":
                downloader_kemono.run(author, messages, lang)

        elif choice == "2":
            tag = input(messages["input_tag"]).strip()
            config = prompt_tag_config(tag, messages)
            downloader_e621.run(config, messages, lang)
        else:
            print(messages["invalid"])
            input("\n" + messages["press_enter"])
            continue

        print("\n" + messages["next_action"])
        print(messages["again"])
        print(messages["exit"])
        if input(messages["prompt_choice"]).strip() != "1":
            print(messages["bye"])
            break

if __name__ == "__main__":
    main()