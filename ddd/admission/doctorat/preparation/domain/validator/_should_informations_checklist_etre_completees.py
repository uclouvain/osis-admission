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
from typing import Optional, List

import attr

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_FAC_POUR_DECISION,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_SIC,
    STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC_ETENDUS,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
    DecisionFacultaireEnum,
    BesoinDeDerogation,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    StatutsChecklistDoctorale,
    StatutChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    TitreAccesEtreSelectionneException,
    ConditionAccesEtreSelectionneException,
    MotifRefusFacultaireNonSpecifieException,
    InformationsAcceptationFacultaireNonSpecifieesException,
    SituationPropositionNonSICException,
    SituationPropositionNonFACException,
    InscriptionTardiveAvecConditionAccesException,
    TitreAccesEtreSelectionnePourEnvoyerASICException,
    EtatChecklistDecisionSicNonValidePourApprouverUneInscription,
    DemandeDoitEtreAdmissionException,
    DemandeDoitEtreInscriptionException,
    ParcoursAnterieurNonSuffisantException,
    ComplementsFormationEtreVidesSiPasDeComplementsFormationException,
    DocumentAReclamerImmediatException,
    EtatChecklistFinancabiliteNonValidePourApprouverDemande,
)
from admission.ddd.admission.domain.model.complement_formation import ComplementFormationIdentity
from admission.ddd.admission.domain.model.condition_complementaire_approbation import (
    ConditionComplementaireApprobationIdentity,
    ConditionComplementaireLibreApprobation,
)
from admission.ddd.admission.domain.model.motif_refus import MotifRefusIdentity
from admission.ddd.admission.domain.model.titre_acces_selectionnable import (
    TitreAccesSelectionnable,
)
from admission.ddd.admission.dtos.emplacement_document import EmplacementDocumentDTO
from admission.ddd.admission.enums.emplacement_document import (
    StatutReclamationEmplacementDocument,
    STATUTS_EMPLACEMENT_DOCUMENT_A_RECLAMER,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from base.ddd.utils.business_validator import BusinessValidator
from epc.models.enums.condition_acces import ConditionAcces


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
    conditions_complementaires_libres: List[ConditionComplementaireLibreApprobation]

    avec_complements_formation: Optional[bool]
    complements_formation: Optional[List[ComplementFormationIdentity]]

    nombre_annees_prevoir_programme: Optional[int]

    def validate(self, *args, **kwargs):
        if (
            self.avec_conditions_complementaires is None
            or self.avec_conditions_complementaires
            and not (self.conditions_complementaires_libres or self.conditions_complementaires_existantes)
            or not self.nombre_annees_prevoir_programme
        ):
            raise InformationsAcceptationFacultaireNonSpecifieesException


@attr.dataclass(frozen=True, slots=True)
class ShouldSpecifierInformationsAcceptationFacultaireInscription(BusinessValidator):
    avec_conditions_complementaires: Optional[bool]
    conditions_complementaires_existantes: List[ConditionComplementaireApprobationIdentity]
    conditions_complementaires_libres: List[ConditionComplementaireLibreApprobation]

    def validate(self, *args, **kwargs):
        if self.avec_conditions_complementaires and not (
            self.conditions_complementaires_libres or self.conditions_complementaires_existantes
        ):
            raise InformationsAcceptationFacultaireNonSpecifieesException


@attr.dataclass(frozen=True, slots=True)
class ShouldSICPeutSoumettreAFacLorsDeLaDecisionFacultaire(BusinessValidator):
    statut: ChoixStatutPropositionDoctorale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_DOCTORALE_ENVOYABLE_EN_FAC_POUR_DECISION:
            raise SituationPropositionNonSICException


@attr.dataclass(frozen=True, slots=True)
class ShouldFacPeutSoumettreAuSicLorsDeLaDecisionFacultaire(BusinessValidator):
    statut: ChoixStatutPropositionDoctorale
    checklist_actuelle: StatutsChecklistDoctorale

    def validate(self, *args, **kwargs):
        if (
            self.statut.name not in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC
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
class ShouldSicPeutSoumettreAuSicLorsDeLaDecisionFacultaire(BusinessValidator):
    statut: ChoixStatutPropositionDoctorale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC:
            raise SituationPropositionNonFACException


@attr.dataclass(frozen=True, slots=True)
class ShouldFacPeutDonnerDecision(BusinessValidator):
    statut: ChoixStatutPropositionDoctorale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC:
            raise SituationPropositionNonFACException


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
class ShouldPeutSpecifierInformationsDecisionFacultaire(BusinessValidator):
    statut: ChoixStatutPropositionDoctorale

    def validate(self, *args, **kwargs):
        if self.statut.name not in STATUTS_PROPOSITION_DOCTORALE_SOUMISE_POUR_FAC_ETENDUS:
            raise SituationPropositionNonFACException


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