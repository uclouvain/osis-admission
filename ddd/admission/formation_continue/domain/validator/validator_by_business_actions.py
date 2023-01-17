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
from typing import List

import attr

from admission.ddd.admission.domain.validator import (
    ShouldIBANCarteBancaireRemboursementEtreCompletee,
    ShouldAutreFormatCarteBancaireRemboursementEtreCompletee,
    ShouldTypeCompteBancaireRemboursementEtreComplete,
)
from admission.ddd.admission.formation_continue.domain.model._comptabilite import Comptabilite
from admission.ddd.admission.formation_continue.domain.validator._should_comptabilite_etre_completee import (
    ShouldAffiliationsEtreCompletees,
)
from base.ddd.utils.business_validator import BusinessValidator, TwoStepsMultipleBusinessExceptionListValidator


@attr.dataclass(frozen=True, slots=True)
class FormationContinueComptabiliteValidatorList(TwoStepsMultipleBusinessExceptionListValidator):
    comptabilite: Comptabilite

    def get_data_contract_validators(self) -> List[BusinessValidator]:
        return []

    def get_invariants_validators(self) -> List[BusinessValidator]:
        return [
            ShouldAffiliationsEtreCompletees(
                etudiant_solidaire=self.comptabilite.etudiant_solidaire,
            ),
            ShouldTypeCompteBancaireRemboursementEtreComplete(
                type_numero_compte=self.comptabilite.type_numero_compte,
            ),
            ShouldIBANCarteBancaireRemboursementEtreCompletee(
                type_numero_compte=self.comptabilite.type_numero_compte,
                numero_compte_iban=self.comptabilite.numero_compte_iban,
                prenom_titulaire_compte=self.comptabilite.prenom_titulaire_compte,
                nom_titulaire_compte=self.comptabilite.nom_titulaire_compte,
            ),
            ShouldAutreFormatCarteBancaireRemboursementEtreCompletee(
                type_numero_compte=self.comptabilite.type_numero_compte,
                numero_compte_autre_format=self.comptabilite.numero_compte_autre_format,
                code_bic_swift_banque=self.comptabilite.code_bic_swift_banque,
                prenom_titulaire_compte=self.comptabilite.prenom_titulaire_compte,
                nom_titulaire_compte=self.comptabilite.nom_titulaire_compte,
            ),
        ]
