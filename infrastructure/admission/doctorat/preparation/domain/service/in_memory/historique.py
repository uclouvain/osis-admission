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

from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    SignataireIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.dtos import AvisDTO


class HistoriqueInMemory(IHistorique):
    @classmethod
    def historiser_initiation(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_completion(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_completion_cotutelle(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_avis(cls, proposition: Proposition, signataire_id: 'SignataireIdentity', avis: AvisDTO):
        pass

    @classmethod
    def historiser_ajout_membre(
        cls,
        proposition: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
    ):
        pass

    @classmethod
    def historiser_suppression_membre(
        cls,
        proposition: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: 'SignataireIdentity',
    ):
        pass

    @classmethod
    def historiser_demande_signatures(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_soumission(cls, proposition: Proposition):
        pass

    @classmethod
    def historiser_suppression(cls, proposition: Proposition):
        pass
