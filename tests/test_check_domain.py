import unittest
from urllib.error import URLError

import scripts.check_domain as cd


class TestCheckDomain(unittest.TestCase):
    def test_fetch_domain_for_urn_found(self):
        orig = cd.graphql_query

        def fake_graphql_query(gms, query, variables, timeout=10.0):
            return {
                "data": {
                    "dataset": {
                        "urn": variables["urn"],
                        "domain": {
                            "domain": {
                                "urn": "urn:li:domain:obsidian_notes",
                                "id": "obsidian_notes",
                                "properties": {
                                    "name": "obsidian_notes",
                                    "description": "Domain for Obsidian notes",
                                },
                            }
                        },
                    }
                }
            }

        try:
            cd.graphql_query = fake_graphql_query
            res = cd.fetch_domain_for_urn("urn:li:dataset:test", "http://localhost:8080", timeout=5.0)
            self.assertEqual(res["urn"], "urn:li:dataset:test")
            self.assertIsNone(res["error"])
            self.assertIsInstance(res["domain"], dict)
            self.assertEqual(res["domain"]["id"], "obsidian_notes")
        finally:
            cd.graphql_query = orig

    def test_fetch_domain_for_urn_not_found(self):
        orig = cd.graphql_query

        def fake_graphql_query(gms, query, variables, timeout=10.0):
            return {"data": {"dataset": None}}

        try:
            cd.graphql_query = fake_graphql_query
            res = cd.fetch_domain_for_urn("urn:li:dataset:missing", "http://localhost:8080", timeout=5.0)
            self.assertEqual(res["error"], "not_found")
            self.assertIsNone(res["domain"])
        finally:
            cd.graphql_query = orig

    def test_fetch_with_retries_network_error(self):
        orig = cd.graphql_query
        calls = {"n": 0}

        def fake_graphql_query(gms, query, variables, timeout=10.0):
            calls["n"] += 1
            raise URLError("simulated network failure")

        try:
            cd.graphql_query = fake_graphql_query
            res = cd.fetch_with_retries(
                "urn:li:dataset:test",
                "http://localhost:8080",
                retries=2,
                delay=0.0,
                timeout=1.0,
            )
            self.assertEqual(res["error"], "network_error")
            self.assertIn("simulated network failure", res["exception"])
        finally:
            cd.graphql_query = orig


if __name__ == '__main__':
    unittest.main()
