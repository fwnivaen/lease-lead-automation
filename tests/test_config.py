import copy
import json
from pathlib import Path
import unittest

from scripts.validate_config import validate


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((Path(__file__).resolve().parents[1] / "apify-task-input.json").read_text())

    def test_committed_config(self):
        self.assertEqual(validate(self.config), [])

    def test_duplicate_variants(self):
        duplicate = copy.deepcopy(self.config["startUrls"][0])
        duplicate["url"] = duplicate["url"].replace("www.facebook.com", "facebook.com").rstrip("/")
        self.config["startUrls"].append(duplicate)
        self.assertTrue(any("duplicate" in e for e in validate(self.config)))

    def test_invalid_urls(self):
        for url in ["http://www.facebook.com/groups/123/", "https://facebook.com.evil.test/groups/123/",
                    "https://www.facebook.com/groups/123/posts/456/", "https://www.facebook.com/groups/123/?token=secret",
                    "https://[invalid", "https://user:pass@facebook.com/groups/123/"]:
            with self.subTest(url=url):
                self.config["startUrls"] = [{"url": url}]
                self.assertTrue(validate(self.config))

    def test_malformed_and_unbounded_inputs(self):
        for config in [None, [], {}, {**self.config, "startUrls": [None]},
                       {**self.config, "startUrls": []}, {**self.config, "resultsLimit": True},
                       {**self.config, "resultsLimit": 0}, {**self.config, "onlyPostsNewerThan": "0 days"},
                       {**self.config, "viewOption": "TOP_POSTS"}]:
            with self.subTest(config=config):
                self.assertTrue(validate(config))


if __name__ == "__main__":
    unittest.main()
