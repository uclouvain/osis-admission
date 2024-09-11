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

import attr

from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_continue.domain.model.statut_checklist import StatutChecklist
from admission.ddd.admission.formation_continue.domain.validator.exceptions import (
    ApprouverPropositionTransitionStatutException,
    AnnulerPropositionTransitionStatutException,
    RefuserPropositionTransitionStatutException,
    ApprouverParFacTransitionStatutException,
    MettreEnAttenteTransitionStatutException,
    MettreAValiderTransitionStatutException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldPeutMettreEnAttente(BusinessValidator):
    checklist_statut: StatutChecklist

    def validate(self, *args, **kwargs):
        if (
            self.checklist_statut.statut == ChoixStatutChecklist.GEST_BLOCAGE
            and self.checklist_statut.extra.get('blocage') == 'closed'
        ):
            raise MettreEnAttenteTransitionStatutException


@attr.dataclass(frozen=True, slots=True)
class ShouldPeutApprouverParFac(BusinessValidator):
    checklist_statut: StatutChecklist

    def validate(self, *args, **kwargs):
        if (
            self.checklist_statut.statut == ChoixStatutChecklist.GEST_BLOCAGE
            and self.checklist_statut.extra.get('blocage') == 'closed'
        ) or self.checklist_statut.statut == ChoixStatutChecklist.GEST_REUSSITE:
            raise ApprouverParFacTransitionStatutException


@attr.dataclass(frozen=True, slots=True)
class ShouldPeutRefuserProposition(BusinessValidator):
    checklist_statut: StatutChecklist

    def validate(self, *args, **kwargs):
        if (
            self.checklist_statut.statut == ChoixStatutChecklist.GEST_BLOCAGE
            and self.checklist_statut.extra.get('blocage') == 'closed'
        ) or self.checklist_statut.statut == ChoixStatutChecklist.GEST_REUSSITE:
            raise RefuserPropositionTransitionStatutException


@attr.dataclass(frozen=True, slots=True)
class ShouldPeutAnnulerProposition(BusinessValidator):
    checklist_statut: StatutChecklist

    def validate(self, *args, **kwargs):
        if (
            self.checklist_statut.statut == ChoixStatutChecklist.GEST_BLOCAGE
            and self.checklist_statut.extra.get('blocage') == 'closed'
        ):
            raise AnnulerPropositionTransitionStatutException


@attr.dataclass(frozen=True, slots=True)
class ShouldPeutApprouverProposition(BusinessValidator):
    checklist_statut: StatutChecklist

    def validate(self, *args, **kwargs):
        if self.checklist_statut.statut != ChoixStatutChecklist.GEST_EN_COURS or self.checklist_statut.extra.get(
            'en_cours'
        ) not in {'fac_approval', 'to_validate'}:
            raise ApprouverPropositionTransitionStatutException


@attr.dataclass(frozen=True, slots=True)
class ShouldPeutMettreAValider(BusinessValidator):
    checklist_statut: StatutChecklist

    def validate(self, *args, **kwargs):
        if (
            self.checklist_statut.statut != ChoixStatutChecklist.GEST_EN_COURS
            or self.checklist_statut.extra.get('en_cours') != 'fac_approval'
        ):
            raise MettreAValiderTransitionStatutException


@attr.dataclass(frozen=True, slots=True)
class ShouldPeutCloturerProposition(BusinessValidator):
    checklist_statut: StatutChecklist

    def validate(self, *args, **kwargs):
        pass
