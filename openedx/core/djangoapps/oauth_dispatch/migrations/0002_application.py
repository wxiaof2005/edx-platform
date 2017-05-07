# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import oauth2_provider.generators
import oauth2_provider.validators
from django.conf import settings
from django.db import migrations, models


def clone_applications(apps, schema_editor):
    Application = apps.get_model('oauth_dispatch', 'Application')
    OldApplication = apps.get_model('oauth2_provider', 'Application')

    for old_application in OldApplication.objects.all():
        kwargs = {field.name: getattr(old_application, field.name) for field in Application._meta.fields}
        del kwargs['id']
        Application.objects.create(**kwargs)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('oauth_dispatch', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('client_id',
                 models.CharField(default=oauth2_provider.generators.generate_client_id, unique=True, max_length=100,
                                  db_index=True)),
                ('redirect_uris', models.TextField(help_text='Allowed URIs list, space separated', blank=True,
                                                   validators=[oauth2_provider.validators.validate_uris])),
                ('client_type',
                 models.CharField(max_length=32, choices=[('confidential', 'Confidential'), ('public', 'Public')])),
                ('authorization_grant_type', models.CharField(max_length=32,
                                                              choices=[('authorization-code', 'Authorization code'),
                                                                       ('implicit', 'Implicit'),
                                                                       ('password', 'Resource owner password-based'),
                                                                       ('client-credentials', 'Client credentials')])),
                ('client_secret',
                 models.CharField(default=oauth2_provider.generators.generate_client_secret, max_length=255,
                                  db_index=True, blank=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('skip_authorization', models.BooleanField(default=False)),
                ('restricted', models.BooleanField(default=False,
                                                   help_text='Restricted clients receive expired access tokens. They are intended to provide identity information to third-parties.')),
                ('user',
                 models.ForeignKey(related_name='oauth_dispatch_application', blank=True, to=settings.AUTH_USER_MODEL,
                                   null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RunPython(clone_applications, migrations.RunPython.noop),
    ]
