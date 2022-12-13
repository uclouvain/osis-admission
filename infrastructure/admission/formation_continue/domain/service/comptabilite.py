##############################################################################
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
##############################################################################
from admission.contrib.models import Accounting
from admission.ddd.admission.formation_continue.domain.service.i_comptabilite import IComptabiliteTranslator
from admission.ddd.admission.formation_continue.dtos import ComptabiliteDTO


class ComptabiliteTranslator(IComptabiliteTranslator):
    @classmethod
    def get_comptabilite_dto(cls, proposition_uuid: str) -> ComptabiliteDTO:
        accounting = Accounting.objects.get(admission__uuid=proposition_uuid)

        return ComptabiliteDTO(
            etudiant_solidaire=accounting.solidarity_student,
            type_numero_compte=accounting.account_number_type,
            numero_compte_iban=accounting.iban_account_number,
            iban_valide=accounting.valid_iban,
            numero_compte_autre_format=accounting.other_format_account_number,
            code_bic_swift_banque=accounting.bic_swift_code,
            prenom_titulaire_compte=accounting.account_holder_first_name,
            nom_titulaire_compte=accounting.account_holder_last_name,
        )
