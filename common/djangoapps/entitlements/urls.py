from django.conf.urls import url, patterns
from .views import EntitlementView, EntitlementUUIDView

urlpatterns = patterns(
    'entitlements.views',
    url(r'^entitlements/$', EntitlementView.as_view(), name='entitlement_api_view'),
    url(
        r'^entitlements/(?P<entitlement_uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})/$',
        EntitlementUUIDView.as_view(),
        name='entitlement_api_uuid'
    )
)
