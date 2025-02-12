# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional

import attr

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_CDD_POUR_DECISION,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD_ETENDUS,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC,
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    BesoinDeDerogation,
    ChoixStatutChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    StatutChecklist,
    StatutsChecklistDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    ComplementsFormationEtreVidesSiPasDeComplementsFormationException,
    ConditionAccesEtreSelectionneException,
    DemandeDoitEtreAdmissionException,
    DemandeDoitEtreInscriptionException,
    DocumentAReclamerImmediatException,
    EtatChecklistDecisionSicNonValidePourApprouverUneInscription,
    EtatChecklistFinancabiliteNonValidePourApprouverDemande,
    InscriptionTardiveAvecConditionAccesException,
    ParcoursAnterieurNonSuffisantException,
    SituationPropositionNonCddException,
    SituationPropositionNonSICException,
    TitreAccesEtreSelectionneException,
    TitreAccesEtreSelectionnePourEnvoyerASICException,
)
from admission.ddd.admission.domain.model.complement_formation import (
    ComplementFormationIdentity,
)
from admission.ddd.admission.domain.model.titre_acces_selectionnable import (
    TitreAccesSelectionnable,
)
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import (
    STATUTS_EMPLACEMENT_DOCUMENT_A_RECLAMER,
    StatutReclamationEmplacementDocument,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from base.ddd.utils.business_validator import BusinessValidator
from epc.models.enums.condition_acces import ConditionAcces


@attr.dataclass(frozen=True, slots=True)
class ShouldSICPeutSoumettreACddLorsDeLaDecisionCdd(BusinessValidator):
    statut: ChoixStatutPropositionDoctorale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_CDD_POUR_DECISION:
            raise SituationPropositionNonSICException


@attr.dataclass(frozen=True, slots=True)
class ShouldGestionnairePeutSoumettreAuSicLorsDeLaDecisionCdd(BusinessValidator):
    statut: ChoixStatutPropositionDoctorale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD:
            raise SituationPropositionNonCddException


@attr.dataclass(frozen=True, slots=True)
class ShouldCddPeutDonnerDecision(BusinessValidator):
    statut: ChoixStatutPropositionDoctorale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD:
            raise SituationPropositionNonCddException


@attr.dataclass(frozen=True, slots=True)
class ShouldPropositionEtreInscriptionTardiveAvecConditionAcces(BusinessValidator):
    condition_acces: Optional[ConditionAcces]
    est_inscription_tardive: bool

    def validate(self, *args, **kwargs):
        if not self.est_inscription_tardive or not self.condition_acces:
            raise InscriptionTardiveAvecConditionAccesException


@attr.dataclass(frozen=True, slots=True)
class ShouldSelectionnerTitreAccesPourEnvoyerASIC(BusinessValidator):
    titres_selectionnes: List[TitreAccesSelectionnable]

    def validate(self, *args, **kwargs):
        if not self.titres_selectionnes:
            raise TitreAccesEtreSelectionnePourEnvoyerASICException


@attr.dataclass(frozen=True, slots=True)
class ShouldSicPeutDonnerDecision(BusinessValidator):
    statut: ChoixStatutPropositionDoctorale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC:
            raise SituationPropositionNonSICException


@attr.dataclass(frozen=True, slots=True)
class ShouldChecklistEtreDansEtatCorrectPourApprouverInscription(BusinessValidator):
    checklist_actuelle: StatutsChecklistDoctorale
    besoin_de_derogation: BesoinDeDerogation

    def validate(self, *args, **kwargs):
        if not (
            self.checklist_actuelle.decision_sic.statut == ChoixStatutChecklist.INITIAL_CANDIDAT
            or self.checklist_actuelle.decision_sic.statut == ChoixStatutChecklist.GEST_EN_COURS
            and self.checklist_actuelle.decision_sic.extra.get('en_cours') == 'derogation'
            and self.besoin_de_derogation == BesoinDeDerogation.ACCORD_DIRECTION
        ):
            raise EtatChecklistDecisionSicNonValidePourApprouverUneInscription


@attr.dataclass(frozen=True, slots=True)
class ShouldDemandeEtreTypeAdmission(BusinessValidator):
    type_demande: TypeDemande

    def validate(self, *args, **kwargs):
        if self.type_demande != TypeDemande.ADMISSION:
            raise DemandeDoitEtreAdmissionException


@attr.dataclass(frozen=True, slots=True)
class ShouldDemandeEtreTypeInscription(BusinessValidator):
    type_demande: TypeDemande

    def validate(self, *args, **kwargs):
        if self.type_demande != TypeDemande.INSCRIPTION:
            raise DemandeDoitEtreInscriptionException


@attr.dataclass(frozen=True, slots=True)
class ShouldPeutSpecifierInformationsDecisionCdd(BusinessValidator):
    statut: ChoixStatutPropositionDoctorale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_CDD_ETENDUS:
            raise SituationPropositionNonCddException


@attr.dataclass(frozen=True, slots=True)
class ShouldTitreAccesEtreSelectionne(BusinessValidator):
    statut: ChoixStatutChecklist
    titres_acces_selectionnes: List[TitreAccesSelectionnable]

    def validate(self, *args, **kwargs):
        if self.statut == ChoixStatutChecklist.GEST_REUSSITE and not self.titres_acces_selectionnes:
            raise TitreAccesEtreSelectionneException


@attr.dataclass(frozen=True, slots=True)
class ShouldConditionAccesEtreSelectionne(BusinessValidator):
    statut: ChoixStatutChecklist
    condition_acces: Optional[ConditionAcces]
    millesime_condition_acces: Optional[int]

    def validate(self, *args, **kwargs):
        if self.statut == ChoixStatutChecklist.GEST_REUSSITE and not (
            self.condition_acces and self.millesime_condition_acces
        ):
            raise ConditionAccesEtreSelectionneException


@attr.dataclass(frozen=True, slots=True)
class ShouldParcoursAnterieurEtreSuffisant(BusinessValidator):
    statut: StatutChecklist

    def validate(self, *args, **kwargs):
        if self.statut.statut != ChoixStatutChecklist.GEST_REUSSITE:
            raise ParcoursAnterieurNonSuffisantException


@attr.dataclass(frozen=True, slots=True)
class ShouldComplementsFormationEtreVidesSiPasDeComplementsFormation(BusinessValidator):
    avec_complements_formation: Optional[bool]

    complements_formation: Optional[List[ComplementFormationIdentity]]
    commentaire_complements_formation: str

    def validate(self, *args, **kwargs):
        if not self.avec_complements_formation and (
            self.complements_formation or self.commentaire_complements_formation
        ):
            raise ComplementsFormationEtreVidesSiPasDeComplementsFormationException


@attr.dataclass(frozen=True, slots=True)
class ShouldNePasAvoirDeDocumentReclameImmediat(BusinessValidator):
    documents_dto: List[EmplacementDocumentDTO]

    def validate(self, *args, **kwargs):
        if any(
            document.statut in STATUTS_EMPLACEMENT_DOCUMENT_A_RECLAMER
            and document.statut_reclamation == StatutReclamationEmplacementDocument.IMMEDIATEMENT.name
            for document in self.documents_dto
        ):
            raise DocumentAReclamerImmediatException


@attr.dataclass(frozen=True, slots=True)
class ShouldFinancabiliteEtreDansEtatCorrectPourApprouverDemande(BusinessValidator):
    checklist_actuelle: StatutsChecklistDoctorale

    def validate(self, *args, **kwargs):
        if (
            self.checklist_actuelle.financabilite.statut != ChoixStatutChecklist.INITIAL_NON_CONCERNE
            and self.checklist_actuelle.financabilite.statut != ChoixStatutChecklist.GEST_REUSSITE
        ):
            raise EtatChecklistFinancabiliteNonValidePourApprouverDemande
