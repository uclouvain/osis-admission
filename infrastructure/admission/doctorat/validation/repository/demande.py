# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List, Optional

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.doctorate import DemandeProxy
from admission.ddd.admission.domain.model._profil_candidat import ProfilCandidat
from admission.ddd.admission.doctorat.validation.domain.model.demande import Demande, DemandeIdentity
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC
from admission.ddd.admission.doctorat.validation.domain.service.proposition_identity import (
    PropositionIdentityTranslator,
)
from admission.ddd.admission.doctorat.validation.domain.validator.exceptions import DemandeNonTrouveeException
from admission.ddd.admission.doctorat.validation.dtos import DemandeDTO, ProfilCandidatDTO
from admission.ddd.admission.doctorat.validation.repository.i_demande import IDemandeRepository


class DemandeRepository(IDemandeRepository):
    @classmethod
    def search_dto(
        cls,
        etat_cdd: Optional[str] = '',
        etat_sic: Optional[str] = '',
        entity_ids: Optional[List['DemandeIdentity']] = None,
        **kwargs,
    ) -> List['DemandeDTO']:
        qs = DemandeProxy.objects.all()
        if etat_sic:
            qs = qs.filter(status_sic=etat_sic)
        if etat_cdd:
            qs = qs.filter(status_cdd=etat_cdd)
        if entity_ids is not None:
            qs = qs.filter(uuid__in=[e.uuid for e in entity_ids])
        return [cls._load_dto(demande) for demande in qs]

    @classmethod
    def get(cls, entity_id: 'DemandeIdentity') -> 'Demande':
        try:
            admission: DemandeProxy = DemandeProxy.objects.get(uuid=entity_id.uuid)
        except DoctorateAdmission.DoesNotExist:
            raise DemandeNonTrouveeException
        return Demande(
            profil_soumis_candidat=ProfilCandidat.from_dict(admission.submitted_profile),
            entity_id=entity_id,
            proposition_id=PropositionIdentityTranslator.convertir_depuis_demande(entity_id),
            statut_cdd=ChoixStatutCDD[admission.status_cdd],
            statut_sic=ChoixStatutSIC[admission.status_sic],
            modifiee_le=admission.modified_at,
            admission_confirmee_le=admission.submitted_at,
        )

    @classmethod
    def search(cls, entity_ids: Optional[List['DemandeIdentity']] = None, **kwargs) -> List['Demande']:
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'DemandeIdentity', **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def save(cls, entity: 'Demande') -> None:
        DoctorateAdmission.objects.update_or_create(
            uuid=entity.entity_id.uuid,
            defaults={
                'submitted_profile': entity.profil_soumis_candidat.to_dict(),
                'submitted_at': entity.admission_confirmee_le,
                'status_cdd': entity.statut_cdd.name,
                'status_sic': entity.statut_sic.name,
            },
        )

    @classmethod
    def get_dto(cls, entity_id) -> DemandeDTO:
        return cls._load_dto(DemandeProxy.objects.get(uuid=entity_id.uuid))

    @classmethod
    def _load_dto(cls, demande: DemandeProxy) -> DemandeDTO:
        return DemandeDTO(
            uuid=demande.uuid,
            statut_cdd=demande.status_cdd,
            statut_sic=demande.status_sic,
            derniere_modification=demande.modified_at,
            admission_confirmee_le=demande.submitted_at,
            profil_soumis_candidat=ProfilCandidatDTO.from_dict(
                dict_profile=demande.submitted_profile,
                nom_pays_nationalite=demande.submitted_profile_country_of_citizenship_name or '',  # from annotation
                nom_pays_adresse=demande.submitted_profile_country_name or '',  # from annotation
            ),
            # TODO use the related fields when they will be available
            pre_admission_acceptee_le=None,
            admission_acceptee_le=None,
        )
