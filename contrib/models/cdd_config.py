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
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models.enums.entity_type import DOCTORAL_COMMISSION


def default_service_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "Didactic supervision",
            "Teaching activities",
            "Popularisation of science",
            "Writing a research project",
            "Organisation of scientific events",
            "Scientific expertise report (refering)",
            "Supervision of dissertations",
            "International cooperation",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Encadrement didactique",
            "Activités d'enseignement",
            "Vulgarisation scientifique",
            "Rédaction d'un projet de recherche",
            "Organisation de manifestation scientifique",
            "Rapport d’expertise scientifique (refering)",
            "Supervision de mémoire",
            "Coopération internationale",
        ],
    }


def default_seminar_types():
    return {
        settings.LANGUAGE_CODE_EN: [
            "Research seminar",
            "PhD students' day",
        ],
        settings.LANGUAGE_CODE_FR: [
            "Séminaire de recherche",
            "Journée des doctorantes et des doctorants",
        ],
    }


class CddConfiguration(models.Model):
    cdd = models.OneToOneField(
        'base.Entity',
        on_delete=models.CASCADE,
        limit_choices_to={'entityversion__entity_type': DOCTORAL_COMMISSION},
        related_name='admission_config',
    )
    service_types = models.JSONField(
        verbose_name=_("Service types"),
        default=default_service_types,
    )
    seminar_types = models.JSONField(
        verbose_name=_("Seminar types"),
        default=default_seminar_types,
    )
