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
from functools import partial
from typing import List

from admission.ddd.parcours_doctoral.formation.builder.activite_identity_builder import ActiviteIdentityBuilder
from admission.ddd.parcours_doctoral.formation.domain.model.activite import Activite, ActiviteIdentity
from admission.ddd.parcours_doctoral.formation.domain.model.enums import CategorieActivite, StatutActivite
from admission.ddd.parcours_doctoral.formation.domain.validator.exceptions import ActiviteDoitEtreSoumise
from admission.ddd.parcours_doctoral.formation.repository.i_activite import IActiviteRepository
from base.ddd.utils.business_validator import execute_functions_and_aggregate_exceptions
from osis_common.ddd import interface


class AccepterActivites(interface.DomainService):
    @classmethod
    def verifier(cls, activite_uuids: List[str], activite_repository: IActiviteRepository) -> List[Activite]:
        entity_ids = [ActiviteIdentityBuilder.build_from_uuid(uuid) for uuid in activite_uuids]
        activites = activite_repository.get_multiple(entity_ids)
        execute_functions_and_aggregate_exceptions(
            *[partial(cls.verifier_statut, activite=activites[entity_id]) for entity_id in entity_ids]
        )
        return list(activites.values())

    @classmethod
    def verifier_statut(cls, activite: Activite):
        if activite.statut != StatutActivite.SOUMISE:
            raise ActiviteDoitEtreSoumise(activite.entity_id)

    @classmethod
    def accepter(cls, activites: List[Activite], activite_repository: IActiviteRepository) -> List[ActiviteIdentity]:
        for activite in activites:
            activite.accepter()
            # TODO Performance ?
            # TODO Communicate to OSIS-Parcours if UCL_COURSE
            activite_repository.save(activite)
            # Also accept sub-activities for seminars
            if activite.categorie == CategorieActivite.SEMINAR:
                for sous_activite in activite_repository.search(parent_id=activite.entity_id):
                    sous_activite.accepter()
                    activite_repository.save(sous_activite)
        return [activite.entity_id for activite in activites]
