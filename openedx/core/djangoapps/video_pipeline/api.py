"""
API utils in order to communicate to edx-video-pipeline.
"""
import logging

from django.core.exceptions import ObjectDoesNotExist
from slumber.exceptions import HttpClientError

from openedx.core.djangoapps.video_pipeline.models import VideoPipelineIntegration
from openedx.core.djangoapps.video_pipeline.utils import create_video_pipeline_api_client

log = logging.getLogger(__name__)


def update_3rd_party_transcription_service_credentials(**credentials_payload):
    """
    Updates the 3rd Party Transcription Service's Credentials.

    Arguments:
        credentials_payload(dict): A payload containing org, provider and its credentials.

    Returns:
        A Boolean specifying whether the credentials update was a success or not.
    """
    is_updated = False
    pipeline_integration = VideoPipelineIntegration.current()
    if pipeline_integration.enabled:
        try:
            video_pipeline_user = pipeline_integration.get_service_user()
        except ObjectDoesNotExist:
            return False

        client = create_video_pipeline_api_client(user=video_pipeline_user, api_url=pipeline_integration.api_url)

        try:
            client.transcript_credentials.post(credentials_payload)
            is_updated = True
        except HttpClientError as ex:
            is_updated = False
            log.exception(
                '[video-pipeline-service] unable to update transcript credentials -- response -- %s',
                ex.content,
            )

    return is_updated
