# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from rest_framework import serializers

from admission.ddd.admission.formation_generale.commands import (
    PayerFraisDossierPropositionSuiteDemandeCommand,
    PayerFraisDossierPropositionSuiteSoumissionCommand,
    SpecifierPaiementVaEtreOuvertParCandidatCommand,
)
from admission.ddd.admission.formation_generale.dtos.paiement import PaiementDTO
from base.utils.serializers import DTOSerializer

__all__ = [
    'PayerFraisDossierPropositionSuiteDemandeCommandSerializer',
    'PayerFraisDossierPropositionSuiteSoumissionCommandSerializer',
    'SpecifierPaiementVaEtreOuvertParCandidatCommandSerializer',
    'PaiementDTOSerializer',
]


class PayerFraisDossierPropositionSuiteDemandeCommandSerializer(DTOSerializer):
    class Meta:
        source = PayerFraisDossierPropositionSuiteDemandeCommand


class PayerFraisDossierPropositionSuiteSoumissionCommandSerializer(DTOSerializer):
    class Meta:
        source = PayerFraisDossierPropositionSuiteSoumissionCommand


class SpecifierPaiementVaEtreOuvertParCandidatCommandSerializer(DTOSerializer):
    class Meta:
        source = SpecifierPaiementVaEtreOuvertParCandidatCommand


class PaiementDTOSerializer(DTOSerializer):
    class Meta:
        source = PaiementDTO
        extra_kwargs = {
            # Necessary for decimal fields
            'montant': {
                'decimal_places': 2,
                'max_digits': 6,
            }
        }
