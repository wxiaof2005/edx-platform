import json
import unittest
import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from entitlements.models import CourseEntitlement
from openedx.core.lib.token_utils import JwtBuilder
from student.tests.factories import CourseEnrollmentFactory, UserFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EntitlementsTest(ModuleStoreTestCase):
    """
    Entitlements API/View Tests
    """
    USERNAME = 'Bob'
    ENABLED_CACHES = ['default']
    COURSE_RUN_ID = 'some/great/course'

    def setUp(self):
        super(EntitlementsTest, self).setUp()
        self.user = UserFactory(is_staff=True)
        self.course = CourseFactory.create(org='TestX', course='TS101', run='T1')
        self.entitlements_url = reverse('entitlements_api:entitlement_api_view')
        self.entitlements_uuid_path = 'entitlements_api:entitlement_api_uuid'
        self.course_uuid = str(uuid.uuid4())

    def tearDown(self):
        self.client.logout()

    def _setup_header(self, user):
        """
        Get a header containing the Authentication Token
        """
        scopes = ['email', 'profile']
        expires_in = settings.OAUTH_ID_TOKEN_EXPIRATION
        token = JwtBuilder(user).build_token(scopes, expires_in)
        return {
            'HTTP_AUTHORIZATION': 'JWT ' + token
        }

    def _get_data_set(self, user):
        """
        Get a basic data set for an entitlement
        """
        return {
            "username": user.username,
            "mode": "verified",
            "course_uuid": self.course_uuid,
            "order_number": "EDX-1001"
        }

    def _add_entitlement(self, user, order_number):
        """
        Add an entitlement to the database
        """
        entitlement = CourseEntitlement()
        entitlement.course_uuid = uuid.uuid4()
        entitlement.mode = 'verified'
        entitlement.user = user
        entitlement.order_number = order_number
        entitlement.save()
        return entitlement

    def test_auth_required(self):
        headers = {}
        response = self.client.get(self.entitlements_url, **headers)
        self.assertEqual(response.status_code, 401)

    def test_staff_user_required(self):
        headers = {}
        not_staff_user = UserFactory()
        self.client.login(username=not_staff_user.username, password=UserFactory._DEFAULT_PASSWORD)
        response = self.client.get(self.entitlements_url, **headers)
        self.assertEqual(response.status_code, 403)

    def test_add_entitlement_with_missing_data(self):
        headers = self._setup_header(self.user)

        entitlement_data_missing_parts = self._get_data_set(self.user)
        entitlement_data_missing_parts.pop('mode')

        response = self.client.post(
            self.entitlements_url,
            data=json.dumps(entitlement_data_missing_parts),
            content_type='application/json',
            **headers
        )
        self.assertEqual(response.status_code, 400)

    def test_add_entitlement(self):
        headers = self._setup_header(self.user)
        entitlement_data = self._get_data_set(self.user)

        response = self.client.post(
            self.entitlements_url,
            data=json.dumps(entitlement_data),
            content_type='application/json',
            **headers
        )
        self.assertEqual(response.status_code, 201)
        results = response.data.get('results', [])
        self.assertGreater(len(results), 0)

        course_entitlement = CourseEntitlement.objects.get(
            user=self.user,
            course_uuid=self.course_uuid
        )

        self.assertIsNotNone(course_entitlement)
        self.assertEqual(results[0]['uuid'], str(course_entitlement.uuid))
        self.assertEqual(str(course_entitlement.course_uuid), self.course_uuid)
        self.assertEqual(course_entitlement.enrollment_course_run, None)
        self.assertEqual(course_entitlement.mode, 'verified')
        self.assertIsNotNone(course_entitlement.created)
        self.assertTrue(course_entitlement.user, self.user)

    def test_get_entitlements(self):
        self._add_entitlement(self.user, 'TESTX-1001')
        self._add_entitlement(self.user, 'TESTX-1002')
        headers = self._setup_header(self.user)

        response = self.client.get(
            self.entitlements_url,
            content_type='application/json',
            **headers
        )
        self.assertEqual(response.status_code, 200)

        results = response.data.get('results', [])
        self.assertEqual(len(results), 2)

    def test_get_entitlement_by_uuid(self):
        uuid1 = self._add_entitlement(self.user, 'TESTX-1001').uuid
        self._add_entitlement(self.user, 'TESTX-1002')
        url = reverse('entitlements_api:entitlement_api_uuid', args=[str(uuid1)])
        headers = self._setup_header(self.user)

        response = self.client.get(
            url,
            content_type='application/json',
            **headers
        )
        self.assertEqual(response.status_code, 200)

        results = response.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['uuid'], str(uuid1))

    def test_delete_and_revoke_entitlement(self):
        uuid1 = self._add_entitlement(self.user, 'TESTX-1001').uuid
        url = reverse('entitlements_api:entitlement_api_uuid', args=[str(uuid1)])
        headers = self._setup_header(self.user)

        response = self.client.delete(
            url,
            content_type='application/json',
            **headers
        )
        self.assertEqual(response.status_code, 204)

        course_entitlement = CourseEntitlement.objects.get(
            uuid=uuid1
        )

        self.assertIsNotNone(course_entitlement.expired_at)

    def test_revoke_unenroll_entitlement(self):
        uuid1 = self._add_entitlement(self.user, 'TESTX-1001').uuid
        url = reverse('entitlements_api:entitlement_api_uuid', args=[str(uuid1)])
        enrollment = CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

        course_entitlement = CourseEntitlement.objects.get(
            uuid=uuid1
        )

        course_entitlement.enrollment_course_run = enrollment
        course_entitlement.save()

        self.assertIsNotNone(course_entitlement.enrollment_course_run)

        headers = self._setup_header(self.user)
        response = self.client.delete(
            url,
            content_type='application/json',
            **headers
        )
        self.assertEqual(response.status_code, 204)

        course_entitlement = CourseEntitlement.objects.get(
            uuid=uuid1
        )

        self.assertIsNotNone(course_entitlement.expired_at)
        self.assertIsNone(course_entitlement.enrollment_course_run)
