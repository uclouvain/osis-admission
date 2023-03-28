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
from typing import Optional

from admission.ddd.admission.doctorat.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervisionIdentity,
    SignataireIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_membre_CA import IMembreCATranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    DejaMembreException,
    MembreNonExterneException,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from osis_common.ddd import interface


class MembresGroupeDeSupervision(interface.DomainService):
    @classmethod
    def verifier_pas_deja_present(
        cls,
        groupe_id: 'GroupeDeSupervisionIdentity',
        groupe_de_supervision_repository: 'IGroupeDeSupervisionRepository',
        matricule: Optional[str],
        email: Optional[str],
    ):
        membres = groupe_de_supervision_repository.get_members(groupe_id)
        for membre in membres:
            if (
                # Matricule déjà référencé
                matricule
                and matricule == membre.matricule
                # E-mail déjà référencé
                or not matricule
                and membre.email == email
            ):
                raise DejaMembreException

    @classmethod
    def verifier_externe(
        cls,
        signataire: 'SignataireIdentity',
        promoteur_translator: 'IPromoteurTranslator',
        membre_ca_translator: 'IMembreCATranslator',
    ) -> None:
        # Verifier que le membre est bien externe
        if (
            isinstance(signataire, PromoteurIdentity)
            and not promoteur_translator.get_dto(signataire).est_externe
            or isinstance(signataire, MembreCAIdentity)
            and not membre_ca_translator.get_dto(signataire).est_externe
        ):
            raise MembreNonExterneException
