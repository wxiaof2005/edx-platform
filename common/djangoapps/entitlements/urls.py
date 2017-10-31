from django.conf.urls import url, patterns, include
from .views import EntitlementUUIDView, EntitlementViewSet

from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'entitlements', EntitlementViewSet, base_name='entitlements_list')
# router.register(r'users', views.UserViewSet)


urlpatterns = patterns(
    'entitlements.views',
    url(r'^', include(router.urls, namespace='api')),
    # url(r'^entitlements/$', EntitlementUUIDView.as_view(), name='entitlement_api_view'),
    url(
        r'^entitlements/(?P<entitlement_uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})/$',
        EntitlementUUIDView.as_view(),
        name='entitlement_api_uuid'
    )
)
