# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from base.models.utils.utils import ChoiceEnum


class StatutActivite(ChoiceEnum):
    NON_SOUMISE = _("NON_SOUMISE")
    SOUMISE = _("SOUMISE")
    ACCEPTEE = _("ACCEPTEE")
    REFUSEE = _("REFUSEE")


class CategorieActivite(ChoiceEnum):
    CONFERENCE = pgettext_lazy("CategorieActivite", "CONFERENCE")
    COMMUNICATION = pgettext_lazy("CategorieActivite", "COMMUNICATION")
    SEMINAR = pgettext_lazy("CategorieActivite", "SEMINAR")
    PUBLICATION = pgettext_lazy("CategorieActivite", "PUBLICATION")
    SERVICE = pgettext_lazy("CategorieActivite", "SERVICE")
    RESIDENCY = pgettext_lazy("CategorieActivite", "RESIDENCY")
    VAE = pgettext_lazy("CategorieActivite", "VAE")
    COURSE = pgettext_lazy("CategorieActivite", "COURSE")
    PAPER = pgettext_lazy("CategorieActivite", "PAPER")
    UCL_COURSE = pgettext_lazy("CategorieActivite", "UCL_COURSE")


class ChoixComiteSelection(ChoiceEnum):
    YES = _("YES")
    NO = _("NO")
    NA = _("N/A")


class ChoixStatutPublication(ChoiceEnum):
    UNSUBMITTED = _("Unsubmitted for publication")
    SUBMITTED = _("Submitted for publication")
    IN_REVIEW = _("In review")
    ACCEPTED = _("Accepted")
    PUBLISHED = _("Published")


class ChoixTypeEpreuve(ChoiceEnum):
    CONFIRMATION_PAPER = _("CONFIRMATION_PAPER")
    PRIVATE_DEFENSE = _("PRIVATE_DEFENSE")
    PUBLIC_DEFENSE = _("PUBLIC_DEFENSE")


class ContexteFormation(ChoiceEnum):
    DOCTORAL_TRAINING = _("DOCTORAL_TRAINING")
    COMPLEMENTARY_TRAINING = _("COMPLEMENTARY_TRAINING")
    FREE_COURSE = _("FREE_COURSE")
