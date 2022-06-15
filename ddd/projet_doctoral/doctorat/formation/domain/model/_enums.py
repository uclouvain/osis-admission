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
from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class StatutActivite(ChoiceEnum):
    NON_SOUMISE = _("NON_SOUMISE")
    SOUMISE = _("SOUMISE")
    ACCEPTEE = _("ACCEPTEE")
    REFUSEE = _("REFUSEE")


class CategorieActivite(ChoiceEnum):
    CONFERENCE = _("CONFERENCE")
    COMMUNICATION = _("COMMUNICATION")
    SEMINAR = _("SEMINAR")
    PUBLICATION = _("PUBLICATION")
    SERVICE = _("SERVICE")
    RESIDENCY = _("RESIDENCY")
    VAE = _("VAE")
    # COURS = _("COURS")  # TODO


class ChoixComiteSelection(ChoiceEnum):
    YES = _("YES")
    NO = _("NO")
    NA = _("N/A")


class ChoixStatutPublication(ChoiceEnum):
    UNSUBMITTED = _("Unsubmitted")
    SUBMITTED = _("Submitted")
    IN_REVIEW = _("In review")
    ACCEPTED = _("Accepted")
    PUBLISHED = _("Published")
