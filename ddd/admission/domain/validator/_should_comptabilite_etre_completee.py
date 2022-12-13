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
from typing import List, Optional

import attr

from admission.ddd.admission.enums import ChoixTypeCompteBancaire
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AbsenceDeDetteNonCompleteeException,
    CarteBancaireRemboursementAutreFormatNonCompleteException,
    CarteBancaireRemboursementIbanNonCompleteException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldAbsenceDeDetteEtreCompletee(BusinessValidator):
    attestation_absence_dette_etablissement: List[str]
    a_frequente_recemment_etablissement_communaute_fr: Optional[bool]

    def validate(self, *args, **kwargs):
        if self.a_frequente_recemment_etablissement_communaute_fr and not self.attestation_absence_dette_etablissement:
            raise AbsenceDeDetteNonCompleteeException


@attr.dataclass(frozen=True, slots=True)
class ShouldIBANCarteBancaireRemboursementEtreCompletee(BusinessValidator):
    type_numero_compte: Optional[ChoixTypeCompteBancaire]
    numero_compte_iban: Optional[str]
    prenom_titulaire_compte: Optional[str]
    nom_titulaire_compte: Optional[str]

    def validate(self, *args, **kwargs):
        if self.type_numero_compte == ChoixTypeCompteBancaire.IBAN and any(
            not champ
            for champ in [
                self.numero_compte_iban,
                self.prenom_titulaire_compte,
                self.nom_titulaire_compte,
            ]
        ):
            raise CarteBancaireRemboursementIbanNonCompleteException


@attr.dataclass(frozen=True, slots=True)
class ShouldAutreFormatCarteBancaireRemboursementEtreCompletee(BusinessValidator):
    type_numero_compte: Optional[ChoixTypeCompteBancaire]
    numero_compte_autre_format: Optional[str]
    code_bic_swift_banque: Optional[str]
    prenom_titulaire_compte: Optional[str]
    nom_titulaire_compte: Optional[str]

    def validate(self, *args, **kwargs):
        if self.type_numero_compte == ChoixTypeCompteBancaire.AUTRE_FORMAT and any(
            not champ
            for champ in [
                self.numero_compte_autre_format,
                self.code_bic_swift_banque,
                self.prenom_titulaire_compte,
                self.nom_titulaire_compte,
            ]
        ):
            raise CarteBancaireRemboursementAutreFormatNonCompleteException
