"""
Credit Application Configuration
"""

from django.apps import AppConfig
from django.conf import settings
from edx_proctoring.runtime import set_runtime_service


class CreditConfig(AppConfig):
    """
    Default configuration for the "credit" Django application.
    """
    name = u'credit'

    def ready(self):
        if settings.FEATURES.get('ENABLE_SPECIAL_EXAMS'):
            from .services import CreditService
            set_runtime_service('credit', CreditService())
