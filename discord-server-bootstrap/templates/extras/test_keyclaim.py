import os
import tempfile
import unittest

from keyclaim import ClaimStore, FailureLimiter, claim_key, load_keys, mask_email, normalize_email


class KeyClaimTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = ClaimStore(os.path.join(self.dir.name, "claims.json"))
        self.keys = {"ann@example.com": "sk-ann-FAKE", "bob@example.com": "sk-bob-FAKE"}

    def tearDown(self):
        self.dir.cleanup()

    def test_load_keys_handles_csv_tsv_header_quotes_and_case(self):
        path = os.path.join(self.dir.name, "keys.csv")
        with open(path, "w", encoding="utf-8-sig") as file:
            file.write('email,key,budget\n"Ann@Example.com","sk-ann-FAKE",100\nbob@example.com\tsk-bob-FAKE\tUS$100\nbroken-line-no-key@example.com\n')
        self.assertEqual(load_keys(path), {"ann@example.com": "sk-ann-FAKE", "bob@example.com": "sk-bob-FAKE"})

    def test_email_matching_ignores_case_and_spaces(self):
        result = claim_key(self.keys, self.store, "  ANN@Example.COM ", 1)
        self.assertEqual((result.status, result.key), ("claimed", "sk-ann-FAKE"))

    def test_unknown_email(self):
        self.assertEqual(claim_key(self.keys, self.store, "nobody@example.com", 1).status, "not_found")

    def test_same_member_gets_the_same_key_again(self):
        claim_key(self.keys, self.store, "ann@example.com", 1)
        result = claim_key(self.keys, self.store, "ann@example.com", 1)
        self.assertEqual((result.status, result.key), ("repeat", "sk-ann-FAKE"))

    def test_other_member_can_not_take_a_claimed_key(self):
        claim_key(self.keys, self.store, "ann@example.com", 1)
        result = claim_key(self.keys, self.store, "ann@example.com", 2)
        self.assertEqual((result.status, result.key), ("taken", None))

    def test_member_can_not_collect_a_second_key(self):
        claim_key(self.keys, self.store, "ann@example.com", 1)
        result = claim_key(self.keys, self.store, "bob@example.com", 1)
        self.assertEqual((result.status, result.key), ("other_email", None))

    def test_clear_lets_the_key_be_claimed_again(self):
        claim_key(self.keys, self.store, "ann@example.com", 1)
        self.assertTrue(self.store.clear("ann@example.com"))
        self.assertFalse(self.store.clear("ann@example.com"))
        self.assertEqual(claim_key(self.keys, self.store, "ann@example.com", 2).status, "claimed")

    def test_claims_survive_a_restart(self):
        claim_key(self.keys, self.store, "ann@example.com", 1)
        reopened = ClaimStore(self.store.path)
        self.assertEqual(claim_key(self.keys, reopened, "ann@example.com", 2).status, "taken")

    def test_limiter_blocks_after_five_failures_and_recovers(self):
        limiter = FailureLimiter(max_failures=5, window_seconds=3600)
        for _ in range(5):
            self.assertFalse(limiter.blocked(7, now=1000))
            limiter.record(7, now=1000)
        self.assertTrue(limiter.blocked(7, now=1001))
        self.assertFalse(limiter.blocked(8, now=1001))
        self.assertFalse(limiter.blocked(7, now=1000 + 3601))

    def test_helpers(self):
        self.assertEqual(normalize_email(" A@B.com "), "a@b.com")
        self.assertEqual(mask_email("ann@example.com"), "a***@example.com")


if __name__ == "__main__":
    unittest.main()
