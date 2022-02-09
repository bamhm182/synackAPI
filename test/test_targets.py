"""test_Targets.py

Tests for the Targets Plugin
"""

import os
import sys
import unittest

from factories import ObjectFactory
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '../../src')))

import synack  # noqa: E402


class TargetsTestCase(unittest.TestCase):
    def setUp(self):
        self.state = synack._state.State()
        self.targets = synack.plugins.Targets(self.state)
        self.targets.api = MagicMock()
        self.targets.db = MagicMock()

    def test_get_assessments_all_passed(self):
        """Should return a list of passed assessments"""
        assessments = [
            {
                "category_name": "Cat1",
                "category_id": "1",
                "written_assessment": {
                    "passed": True
                },
                "practical_assessment": {
                    "passed": True
                }
            },
            {
                "category_name": "Cat2",
                "category_id": "2",
                "written_assessment": {
                    "passed": True
                },
                "practical_assessment": {
                    "passed": True
                }
            }
        ]
        self.targets.api.request.return_value.status_code = 200
        self.targets.api.request.return_value.json.return_value = assessments
        cat1 = ObjectFactory
        self.targets.db.categories = [cat1]
        self.assertEqual([cat1], self.targets.get_assessments())
        self.targets.db.update_categories.assert_called_with(assessments)

    def test_get_slug_from_codename(self):
        """Should return a slug for a given codename"""
        ret_targets = [ObjectFactory(slug="qwerty")]
        self.targets.db.filter_targets.return_value = ret_targets
        self.assertEqual("qwerty",
                         self.targets.get_slug_from_codename("qwerty"))
        self.targets.db.filter_targets.assert_called_with(codename="qwerty")

    def test_get_slug_from_codename_no_targets(self):
        """Should update the targets if empty"""
        self.targets.db.filter_targets.side_effect = [
            [],
            [ObjectFactory(slug="qwerty")]
        ]
        calls = [
            unittest.mock.call(codename="CHONKEYMONKEY"),
            unittest.mock.call(codename="CHONKEYMONKEY")
        ]
        self.targets.get_registered_summary = MagicMock()
        self.assertEqual("qwerty",
                         self.targets.get_slug_from_codename("CHONKEYMONKEY"))
        self.targets.db.filter_targets.assert_has_calls(calls)
        self.targets.get_registered_summary.assert_called_with()

    def test_get_codename_from_slug(self):
        """Should return a codename for a given slug"""
        ret_targets = [ObjectFactory(codename="SLOPPYSLUG")]
        self.targets.db.filter_targets.return_value = ret_targets
        self.assertEqual("SLOPPYSLUG",
                         self.targets.get_codename_from_slug("qwfars"))
        self.targets.db.filter_targets.assert_called_with(slug="qwfars")

    def test_get_codename_from_slug_no_targets(self):
        """Should update the targets if empty"""
        self.targets.db.filter_targets.side_effect = [
            [],
            [ObjectFactory(codename="SLOPPYSLUG")]
        ]
        calls = [
            unittest.mock.call(slug="qwfars"),
            unittest.mock.call(slug="qwfars")
        ]
        self.targets.get_registered_summary = MagicMock()
        self.assertEqual("SLOPPYSLUG",
                         self.targets.get_codename_from_slug("qwfars"))
        self.targets.db.filter_targets.assert_has_calls(calls)
        self.targets.get_registered_summary.assert_called_with()

    def test_get_current_target(self):
        """Should make a request to get the currently selected target"""
        self.targets.api.request.return_value.status_code = 200
        self.targets.api.request.return_value.json.return_value = {
            "pending_slug": "-1",
            "slug": "qwfars",
            "status": "connected"
        }
        self.targets.get_codename_from_slug = MagicMock()
        self.targets.get_codename_from_slug.return_value = "SLOPPYSLUG"
        out = {
            "slug": "qwfars",
            "codename": "SLOPPYSLUG",
            "status": "Connected"
        }
        self.assertEqual(out, self.targets.get_current_target())

    def test_get_current_target_pending(self):
        """Should return the pending target if one is pending"""
        self.targets.api.request.return_value.status_code = 200
        self.targets.api.request.return_value.json.return_value = {
            "pending_slug": "qwfars",
            "slug": "",
            "status": ""
        }
        self.targets.get_codename_from_slug = MagicMock()
        self.targets.get_codename_from_slug.return_value = "SLOPPYSLUG"
        out = {
            "slug": "qwfars",
            "codename": "SLOPPYSLUG",
            "status": "Connecting"
        }
        self.assertEqual(out, self.targets.get_current_target())

    def test_get_registered_summary(self):
        """Should make a request to get basic info about registered targets"""
        t1 = {
            "id": "qwfars",
            "codename": "SLOPPYSLUG",
            "organization_id": "89yefds",
            "activated_at": 1633640638,
            "name": "Bob's Slug Hut",
            "category": {
                "id": 1,
                "name": "Web Application"
            },
            "outage_windows": [],
            "vulnerability_discovery": True
        }
        self.targets.api.request.return_value.status_code = 200
        self.targets.api.request.return_value.json.return_value = [t1]
        out = {
            "qwfars": t1
        }
        path = 'targets/registered_summary'
        self.assertEqual(out, self.targets.get_registered_summary())
        self.targets.api.request.assert_called_with('GET', path)

    def test_get_unregistered(self):
        """Should get a list unregistered targets"""
        self.targets.db.categories = [
            ObjectFactory(id=1, practical_passed=True, written_passed=True),
            ObjectFactory(id=2, practical_passed=True, written_passed=True),
            ObjectFactory(id=3, practical_passed=False, written_passed=False),
        ]
        query = {
            'filter[primary]': 'unregistered',
            'filter[secondary]': 'all',
            'filter[industry]': 'all',
            'filter[category][]': [1, 2]
        }
        self.targets.api.request.return_value.status_code = 200
        unreg = [
            {
                "codename": "SLEEPYSLUG",
                "slug": "1o2h8o"
            }
        ]
        self.targets.api.request.return_value.json.return_value = unreg
        self.assertEqual(unreg, self.targets.get_unregistered())
        self.targets.api.request.assert_called_with("GET",
                                                    "targets",
                                                    query=query)

    def test_get_unregistered_assessments_empty(self):
        """Should get a list of unregistered targets"""
        self.targets.get_assessments = MagicMock()
        self.targets.db.categories = []
        query = {
            'filter[primary]': 'unregistered',
            'filter[secondary]': 'all',
            'filter[industry]': 'all',
            'filter[category][]': []
        }
        self.targets.api.request.return_value.status_code = 200
        unreg = []
        self.targets.api.request.return_value.json.return_value = unreg
        self.assertEqual(unreg, self.targets.get_unregistered())
        self.targets.get_assessments.assert_called_with()
        self.targets.api.request.assert_called_with("GET",
                                                    "targets",
                                                    query=query)

    def test_do_register_all(self):
        """Should register each unregistered target"""
        self.targets.get_unregistered = MagicMock()
        unreg = [
            {
                "codename": "SLEEPYSLUG",
                "slug": "1o2h8o"
            },
            {
                "codename": "SLEEPYWALRUS",
                "slug": "82h934"
            }
        ]
        calls = [
            unittest.mock.call("POST",
                               "targets/1o2h8o/signup",
                               data='{"ResearcherListing":{"terms":1}}'),
            unittest.mock.call("POST",
                               "targets/82h934/signup",
                               data='{"ResearcherListing":{"terms":1}}')
        ]
        self.targets.get_unregistered.return_value = unreg
        self.targets.api.request.return_value.status_code = 200
        self.assertEqual(unreg, self.targets.do_register_all())
        self.targets.api.request.assert_has_calls(calls)

    def test_do_register_all_many(self):
        """Should call itself again if it has determined the page was full"""
        self.targets.get_unregistered = MagicMock()
        t = {
            "codename": "SLEEPYSLUG",
            "slug": "1o2h8o"
        }
        unreg = []
        for i in range(0, 15):
            unreg.append(t)
        self.targets.get_unregistered.side_effect = [unreg, [t, t]]
        self.targets.api.request.return_value.status_code = 200
        self.assertEqual(17, len(self.targets.do_register_all()))
