from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.models import SiteTheme

SITES = {
    "mitxpro": {
        "theme_dir_name": "mitxpro.mit.edu",
        "configuration": {}
    },
    "hms": {
        "theme_dir_name": "globalacademy.hms.harvard.edu",
        "configuration": {}
    },
    "wharton": {
        "theme_dir_name": "	professionaleducation.wharton.upenn.edu",
        "configuration": {}
    },
    "harvardx": {
        "theme_dir_name": "	harvardxplus.harvard.edu",
        "configuration": {}
    }
}

class Command(BaseCommand):
    """
    Command to create the site, site themes and configuration for all WL-sites.

    Example:
    ./manage.py lms create_sites_and_configurations --dns-name whitelabel
    """

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """

        parser.add_argument(
            '--dns-name',
            type=str,
            dest='dns_name',
            help='DNS name of sandbox.',
        )

    def handle(self, *args, **options):

        dns_name = options['dns_name']

        for site_alias, site_data in SITES.items():

            site = Site.objects.create(
                domain="{domain}-{dns_name}.sandbox.edx.org".format(domain=site_alias, dns_name=dns_name),
                name=site_alias
            )

            SiteTheme.objects.create(site=site, theme_dir_name=site_data['theme_dir_name'])

            SiteConfiguration.objects.create(
                site=site,
                values=site_data['configuration'],
                enabled=True,
            )
