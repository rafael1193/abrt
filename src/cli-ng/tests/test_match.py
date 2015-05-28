#!/usr/bin/python
# -*- encoding: utf-8 -*-
import logging
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import clitests

from abrtcli.match import get_match_data, match_completer, match_lookup


class MatchTestCase(clitests.TestCase):
    '''
    Simple test to check if database creation & access
    works as expected.
    '''

    hashes = ['ccacca5', 'bc60a5c', 'acbea5c', 'ffe635c']
    collision_hash = 'bc60a5c'
    human = ['/home/user/bin/user_app', 'unknown_problem', 'polkitd']
    collision_human = 'pavucontrol'
    combined = ['pavucontrol@bc60a5c', 'pavucontrol@acbea5c']

    def test_get_match_data(self):
        '''
        Test get_match_data returns correctly merged data
        '''

        by_human_id, by_short_id = get_match_data()
        self.assertEqual(len(by_human_id), 4)

        self.assertEqual(len(by_short_id), 4)

    def test_match_completer(self):
        '''
        Test that match_completer yields properly formatted candidates
        '''

        pm = match_completer(None, None)
        self.assertEqual(set(pm), set(self.hashes + self.human + self.combined))

    def test_match_lookup_hash(self):
        '''
        Test match lookup by hash
        '''

        for h in self.hashes:
            m = match_lookup(h)
            self.assertTrue(len(m) >= 1)

    def test_match_lookup_human_id(self):
        '''
        Test match lookup by human id
        '''

        for h in self.human:
            m = match_lookup(h)
            self.assertTrue(len(m) == 1)

    def test_match_lookup_combined(self):
        '''
        Test match lookup by human id
        '''

        for h in self.combined:
            m = match_lookup(h)
            self.assertTrue(len(m) == 1)

    def test_match_lookup_collisions(self):
        '''
        Test match lookup handles collisions
        '''

        m = match_lookup(self.collision_hash)
        self.assertTrue(len(m) == 2)

        m = match_lookup(self.collision_human)
        self.assertTrue(len(m) == 2)

    def test_match_lookup_nonexistent(self):
        '''
        Test match lookup handles empty input
        '''

        m = match_lookup('')
        self.assertEqual(m, None)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
