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
from typing import List, Optional

import attr

from admission.ddd import BE_ISO_CODE
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    CarteIdentiteeNonSpecifieeException,
    DateOuAnneeNaissanceNonSpecifieeException,
    DetailsPasseportNonSpecifiesException,
    IdentificationNonCompleteeException,
    NomEtPrenomNonSpecifiesException,
    NumeroIdentiteBelgeNonSpecifieException,
    NumeroIdentiteNonSpecifieException,
    SpecifierNOMASiDejaInscritException,
)
from admission.ddd.admission.domain.model._candidat_signaletique import CandidatSignaletique
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldSignaletiqueCandidatEtreCompletee(BusinessValidator):
    signaletique: 'CandidatSignaletique'

    def validate(self, *args, **kwargs):
        champs_obligatoires = [
            'sexe',
            'genre',
            'pays_nationalite',
            'photo_identite',
            'langue_contact',
            'pays_naissance',
            'lieu_naissance',
            'etat_civil',
        ]
        if not all(getattr(self.signaletique, champ_obligatoire) for champ_obligatoire in champs_obligatoires):
            raise IdentificationNonCompleteeException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatSpecifierNomOuPrenom(BusinessValidator):
    nom: Optional[str]
    prenom: Optional[str]

    def validate(self, *args, **kwargs):
        if not self.nom and not self.prenom:
            raise NomEtPrenomNonSpecifiesException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatSpecifierNumeroIdentite(BusinessValidator):
    numero_registre_national_belge: Optional[str]
    numero_carte_identite: Optional[str]
    numero_passeport: Optional[str]

    def validate(self, *args, **kwargs):
        if not (self.numero_registre_national_belge or self.numero_carte_identite or self.numero_passeport):
            raise NumeroIdentiteNonSpecifieException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatBelgeSpecifierNumeroRegistreNationalBelge(BusinessValidator):
    numero_registre_national_belge: Optional[str]
    pays_nationalite: Optional[str]
    pays_residence: Optional[str]

    def validate(self, *args, **kwargs):
        if self.pays_nationalite == self.pays_residence == BE_ISO_CODE and not self.numero_registre_national_belge:
            raise NumeroIdentiteBelgeNonSpecifieException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatSpecifierDateOuAnneeNaissance(BusinessValidator):
    date_naissance: Optional[datetime.date]
    annee_naissance: Optional[int]

    def validate(self, *args, **kwargs):
        if not (self.date_naissance or self.annee_naissance):
            raise DateOuAnneeNaissanceNonSpecifieeException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatAuthentiquerPasseport(BusinessValidator):
    numero_passeport: Optional[str]
    passeport: List[str]

    def validate(self, *args, **kwargs):
        if self.numero_passeport and not self.passeport:
            raise DetailsPasseportNonSpecifiesException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatAuthentiquerIdentite(BusinessValidator):
    numero_registre_national_belge: Optional[str]
    numero_carte_identite: Optional[str]
    carte_identite: List[str]

    def validate(self, *args, **kwargs):
        if (self.numero_registre_national_belge or self.numero_carte_identite) and not self.carte_identite:
            raise CarteIdentiteeNonSpecifieeException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatSpecifierNOMASiDejaInscrit(BusinessValidator):
    noma_derniere_inscription_ucl: Optional[str]
    annee_derniere_inscription_ucl: Optional[int]

    def validate(self, *args, **kwargs):
        if self.annee_derniere_inscription_ucl and not self.noma_derniere_inscription_ucl:
            raise SpecifierNOMASiDejaInscritException
