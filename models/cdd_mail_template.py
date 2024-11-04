# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict, List

from django.conf import settings
from django.db import models
from django.db.models import Subquery
from django.utils.translation import gettext_lazy as _

from admission.mail_templates import (
    ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
)
from base.models.enums.organization_type import MAIN
from osis_mail_template.models import MailTemplateManager, check_mail_template_identifier
from osis_mail_template.utils import MissingTokenDict, transform_html_to_text


ALLOWED_CUSTOM_IDENTIFIERS = [
    ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_FAILURE_STUDENT,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_ON_RETAKING_STUDENT,
]


class CddMailTemplateManager(MailTemplateManager):
    def get_by_id_and_pk(self, identifier: str, pk: int):
        """Get a list of mail template instances by identifier and one pk"""
        return list(
            self.get_queryset()
            .filter(
                identifier=identifier,
                name=Subquery(CddMailTemplate.objects.filter(pk=pk).values('name')[:1]),
            )
            .order_by('language')
        )

    def get_from_identifiers(self, identifiers: List[str], language: str, cdd_id: int):
        """Get a list of mail template instances by identifier and language"""
        qs = self.get_queryset().filter(
            identifier__in=identifiers,
            language=language,
            cdd_id=cdd_id,
        )

        return list(qs)

    def delete_by_id_and_pk(self, identifier: str, pk: int):
        """Delete mail template instances associated with an identifier and a pk"""
        return (
            self.get_queryset()
            .filter(
                identifier=identifier,
                name=Subquery(CddMailTemplate.objects.filter(pk=pk).values('name')[:1]),
            )
            .delete()
        )


class CddMailTemplate(models.Model):
    identifier = models.CharField(
        max_length=255,
        verbose_name=_("Identifier"),
        validators=[check_mail_template_identifier],
        choices=zip(ALLOWED_CUSTOM_IDENTIFIERS, ALLOWED_CUSTOM_IDENTIFIERS),
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
    )
    language = models.CharField(
        max_length=25,
        verbose_name=_("Language"),
        choices=(lang for lang in settings.LANGUAGES),
    )
    cdd = models.ForeignKey(
        'base.Entity',
        on_delete=models.CASCADE,
        limit_choices_to={
            'organization__type': MAIN,
        },
        related_name='+',
    )

    subject = models.CharField(
        max_length=255,
        verbose_name=_("Subject"),
    )
    body = models.TextField(
        verbose_name=_("Body"),
    )

    objects = CddMailTemplateManager()

    class Meta:
        verbose_name = _("CDD Mail template")
        verbose_name_plural = _("CDD Mail templates")
        unique_together = [
            ['identifier', 'language', 'cdd', 'name'],
        ]

    def __str__(self):
        from osis_mail_template import templates

        return '{} (depuis {} en {})'.format(
            self.name,
            templates.get_description(self.identifier),
            self.get_language_display(),
        )

    def _replace_tokens(self, field: str, tokens: Dict[str, str] = None) -> str:
        if tokens is None:
            from osis_mail_template import templates

            tokens = templates.get_example_values(self.identifier)
        return getattr(self, field).format_map(MissingTokenDict(**tokens))

    def render_subject(self, tokens: Dict[str, str] = None) -> str:
        """Renders the subject with the given tokens, or example values"""
        return self._replace_tokens('subject', tokens)

    def body_as_html(self, tokens: Dict[str, str] = None) -> str:
        """Renders the body as HTML with the given tokens, or example values"""
        return self._replace_tokens('body', tokens)

    def body_as_plain(self, tokens: Dict[str, str] = None) -> str:
        """Renders the body as plain text with the given tokens, or example values"""
        formatted_body = self.body_as_html(tokens)
        return transform_html_to_text(formatted_body)
