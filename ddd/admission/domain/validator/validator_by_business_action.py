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

import datetime
from typing import List, Optional, Dict

import attr

from admission.ddd.admission.domain.model._candidat_adresse import CandidatAdresse
from admission.ddd.admission.domain.model._candidat_signaletique import CandidatSignaletique
from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocument
from admission.ddd.admission.domain.validator import *
from admission.ddd.admission.domain.validator._should_ne_pas_etre_en_quarantaine import ShouldNePasEtreEnQuarantaine
from admission.ddd.admission.dtos.merge_proposal import MergeProposalDTO
from base.ddd.utils.business_validator import BusinessValidator, TwoStepsMultipleBusinessExceptionListValidator


@attr.dataclass(frozen=True, slots=True)
class IdentificationValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    identite_signaletique: 'CandidatSignaletique'

    date_naissance: Optional[datetime.date]
    annee_naissance: Optional[int]

    pays_residence: Optional[str]

    numero_registre_national_belge: Optional[str]
    numero_carte_identite: Optional[str]
    carte_identite: List[str]
    date_expiration_carte_identite: Optional[datetime.date]
    numero_passeport: Optional[str]
    passeport: List[str]
    date_expiration_passeport: Optional[datetime.date]

    noma_derniere_inscription_ucl: Optional[str]
    annee_derniere_inscription_ucl: Optional[int]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldSignaletiqueCandidatEtreCompletee(
                signaletique=self.identite_signaletique,
            ),
            ShouldCandidatSpecifierNomOuPrenom(
                nom=self.identite_signaletique.nom,
                prenom=self.identite_signaletique.prenom,
            ),
            ShouldCandidatSpecifierNumeroIdentite(
                numero_registre_national_belge=self.numero_registre_national_belge,
                numero_carte_identite=self.numero_carte_identite,
                numero_passeport=self.numero_passeport,
            ),
            ShouldCandidatBelgeSpecifierNumeroRegistreNationalBelge(
                numero_registre_national_belge=self.numero_registre_national_belge,
                pays_nationalite=self.identite_signaletique.pays_nationalite,
                pays_residence=self.pays_residence,
            ),
            ShouldCandidatSpecifierDateOuAnneeNaissance(
                date_naissance=self.date_naissance,
                annee_naissance=self.annee_naissance,
            ),
            ShouldCandidatAuthentiquerPasseport(
                numero_passeport=self.numero_passeport,
                passeport=self.passeport,
                date_expiration_passeport=self.date_expiration_passeport,
            ),
            ShouldCandidatAuthentiquerIdentite(
                numero_registre_national_belge=self.numero_registre_national_belge,
                numero_carte_identite=self.numero_carte_identite,
                carte_identite=self.carte_identite,
                date_expiration_carte_identite=self.date_expiration_carte_identite,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class CoordonneesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    adresse_email_privee: str
    numero_telephone_mobile: str
    domicile_legal: Optional['CandidatAdresse']
    adresse_correspondance: Optional['CandidatAdresse']

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCoordonneesCandidatEtreCompletees(
                numero_telephone_mobile=self.numero_telephone_mobile,
            ),
            ShouldAdresseDomicileLegalCandidatEtreCompletee(adresse=self.domicile_legal),
            ShouldAdresseCorrespondanceEtreCompleteeSiSpecifiee(adresse=self.adresse_correspondance),
        ]


@attr.dataclass(frozen=True, slots=True)
class DocumentsDemandesCompletesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    documents_reclames: List[EmplacementDocument]
    reponses_documents_a_completer: Dict[str, List[str]]

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldCompleterTousLesDocumentsReclames(
                documents_reclames=self.documents_reclames,
                reponses_documents_a_completer=self.reponses_documents_a_completer,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class QuarantaineValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    merge_proposal: MergeProposalDTO

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldNePasEtreEnQuarantaine(
                merge_proposal=self.merge_proposal,
            ),
        ]
