import uuid
from datetime import datetime

from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import permissions, status
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from student.models import CourseEnrollment
from .filters import CourseEntitlementFilter
from .models import CourseEntitlement
from .serializers import CourseEntitlementSerializer

SESSION_CLASSES = (JwtAuthentication, SessionAuthentication)
PERMISSION_CLASSES = (permissions.IsAuthenticated, permissions.IsAdminUser)


class EntitlementViewSet(viewsets.ModelViewSet):
    authentication_classes = SESSION_CLASSES
    permission_classes = PERMISSION_CLASSES
    queryset = CourseEntitlement.objects.all()
    lookup_value_regex = '[0-9a-f-]+'
    lookup_field = 'uuid'
    serializer_class = CourseEntitlementSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = CourseEntitlementFilter

    def perform_destroy(self, instance):
        """
        Expire and revoke the provided Entitlements UUID and unenroll the User if enrolled
        """
        if instance.expired_at is None:
            instance.expired_at = datetime.now()
            instance.save()

        # if the entitlement is enrolled we need to unenroll the user
        if instance.enrollment_course_run is not None:
            CourseEnrollment.unenroll(
                user=instance.user,
                course_id=instance.enrollment_course_run.course_id,
                skip_refund=True
            )
            instance.enrollment_course_run = None
            instance.save()
