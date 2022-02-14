# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.apps import apps
from django.core.checks import Warning, register
from django.db.models import CharField


@register()
def check_charfield_not_nullable(app_configs, **kwargs):
    """A CharField should not be nullable https://docs.djangoproject.com/en/stable/ref/models/fields/#null"""
    errors = []
    apps_to_check = [
        'admission',
        'osis_profile',
    ]
    app_configs = app_configs or apps.get_app_configs()
    charfields = [
        field
        for app_config in app_configs
        if app_config.name in apps_to_check
        for model in app_config.get_models()
        if not model._meta.proxy
        for field in model._meta.fields
        if isinstance(field, CharField)
    ]
    for field in charfields:
        if field.null:
            errors.append(
                Warning(
                    "'{}' CharField should not be nullable".format(field.name),
                    hint='Remove `null=True` and ensure `default=""`.',
                    obj=field.model,
                    id='admission.E001',
                )
            )
    return errors
