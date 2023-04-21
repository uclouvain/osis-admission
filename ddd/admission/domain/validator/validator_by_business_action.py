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

import datetime
from typing import List, Optional, Tuple, Set

import attr

from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceAcademiqueDTO
from admission.ddd.admission.domain.model._candidat_adresse import CandidatAdresse
from admission.ddd.admission.domain.model._candidat_signaletique import CandidatSignaletique
from admission.ddd.admission.domain.validator import *
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
    numero_passeport: Optional[str]
    passeport: List[str]

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
            ),
            ShouldCandidatAuthentiquerIdentite(
                numero_registre_national_belge=self.numero_registre_national_belge,
                numero_carte_identite=self.numero_carte_identite,
                carte_identite=self.carte_identite,
            ),
            ShouldCandidatSpecifierNOMASiDejaInscrit(
                noma_derniere_inscription_ucl=self.noma_derniere_inscription_ucl,
                annee_derniere_inscription_ucl=self.annee_derniere_inscription_ucl,
            ),
        ]


@attr.dataclass(frozen=True, slots=True)
class CoordonneesValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    adresse_email_privee: str
    domicile_legal: Optional['CandidatAdresse']
    adresse_correspondance: Optional['CandidatAdresse']

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldAdresseDomicileLegalCandidatEtreCompletee(adresse=self.domicile_legal),
            ShouldAdresseCorrespondanceEtreCompleteeSiSpecifiee(adresse=self.adresse_correspondance),
        ]
