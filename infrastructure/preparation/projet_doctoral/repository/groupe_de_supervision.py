# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.contrib.models import DoctorateAdmission
from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.domain.model._cotutelle import Cotutelle
from admission.ddd.preparation.projet_doctoral.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
)
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import PropositionIdentity
from admission.ddd.preparation.projet_doctoral.dtos import CotutelleDTO
from admission.ddd.preparation.projet_doctoral.repository.i_groupe_de_supervision import \
    IGroupeDeSupervisionRepository
from osis_signature.models import Process


class GroupeDeSupervisionRepository(IGroupeDeSupervisionRepository):
    @classmethod
    def get_by_proposition_id(cls, proposition_id: 'PropositionIdentity') -> 'GroupeDeSupervision':
        proposition = DoctorateAdmission.objects.get(uuid=proposition_id.uuid)
        if not proposition.supervision_group_id:
            groupe = Process.objects.create()
        else:
            groupe = proposition.supervision_group
        return GroupeDeSupervision(
            entity_id=GroupeDeSupervisionIdentity(uuid=groupe.uuid),
            proposition_id=PropositionIdentityBuilder.build_from_uuid(proposition.uuid),
            cotutelle=Cotutelle(
                motivation=proposition.cotutelle_motivation,
                institution=proposition.cotutelle_institution,
                demande_ouverture=proposition.cotutelle_opening_request,
                convention=proposition.cotutelle_convention,
                autres_documents=proposition.cotutelle_other_documents,
            ),
        )

    @classmethod
    def get_cotutelle_dto(cls, uuid_proposition: str) -> 'CotutelleDTO':
        proposition_id = PropositionIdentityBuilder.build_from_uuid(uuid_proposition)
        groupe = cls.get_by_proposition_id(proposition_id=proposition_id)
        return CotutelleDTO(
            motivation=groupe.cotutelle.motivation,
            institution=groupe.cotutelle.institution,
            demande_ouverture=groupe.cotutelle.demande_ouverture,
            convention=groupe.cotutelle.convention,
            autres_documents=groupe.cotutelle.autres_documents,
        )

    @classmethod
    def get(cls, entity_id: 'GroupeDeSupervisionIdentity') -> 'GroupeDeSupervision':
        raise NotImplementedError

    @classmethod
    def search(
            cls,
            entity_ids: Optional[List['GroupeDeSupervisionIdentity']] = None,
            **kwargs
    ) -> List['GroupeDeSupervision']:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'GroupeDeSupervisionIdentity', **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def save(cls, entity: 'GroupeDeSupervision') -> None:
        proposition = DoctorateAdmission.objects.get(uuid=entity.proposition_id.uuid)
        proposition.cotutelle_motivation = entity.cotutelle.motivation
        proposition.cotutelle_institution = entity.cotutelle.institution
        proposition.cotutelle_opening_request = entity.cotutelle.demande_ouverture
        proposition.cotutelle_convention = entity.cotutelle.convention
        proposition.cotutelle_other_documents = entity.cotutelle.autres_documents
        proposition.save()
