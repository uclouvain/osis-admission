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
from typing import Union

from admission.ddd.admission.projet_doctoral.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.admission.projet_doctoral.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.projet_doctoral.preparation.domain.model.groupe_de_supervision import GroupeDeSupervision
from admission.ddd.admission.projet_doctoral.preparation.domain.model.proposition import Proposition
from admission.ddd.admission.projet_doctoral.preparation.dtos import AvisDTO
from osis_common.ddd import interface


class IHistorique(interface.DomainService):
    @classmethod
    def historiser_initiation(cls, proposition: Proposition):
        raise NotImplementedError

    @classmethod
    def historiser_completion(cls, proposition: Proposition):
        raise NotImplementedError

    @classmethod
    def historiser_completion_cotutelle(cls, proposition: Proposition):
        raise NotImplementedError

    @classmethod
    def historiser_avis(
        cls,
        proposition: Proposition,
        signataire_id: Union[PromoteurIdentity, MembreCAIdentity],
        avis: AvisDTO,
    ):
        raise NotImplementedError

    @classmethod
    def historiser_ajout_membre(
        cls,
        proposition: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: Union[PromoteurIdentity, MembreCAIdentity],
    ):
        raise NotImplementedError

    @classmethod
    def historiser_suppression_membre(
        cls,
        proposition: Proposition,
        groupe_de_supervision: GroupeDeSupervision,
        signataire_id: Union[PromoteurIdentity, MembreCAIdentity],
    ):
        raise NotImplementedError

    @classmethod
    def historiser_demande_signatures(cls, proposition: Proposition):
        raise NotImplementedError

    @classmethod
    def historiser_soumission(cls, proposition: Proposition):
        raise NotImplementedError

    @classmethod
    def historiser_suppression(cls, proposition: Proposition):
        raise NotImplementedError
