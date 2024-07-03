# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db import models
from django.utils.translation import gettext_lazy as _, pgettext

__all__ = [
    'DiplomaticPost',
]


class DiplomaticPostQuerySet(models.QuerySet):
    def annotate_countries(self):
        return self.annotate(
            countries_iso_codes=ArrayAgg('countries__iso_code'),
        )


class DiplomaticPostManager(models.Manager.from_queryset(DiplomaticPostQuerySet)):
    pass


class DiplomaticPost(models.Model):
    code = models.PositiveSmallIntegerField(
        primary_key=True,
        verbose_name=_('Diplomatic post code'),
        # db_comment="PosteDiplomatiqueDTO.code",
    )
    name_fr = models.CharField(
        max_length=255,
        verbose_name=_('Name in french'),
        # db_comment="PosteDiplomatiqueDTO.nom_francais",
    )
    name_en = models.CharField(
        max_length=255,
        verbose_name=_('Name in english'),
        # db_comment="PosteDiplomatiqueDTO.nom_anglais",
    )
    email = models.EmailField(
        max_length=255,
        verbose_name=pgettext('admission', 'Email'),
        # db_comment="PosteDiplomatiqueDTO.adresse_email",
    )
    countries = models.ManyToManyField(
        to='reference.Country',
        verbose_name=_('Countries'),
        related_name='+',
        # db_comment="Renvoyé en réponse de l'API.",
    )

    objects = DiplomaticPostManager()

    class Meta:
        pass
        # db_table_comment = "Représente un poste diplomatique."

    def __str__(self):
        return {
            settings.LANGUAGE_CODE_FR: self.name_fr,
            settings.LANGUAGE_CODE_EN: self.name_en,
        }[settings.LANGUAGE_CODE]
