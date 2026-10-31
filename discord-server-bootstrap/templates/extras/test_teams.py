import os
import tempfile
import unittest

from teams import MAX_NAME_LENGTH, TeamStore


class TeamStoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = TeamStore(os.path.join(self.dir.name, "teams.json"))

    def tearDown(self):
        self.dir.cleanup()

    def test_create_stores_the_team_with_a_cleaned_name(self):
        result = self.store.create("  Pumpkin   Patch ", [1, 2, 2])
        self.assertEqual(result.status, "ok")
        self.assertEqual((result.team.name, result.team.member_ids), ("Pumpkin Patch", [1, 2]))

    def test_name_is_unique_ignoring_case_and_spacing(self):
        self.store.create("Pumpkin Patch", [1])
        self.assertEqual(self.store.create("pumpkin  patch", [2]).status, "name_taken")

    def test_empty_and_overlong_names_are_rejected(self):
        self.assertEqual(self.store.create("   ", [1]).status, "bad_name")
        self.assertEqual(self.store.create("x" * (MAX_NAME_LENGTH + 1), [1]).status, "bad_name")

    def test_team_of_five_is_rejected(self):
        self.assertEqual(self.store.create("Big", [1, 2, 3, 4, 5]).status, "too_many")

    def test_a_person_joins_one_team_only(self):
        self.store.create("A", [1, 2])
        result = self.store.create("B", [3, 2])
        self.assertEqual((result.status, result.user_id), ("already_on_team", 2))
        self.assertIsNone(self.store.get("B"))

    def test_leave_keeps_the_team_until_the_last_member_goes(self):
        self.store.create("A", [1, 2])
        self.assertFalse(self.store.leave(1).disbanded)
        self.assertIsNone(self.store.team_of(1))
        outcome = self.store.leave(2)
        self.assertTrue(outcome.disbanded)
        self.assertIsNone(self.store.get("A"))

    def test_leave_without_a_team_returns_nothing(self):
        self.assertIsNone(self.store.leave(9))

    def test_a_member_can_join_a_new_team_after_leaving(self):
        self.store.create("A", [1, 2])
        self.store.leave(1)
        self.assertEqual(self.store.create("B", [1]).status, "ok")

    def test_remove_frees_the_name_and_members(self):
        self.store.create("A", [1])
        self.assertIsNotNone(self.store.remove("a"))
        self.assertIsNone(self.store.remove("a"))
        self.assertEqual(self.store.create("A", [1]).status, "ok")

    def test_add_member_joins_an_existing_team(self):
        self.store.create("A", [1])
        result = self.store.add_member("a", 2)
        self.assertEqual((result.status, result.team.member_ids), ("ok", [1, 2]))
        self.assertEqual(self.store.team_of(2).name, "A")

    def test_add_member_stops_at_four(self):
        self.store.create("A", [1, 2, 3, 4])
        result = self.store.add_member("A", 5)
        self.assertEqual(result.status, "full")
        self.assertIsNone(self.store.team_of(5))

    def test_add_member_rejects_someone_on_another_team(self):
        self.store.create("A", [1])
        self.store.create("B", [2])
        result = self.store.add_member("A", 2)
        self.assertEqual((result.status, result.user_id), ("already_on_team", 2))
        self.assertEqual(self.store.get("A").member_ids, [1])

    def test_add_member_rejects_someone_already_on_the_team(self):
        self.store.create("A", [1])
        self.assertEqual(self.store.add_member("A", 1).status, "already_member")

    def test_add_member_to_a_missing_team(self):
        self.assertEqual(self.store.add_member("Nope", 1).status, "no_team")

    def test_added_members_survive_a_restart(self):
        self.store.create("A", [1])
        self.store.add_member("A", 2)
        self.assertEqual(TeamStore(self.store.path).team_of(2).name, "A")

    def test_teams_and_channels_survive_a_restart(self):
        self.store.create("A", [1, 2])
        self.store.set_channel("A", 555)
        reopened = TeamStore(self.store.path)
        self.assertEqual((reopened.get("a").channel_id, reopened.team_of(2).name), (555, "A"))


if __name__ == "__main__":
    unittest.main()
