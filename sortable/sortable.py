"""Sortable XBlock"""
import random
import pkg_resources
from xblock.core import XBlock
from xblock.exceptions import JsonHandlerError
from xblock.fields import Integer, Scope, String, List, Boolean, Float, Dict
from xblock.scorable import ScorableXBlockMixin, Score
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader

from .utils import _, DummyTranslationService


loader = ResourceLoader(__name__)


@XBlock.needs('i18n')
class SortableXBlock(ScorableXBlockMixin ,XBlock):
    """
    An XBlock for sorting problems.
    """
    FEEDBACK_MESSAGES = [_('Incorrect ({}/{})'), _('Correct ({}/{})')]
    DEFAULT_DATA = ["Australia", "China", "Finland", "Pakistan", "United States"]

    weight = Float(
        display_name=_("Problem Weight"),
        help=_("Defines the number of points the problem is worth."),
        scope=Scope.settings,
        default=1,
        enforce_type=True,
    )

    has_score = Boolean(
        display_name=_("Is Graded?"),
        help=_("A graded or ungraded problem"),
        scope=Scope.settings,
        default=True,
        enforce_type=True,
    )

    display_name = String(
        display_name=_("Title"),
        help=_("The title of the sorting problem. The title is displayed to learners."),
        scope=Scope.settings,
        default=_("Sorting Problem"),
        enforce_type=True,
    )

    question_text = String(
        display_name=_("Problem text"),
        help=_("The description of the problem or instructions shown to the learner."),
        scope=Scope.settings,
        default=_("Sort the following country names in alphabetical order"),
        enforce_type=True,
    )

    max_attempts = Integer(
        display_name=_("Maximum attempts"),
        help=_(
            "Defines the number of times a student can try to answer this problem. "
            "If the value is not set, infinite attempts are allowed."
        ),
        scope=Scope.settings,
        default=1,
        enforce_type=True,
    )

    item_background_color = String(
        display_name=_("Item background color"),
        help=_("The background color of sortable items"),
        scope=Scope.settings,
        default="#f2f2f2",
        enforce_type=True,
    )

    item_text_color = String(
        display_name=_("Item text color"),
        help=_("The text color of sortable items"),
        scope=Scope.settings,
        default="#000000",
        enforce_type=True,
    )

    data = List(
        display_name=_("Sortable Items"),
        help=_("Order will be randomized when presented to students"),
        scope=Scope.content,
        default=DEFAULT_DATA,
        enforce_type=True,
    )

    attempts = Integer(
        help=_("Number of attempts learner used"),
        scope=Scope.user_state,
        default=0,
        enforce_type=True,
    )

    completed = Boolean(
        help=_("Indicates whether a learner has completed the problem successfully at least once"),
        scope=Scope.user_state,
        default=False,
        enforce_type=True,
    )

    raw_earned = Float(
        help=_("Keeps maximum score achieved by student as a raw value between 0 and 1."),
        scope=Scope.user_state,
        default=0,
        enforce_type=True,
    )

    raw_possible = Float(
        help=_("Maximum score available of the problem as a raw value between 0 and 1."),
        scope=Scope.user_state,
        default=1,
        enforce_type=True,
    )

    user_sequence = List(
        help = _("User selected sequence"),
        scope=Scope.user_state,
        default=[],
        enforce_type=True,
    )    
    
    @property
    def remaining_attempts(self):
        """Remaining number of attempts"""
        return self.max_attempts - self.attempts
    
    @property
    def score(self):
        """
        Returns learners saved score.
        """
        return Score(self.raw_earned, self.raw_possible)

    def max_score(self):  # pylint: disable=no-self-use
        """
        Return the problem's max score, which for DnDv2 always equals 1.
        Required by the grading system in the LMS.
        """
        return 1

    def set_score(self, score):
        """
        Sets the score on this block.
        Takes a Score namedtuple containing a raw
        score and possible max (for this block, we expect that this will
        always be 1).
        """
        self.raw_earned = score.raw_earned
        self.raw_possible = score.raw_possible

    def resource_string(self, path):  # pylint: disable=no-self-use
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def shuffle_data_based_on_submission(self, submissions):
        """
        Put the items back in the order the learner submitted them.
        `submissions[i]` is the submitted position of `self.data[i]`.
        """
        data = [None] * len(submissions)
        for index, position in enumerate(submissions):
            data[position] = self.data[index]
        return data

    def _has_current_submission(self):
        """
        True when the learner's saved order still fits the items: one distinct
        position per item. If the author adds or removes items afterwards, the
        saved order no longer applies.
        """
        return bool(self.attempts) and sorted(self.user_sequence) == list(range(len(self.data)))

    def _is_locked(self):
        """
        Nothing left to do: the answer is correct or no attempts remain. Read
        from the current settings, so an author raising the limit unlocks it.
        """
        return int(self.raw_earned) >= int(self.max_score()) or self.remaining_attempts <= 0

    def get_weighted_score(self):
        """
        Get weighted scores
        """
        return self.raw_earned*self.weight, self.raw_possible*self.weight

    def get_items_with_state(self, items):
        """
        Pair each displayed item with its state class: 'correct' or 'incorrect'
        after a submission, '' before the first one.
        """
        if not self._has_current_submission():
            return [(item, '') for item in items]
        return [
            (item, 'correct' if item == self.data[position] else 'incorrect')
            for position, item in enumerate(items)
        ]

    def item_style(self):
        """
        Inline CSS custom properties for author-chosen item colours. Colours
        left at their defaults emit nothing, so the theme's own styles apply.
        """
        properties = []
        for field_name, css_property in (
            ('item_background_color', '--sortable-item-bg'),
            ('item_text_color', '--sortable-item-color'),
        ):
            value = getattr(self, field_name).strip()
            if value and value.lower() != self.fields[field_name].default.lower():
                properties.append('{}: {}'.format(css_property, value))
        return '; '.join(properties)

    def student_view_data(self):
        """
        Context for student view
        """
        items = self.data[:]
        if self._has_current_submission():
            items = self.shuffle_data_based_on_submission(self.user_sequence)
        else:
            random.shuffle(items)

        user_score, max_score = self.get_weighted_score()
        is_correct = int(user_score)==int(max_score)
        return {
            'display_name': self.display_name,
            'question_text': self.question_text,
            'max_attempts': self.max_attempts,
            'attempts': self.attempts,
            'item_background_color': self.item_background_color,
            'item_text_color': self.item_text_color,
            'completed': self.completed,
            'graded': self.has_score,
            'user_score': user_score,
            'max_score': max_score,
            'error_indicator': self.attempts and is_correct,
            'success_indicator': self.attempts and not is_correct,
            'item_style': self.item_style(),
            'locked': self._is_locked(),
            'items': self.get_items_with_state(items)
        }
    
    def student_view(self, context=None):
        """
        The primary view of the SortableXBlock, shown to students
        when viewing courses.
        """
        frag = Fragment()
        
        frag.add_content(loader.render_django_template(
            'static/html/sortable.html',
            context=self.student_view_data(),
            i18n_service=self.i18n_service
        ))
        frag.add_css(self.resource_string("static/css/sortable.css"))
        frag.add_javascript(self.resource_string("static/js/vendor/jquery.ui.touch-punch.min.js"))
        frag.add_javascript(self.resource_string("static/js/src/sortable.js"))

        frag.initialize_js('SortableXBlock')
        return frag

    def _get_submission_indexes(self, submission):
        """
        Get positions of submission list. Repeated items each take the next
        unused position, so the result is always a reordering of the positions.
        """
        assert len(submission) == len(self.data)
        user_submission = []
        for item in self.data:
            user_submission.append(next(
                position for position, value in enumerate(submission)
                if value == item and position not in user_submission
            ))
        return user_submission

    def _submission_marks(self, submission):
        """
        'correct' or 'incorrect' for each submitted position, by item text.
        """
        return ['correct' if value == item else 'incorrect' for value, item in zip(submission, self.data)]

    def _calculate_grade(self, submission):
        """
        Calculate grade based on correct positions of strings
        """
        assert len(submission) == len(self.data)
        correctly_placed = 0
        for index, item in enumerate(self.data):
            if item == submission[index]:
                correctly_placed += 1
        grade = (correctly_placed / float(len(self.data)))
        return grade

    def _validate_do_attempt(self):
        """
        Validates if `submit_answer` handler should be executed
        """
        if self.remaining_attempts <= 0:
            raise JsonHandlerError(
                409,
                self.i18n_service.gettext("Max number of attempts reached")
            )
    
    def _mark_complete_and_publish_grade(self, submission):
        """
        Update complete status and publish grade based on user submission
        """
        score = self._calculate_grade(submission)
        
        self.set_score(Score(score, self.max_score()))
        self.completed = self._is_locked()
        self.user_sequence = self._get_submission_indexes(submission)
        self.publish_grade(self.score, False)

        # and no matter what - emit progress event for current user
        self.runtime.publish(self, "progress", {})
    
    @XBlock.json_handler
    def submit_answer(self, submission, suffix=''):
        """
        Checks submitted solution and returns feedback.
        """
        self._validate_do_attempt()

        self.attempts += 1

        self._mark_complete_and_publish_grade(submission)
        
        earned = self.raw_earned*self.weight
        total = self.max_score()*self.weight

        message = SortableXBlock.FEEDBACK_MESSAGES[int(self.raw_earned)].format(earned, total)
        
        return {
            'correct': int(self.raw_earned)==int(self.max_score()),
            'attempts': self.attempts,
            'grade': earned,
            'remaining_attempts': self.remaining_attempts,
            'state': self.user_sequence,
            'marks': self._submission_marks(submission),
            'message': message,
        }

    def studio_view(self, context):
        """
        Editing view in Studio
        """
        frag = Fragment()
        context = {
            'self': self,
            'fields': self.fields,
            'data': self.data,
        }
        frag.add_content(loader.render_django_template(
            'static/html/sortable_edit.html',
            context=context,
            i18n_service=self.i18n_service
        ))
        frag.add_css(self.resource_string("static/css/sortable_edit.css"))
        frag.add_javascript(self.resource_string("static/js/src/sortable_edit.js"))

        frag.initialize_js('SortableXBlockEdit')
        return frag

    @XBlock.json_handler
    def studio_submit(self, submissions, suffix=''):
        """
        Handles studio save.
        """
        self.display_name = submissions['display_name']
        self.max_attempts = submissions['max_attempts']
        self.question_text = submissions['question_text']
        self.item_background_color = submissions['item_background_color']
        self.item_text_color = submissions['item_text_color']
        self.has_score = bool(submissions['has_score'])
        self.weight = float(submissions['weight'])
        self.data = submissions['data']

        return {
            'result': 'success',
        }
    
    def publish_grade(self, score=None, only_if_higher=None):
        """
        Publishes the student's current grade to the system as an event
        """
        if not score:
            score = self.score
        self._publish_grade(score, only_if_higher)
        return {'grade': self.score.raw_earned, 'max_grade': self.score.raw_possible}

    @property
    def i18n_service(self):
        """ Obtains translation service """
        i18n_service = self.runtime.service(self, "i18n")
        if i18n_service:
            return i18n_service
        return DummyTranslationService()

    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("SortableXBlock",
             """<sortable/>
             """),
            ("Multiple SortableXBlock",
             """<vertical_demo>
                <sortable/>
                <sortable/>
                <sortable/>
                </vertical_demo>
             """),
        ]
