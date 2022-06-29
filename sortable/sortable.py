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
    GRADED_FEEDBACK_MESSAGES = [_('Incorrect ({}/{})'), _('Correct ({}/{})')]
    UNGRADED_FEEDBACK_MESSAGES = [_('Incorrect'), _('Correct')]
    GRADED_TOP_MESSAGE = _('{}/{} point (graded)')
    UPGRADED_TOP_MESSAGE = _('{} point possible (ungraded)')
    ATTEMPTS_FEEDBACK = _('You have used {} of {} attempts')

    DEFAULT_DATA = ["Australia", "China", "Finland", "Pakistan", "United States"]

    weight = Float(
        display_name=_("Problem Weight"),
        help=_("Defines the number of points the problem is worth."),
        scope=Scope.settings,
        default=1,
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
        Get data based on last submission
        """
        data = []
        for index in submissions:
            data.append(self.data[index])
        return data
    
    def get_weighted_score(self):
        """
        Get weighted scores
        """
        return self.raw_earned*self.weight, self.raw_possible*self.weight

    def get_items_with_state(self, items):
        """
        Add correct status i.e True or False with every option
        """
        states = []
        if self.attempts == 0:
            states = [True for _ in range(len(items))]
        elif (len(items)==len(self.user_sequence)):
            states = [state==index for index, state in enumerate(self.user_sequence)]
        else:
            states = [False for _ in range(len(items))]
        return zip(items, states)
    
    def student_view_data(self):
        """
        Context for student view
        """
        items = self.data[:]
        if self.attempts and self.user_sequence:
            items = self.shuffle_data_based_on_submission(self.user_sequence)
        else:
            random.shuffle(items)

        user_score, max_score = self.get_weighted_score()
        is_correct = int(self.raw_earned)==int(self.raw_possible)
        is_graded = getattr(self, 'graded', False)
        
        progress_info = ''   
        if is_graded and bool(self.weight):
            progress_info = SortableXBlock.GRADED_TOP_MESSAGE.format(user_score, int(max_score))
        else:
            progress_info = SortableXBlock.UPGRADED_TOP_MESSAGE.format(int(max_score))
        
        attemps_info = SortableXBlock.ATTEMPTS_FEEDBACK.format(self.attempts, self.max_attempts)

        return {
            'display_name': self.display_name,
            'question_text': self.question_text,
            'max_attempts': self.max_attempts,
            'attempts': self.attempts,
            'item_background_color': self.item_background_color,
            'item_text_color': self.item_text_color,
            'completed': self.completed,
            'graded': is_graded,
            'error_indicator': bool(self.attempts) and not is_correct,
            'success_indicator': bool(self.attempts) and is_correct,
            'items': self.get_items_with_state(items),
            'progress_info': progress_info,
            'attempts_info': attemps_info,
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
        frag.add_javascript(self.resource_string("static/js/vendor/sortable.min.js"))
        frag.add_javascript(self.resource_string("static/js/src/sortable.js"))

        frag.initialize_js('SortableXBlock')
        return frag

    def _get_submission_indexes(self, submission):
        """
        Get postions of submission list
        """
        assert len(submission) == len(self.data)
        user_submission = []
        for item in self.data:
            user_submission.append(submission.index(item))
        return user_submission 

    def _calculate_grade(self, submission):
        """
        Calculate grade based on correct possitions of strings
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
        if not self.remaining_attempts:
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
        self.completed = int(self.raw_earned) or not self.remaining_attempts
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
        is_graded = getattr(self, 'graded', False)
        
        message = ''
        progress_info = ''
        if is_graded and bool(self.weight):
            message = SortableXBlock.GRADED_FEEDBACK_MESSAGES[int(self.raw_earned)].format(earned, total)
            progress_info = SortableXBlock.GRADED_TOP_MESSAGE.format(earned, int(total))
        else:
            message = SortableXBlock.UNGRADED_FEEDBACK_MESSAGES[int(self.raw_earned)]
            progress_info = SortableXBlock.UPGRADED_TOP_MESSAGE.format(int(total))
        attempts_info = SortableXBlock.ATTEMPTS_FEEDBACK.format(self.attempts, self.max_attempts)
        
        return {
            'correct': int(self.raw_earned)==int(self.max_score()),
            'attempts': self.attempts,
            'grade': earned,
            'remaining_attempts': self.remaining_attempts,
            'state': self.user_sequence,
            'message': message,
            'progress_info': progress_info,
            'attempts_info': attempts_info,
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
