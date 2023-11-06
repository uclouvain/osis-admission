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
from typing import Optional, List

import attr

from admission.ddd.admission.domain.model.complement_formation import ComplementFormationIdentity
from admission.ddd.admission.domain.model.condition_complementaire_approbation import (
    ConditionComplementaireApprobationIdentity,
)
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC,
    STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS,
    ChoixStatutChecklist,
    DecisionFacultaireEnum,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import StatutsChecklistGenerale
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    MotifRefusFacultaireNonSpecifieException,
    InformationsAcceptationFacultaireNonSpecifieesException,
    SituationPropositionNonSICException,
    SituationPropositionNonFACException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldSpecifierMotifRefusFacultaire(BusinessValidator):
    motifs_refus: List[MotifRefusIdentity]
    autres_motifs_refus: List[str]

    def validate(self, *args, **kwargs):
        if not self.motifs_refus and not self.autres_motifs_refus:
            raise MotifRefusFacultaireNonSpecifieException


@attr.dataclass(frozen=True, slots=True)
class ShouldSpecifierInformationsAcceptationFacultaire(BusinessValidator):
    avec_conditions_complementaires: Optional[bool]
    conditions_complementaires_existantes: List[ConditionComplementaireApprobationIdentity]
    conditions_complementaires_libres: List[str]

    avec_complements_formation: Optional[bool]
    complements_formation: Optional[List[ComplementFormationIdentity]]

    nombre_annees_prevoir_programme: Optional[int]

    def validate(self, *args, **kwargs):
        if (
            self.avec_conditions_complementaires is None
            or self.avec_conditions_complementaires
            and not (self.conditions_complementaires_libres or self.conditions_complementaires_existantes)
            or self.avec_complements_formation is None
            or self.avec_complements_formation
            and not self.complements_formation
            or not self.nombre_annees_prevoir_programme
        ):
            raise InformationsAcceptationFacultaireNonSpecifieesException


@attr.dataclass(frozen=True, slots=True)
class ShouldSICPeutSoumettreAFacLorsDeLaDecisionFacultaire(BusinessValidator):
    statut: ChoixStatutPropositionGenerale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_SIC:
            raise SituationPropositionNonSICException


@attr.dataclass(frozen=True, slots=True)
class ShouldFacPeutSoumettreAuSicLorsDeLaDecisionFacultaire(BusinessValidator):
    statut: ChoixStatutPropositionGenerale
    checklist_actuelle: StatutsChecklistGenerale

    def validate(self, *args, **kwargs):
        if (
            self.statut.name not in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC
            or self.checklist_actuelle.decision_facultaire.statut
            not in {
                ChoixStatutChecklist.INITIAL_CANDIDAT,
                ChoixStatutChecklist.GEST_EN_COURS,
                ChoixStatutChecklist.GEST_BLOCAGE,
            }
            or self.checklist_actuelle.decision_facultaire.extra.get('decision')
            == DecisionFacultaireEnum.EN_DECISION.value
        ):
            raise SituationPropositionNonFACException


@attr.dataclass(frozen=True, slots=True)
class ShouldFacPeutDonnerDecision(BusinessValidator):
    statut: ChoixStatutPropositionGenerale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC:
            raise SituationPropositionNonFACException


@attr.dataclass(frozen=True, slots=True)
class ShouldPeutSpecifierInformationsDecisionFacultaire(BusinessValidator):
    statut: ChoixStatutPropositionGenerale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_GENERALE_SOUMISE_POUR_FAC_ETENDUS:
            raise SituationPropositionNonFACException
