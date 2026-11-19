"""
Tests for the Sorting Problem weight handling.

Run with: python -m unittest discover tests
"""
import json
import unittest
from unittest import mock

from xblock.field_data import DictFieldData
from xblock.scorable import Score
from xblock.test.tools import TestRuntime

from sortable.sortable import SortableXBlock


def make_block(**fields):
    runtime = TestRuntime(services={'field-data': DictFieldData(fields)})
    return SortableXBlock(runtime, scope_ids=mock.Mock())


def studio_save(block, weight='', max_attempts=''):
    data = {
        'display_name': 'Sort', 'question_text': 'q', 'max_attempts': max_attempts,
        'item_background_color': '', 'item_text_color': '', 'has_score': 1,
        'weight': weight, 'data': ['a', 'b', 'c'],
    }
    request = mock.Mock(method='POST', body=json.dumps(data).encode())
    return json.loads(block.studio_submit(request).body)


class WeightTest(unittest.TestCase):

    def test_blank_and_zero_mean_no_points(self):
        for weight in ('', '  ', '0', 0, None):
            block = make_block(weight=3.0)
            self.assertEqual(studio_save(block, weight)['result'], 'success', weight)
            # 0, not None: the LMS grader leaves weight 0 out of the grade.
            self.assertEqual(block.weight, 0.0, weight)
            self.assertFalse(block.student_view_data()['show_points'])

    def test_default_is_no_points(self):
        block = make_block()
        self.assertEqual(block.weight, 0.0)
        self.assertFalse(block.student_view_data()['show_points'])

    def test_positive_weight_is_saved_and_shown(self):
        block = make_block()
        self.assertEqual(studio_save(block, '2.5')['result'], 'success')
        self.assertEqual(block.weight, 2.5)
        self.assertTrue(block.student_view_data()['show_points'])

    def test_invalid_weight_is_rejected(self):
        for weight in ('-1', 'abc', 'nan', 'inf', '-inf'):
            block = make_block(weight=2.0)
            response = studio_save(block, weight)
            self.assertEqual(response['result'], 'error', weight)
            self.assertEqual(response['field'], 'weight', weight)
            self.assertEqual(block.weight, 2.0, weight)

    def test_invalid_max_attempts_names_its_field(self):
        response = studio_save(make_block(), max_attempts='-1')
        self.assertEqual(response['field'], 'max_attempts')

    def test_weighted_score(self):
        block = make_block()
        block.set_score(Score(0.5, 1))
        self.assertEqual(block.get_weighted_score(), (0.0, 0.0))  # default: no points
        block.weight = None
        self.assertEqual(block.get_weighted_score(), (0.5, 1))  # blank in OLX: raw score
        block.weight = 4.0
        self.assertEqual(block.get_weighted_score(), (2.0, 4.0))

    def test_decimal_weight_does_not_mark_wrong_answer_correct(self):
        block = make_block(weight=1.5, attempts=1)
        block.set_score(Score(2 / 3.0, 1))  # weighted 1.0 / 1.5
        view = block.student_view_data()
        self.assertFalse(view['error_indicator'])  # error_indicator is truthy when correct


if __name__ == '__main__':
    unittest.main()
