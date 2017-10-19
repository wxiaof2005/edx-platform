import uuid
from datetime import datetime

from django.contrib.auth.models import User
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from student.models import CourseEnrollment
from .models import CourseEntitlement

SESSION_CLASSES = (JwtAuthentication, SessionAuthentication)
PERMISSION_CLASSES = (permissions.IsAuthenticated, permissions.IsAdminUser)


def _get_updated_entitlement_data_fields(request):
    """
    Get the updated entitlement data fields from the request

    Arguments:
        request: Request object
    Returns:
        Dict: A dictionary containing only the updated data fields
    """
    request_data = {
        'course_uuid': request.data.get('course_uuid', None),
        'mode': request.data.get('mode', None),
        'username': request.data.get('username', None),
        'order_number': request.data.get('order_number', None),
    }
    return dict((k, v) for k, v in request_data.iteritems() if v)


def _get_response_object(course_entitlements):
    """
    Build the response dictionary for the Response

    Arguments:
        course_entitlements (list): A list containing 1 or more CourseEntitlements
    Returns:
        Dict: A dictionary containing the results list
    """
    results_list = []
    for entitlement in course_entitlements:
        results_list.append(entitlement.to_json())
    return {'results': results_list}


class EntitlementView(APIView):
    authentication_classes = SESSION_CLASSES
    permission_classes = PERMISSION_CLASSES

    def _get_clear_entitlements_params_filter_data(self, request):
        """
        Get all the parameter Keys and values and clear out any that are None/not available

        Arguments:
            request: Request Object
        Returns:
            Dict: Dictionary containing all the Parameters that are not None
        """
        request_data = {
            'uuid': request.query_params.get('uuid', None),
            'mode': request.query_params.get('mode', None),
            'username': request.query_params.get('username', None),
            'order_number': request.query_params.get('order_number', None),
        }
        return dict((k, v) for k, v in request_data.iteritems() if v)

    def get(self, request):
        """
        Get the entitlement or entitlement based on the provided query filters of all if not filtered

        TODO: Add pagination for large get requests, until then limit to 100
        """
        if len(request.query_params) > 0:
            course_entitlements = CourseEntitlement.objects.filter(
                **self._get_clear_entitlements_params_filter_data(request)
            ).all().all()
        else:
            course_entitlements = list(CourseEntitlement.objects.all()[0:100])

        return Response(
            status=status.HTTP_200_OK,
            data=_get_response_object(course_entitlements)
        )

    def post(self, request):
        """
        Handler for POST requests to the entitlement API to add a new Entitlement

        Expected Data model
            {
                "username": <username>,
                "course_uuid": <course_uuid>,
                "mode": <mode>, # e.g. verified, credit, audit
                "order_number": <order_number>
            }
        Arguments:
            request: The request object

        Returns:
            Response: The Response object with an appropriate Status code and data
        """
        course_uuid = request.data.get('course_uuid', None)
        mode = request.data.get('mode', None)
        username = request.data.get('username', None)
        order_number = request.data.get('order_number', None)

        # Verify the required input
        if (course_uuid is None or
                mode is None or
                username is None or
                order_number is None):

            return Response(data='Insufficient data to create or update entitlement',
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            course_uuid = uuid.UUID(course_uuid)
        except ValueError:
            return Response(
                data='Invalid course UUID provided',
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(data='Invalid Username provided', status=status.HTTP_401_UNAUTHORIZED)

        entitlement_data = {
            'user': user,
            'course_uuid': course_uuid,
            'mode': mode,
            'order_number': order_number
        }

        stored_entitlement, is_created = CourseEntitlement.objects.get_or_create(
            user=user,
            course_uuid=course_uuid,
            order_number=order_number,
            mode=mode,
            defaults=entitlement_data
        )

        if is_created:
            return Response(
                status=status.HTTP_201_CREATED,
                data=_get_response_object([stored_entitlement])
            )
        else:
            return Response(
                status=status.HTTP_200_OK,
                data=_get_response_object([stored_entitlement])
            )


class EntitlementUUIDView(APIView):
    authentication_classes = SESSION_CLASSES
    permission_classes = PERMISSION_CLASSES

    def _get_entitlement_by_uuid(self, entitlement_uuid):
        if entitlement_uuid is None:
            return Response(
                data='Insufficient data to perform request',
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            entitlement = CourseEntitlement.objects.get(uuid=uuid.UUID(entitlement_uuid))
        except CourseEntitlement.DoesNotExist:
            return Response(
                data='Entitlement of uuid {} does not exist'.format(entitlement_uuid),
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError:
            return Response(
                data='Invalid course UUID provided',
                status=status.HTTP_400_BAD_REQUEST
            )
        return entitlement

    def get(self, request, entitlement_uuid):
        entitlement = self._get_entitlement_by_uuid(entitlement_uuid)
        return Response(_get_response_object([entitlement]))

    def delete(self, request, entitlement_uuid):
        """
        Expire and revoke the provided Entitlements UUID and unenroll the User if enrolled
        """
        entitlement = self._get_entitlement_by_uuid(entitlement_uuid)

        if entitlement.expired_at is None:
            entitlement.expired_at = datetime.now()
            entitlement.save()

        # if the entitlement is enrolled we need to unenroll the user
        if entitlement.enrollment_course_run is not None:
            CourseEnrollment.unenroll(
                user=entitlement.user,
                course_id=entitlement.enrollment_course_run.course_id,
                skip_refund=True
            )
            entitlement.enrollment_course_run = None
            entitlement.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, entitlement_uuid):
        """
        Patch the Entitlement with the provided data and return the update Entitlement information

        Expected incoming data for an Entitlement
            {
                "username": <username>,
                "course_uuid": <course_uuid>,
                "mode": <mode>, # e.g. verified, credit, audit
                "order_number": <order_number>
            }
        """
        if entitlement_uuid is None:
            return Response(
                data='Insufficient data to perform request',
                status=status.HTTP_400_BAD_REQUEST
            )
        entitlement_data = _get_updated_entitlement_data_fields(request=request)

        try:
            entitlement_uuid = uuid.UUID(entitlement_uuid)
            CourseEntitlement.objects.filter(uuid=entitlement_uuid).update(**entitlement_data)
            entitlement = CourseEntitlement.objects.get(uuid=entitlement_uuid)
            return Response(
                status=status.HTTP_200_OK,
                data=_get_response_object([entitlement])
            )
        except ValueError:
            return Response(
                data='Invalid course UUID provided',
                status=status.HTTP_400_BAD_REQUEST
            )
