"""Offline repository checks; does not run Apify or contact a webhook."""
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def validate(config):
    errors = []
    if not isinstance(config, dict):
        return ["input must be a JSON object"]
    allowed = {"startUrls", "resultsLimit", "viewOption", "onlyPostsNewerThan"}
    if set(config) - allowed:
        errors.append("unexpected input fields; review validator against actor schema")
    limit = config.get("resultsLimit")
    if type(limit) is not int or limit < 1:
        errors.append("resultsLimit must be a positive integer to bound usage")
    if config.get("viewOption") != "CHRONOLOGICAL":
        errors.append("daily collection requires CHRONOLOGICAL sorting")
    # This project's rolling lookback policy is deliberately narrower than the actor schema.
    lookback = config.get("onlyPostsNewerThan")
    if not isinstance(lookback, str) or not re.fullmatch(r"[1-9][0-9]* days?", lookback):
        errors.append("onlyPostsNewerThan must be a positive number of days")
    groups = config.get("startUrls")
    if not isinstance(groups, list) or not groups:
        return errors + ["startUrls must be a nonempty list"]
    seen = set()
    for index, item in enumerate(groups, 1):
        url = item.get("url") if isinstance(item, dict) else None
        if not isinstance(url, str):
            errors.append(f"group {index}: missing URL")
            continue
        try:
            parsed = urlsplit(url)
            valid = (parsed.scheme == "https" and parsed.netloc in
                     {"www.facebook.com", "facebook.com"} and
                     re.fullmatch(r"/groups/[A-Za-z0-9._-]+/?", parsed.path) and
                     not parsed.query and not parsed.fragment)
        except ValueError:
            valid = False
        if not valid:
            errors.append(f"group {index}: expected a clean HTTPS Facebook group URL")
            continue
        key = parsed.path.rstrip("/").lower()
        if key in seen:
            errors.append(f"group {index}: duplicate group URL")
        seen.add(key)
    return errors


def main():
    try:
        config = json.loads((ROOT / "apify-task-input.json").read_text())
    except (OSError, ValueError) as exc:
        print(f"Invalid input file: {exc}", file=sys.stderr)
        return 1
    errors = validate(config)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: {len(config['startUrls'])} unique group URLs; bounded chronological scrape.")
    print("Offline checks only. Live scheduling, delivery, and deduplication require service checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
