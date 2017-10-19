import uuid as uuid_tools

from django.db import models
from model_utils.models import TimeStampedModel
from django.contrib.auth.models import User
from course_modes.models import CourseMode


class CourseEntitlement(TimeStampedModel):
    """
    Represents a Student's Entitlement to a Course Run for a given Course.
    """

    user = models.ForeignKey(User)
    uuid = models.UUIDField(default=uuid_tools.uuid4, editable=False)

    # UUID for the Course, not the Course Run
    course_uuid = models.UUIDField()

    # The date that an entitlement expired
    # if NULL the entitlement has not expired
    expired_at = models.DateTimeField(null=True)

    # The mode of the Course that will be applied
    mode = models.CharField(default=CourseMode.DEFAULT_MODE_SLUG, max_length=100)

    # The ID of the course enrollment for this Entitlement
    # if NULL the entitlement is not in use
    enrollment_course_run = models.ForeignKey('student.CourseEnrollment', null=True)
    order_number = models.CharField(max_length=128, null=True)

    def to_json(self):
        run_key = None

        if self.enrollment_course_run is not None:
            run_key = self.enrollment_course_run.course_id

        return {
            'username': self.user.username,
            'uuid': str(self.uuid),
            'created': str(self.created),
            'modified': str(self.modified),
            'course_uuid': str(self.course_uuid),
            'expired_at': str(self.expired_at),
            'mode': self.mode,
            'enrollment_course_run_key': run_key,
            'order_number': self.order_number,
        }
