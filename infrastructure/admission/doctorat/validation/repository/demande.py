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
from typing import List, Optional

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.doctorate import DemandeProxy
from admission.ddd.admission.doctorat.validation.domain.model._profil_candidat import ProfilCandidat
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
            profil_candidat=ProfilCandidat(
                prenom=admission.submitted_profile.get('identification').get('first_name'),
                nom=admission.submitted_profile.get('identification').get('last_name'),
                genre=admission.submitted_profile.get('identification').get('gender'),
                nationalite=admission.submitted_profile.get('identification').get('country_of_citizenship'),
                email=admission.submitted_profile.get('coordinates').get('email'),
                pays=admission.submitted_profile.get('coordinates').get('country'),
                code_postal=admission.submitted_profile.get('coordinates').get('postal_code'),
                ville=admission.submitted_profile.get('coordinates').get('city'),
                lieu_dit=admission.submitted_profile.get('coordinates').get('place'),
                rue=admission.submitted_profile.get('coordinates').get('street'),
                numero_rue=admission.submitted_profile.get('coordinates').get('street_number'),
                boite_postale=admission.submitted_profile.get('coordinates').get('postal_box'),
            ),
            entity_id=entity_id,
            proposition_id=PropositionIdentityTranslator.convertir_depuis_demande(entity_id),
            statut_cdd=ChoixStatutCDD[admission.status_cdd],
            statut_sic=ChoixStatutSIC[admission.status_sic],
            modifiee_le=admission.modified_at,
            pre_admission_confirmee_le=admission.pre_admission_submission_date,
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
                'submitted_profile': {
                    'identification': {
                        'first_name': entity.profil_candidat.prenom,
                        'last_name': entity.profil_candidat.nom,
                        'gender': entity.profil_candidat.genre,
                        'country_of_citizenship': entity.profil_candidat.nationalite,
                    },
                    'coordinates': {
                        'email': entity.profil_candidat.email,
                        'country': entity.profil_candidat.pays,
                        'postal_code': entity.profil_candidat.code_postal,
                        'city': entity.profil_candidat.ville,
                        'place': entity.profil_candidat.lieu_dit,
                        'street': entity.profil_candidat.rue,
                        'street_number': entity.profil_candidat.numero_rue,
                        'postal_box': entity.profil_candidat.boite_postale,
                    },
                },
                'pre_admission_submission_date': entity.pre_admission_confirmee_le,
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
            pre_admission_confirmee_le=demande.pre_admission_submission_date,
            admission_confirmee_le=demande.submitted_at,
            profil_candidat=ProfilCandidatDTO(
                prenom=demande.submitted_profile.get('identification').get('first_name'),
                nom=demande.submitted_profile.get('identification').get('last_name'),
                genre=demande.submitted_profile.get('identification').get('gender'),
                nationalite=demande.submitted_profile.get('identification').get('country_of_citizenship'),
                nom_pays_nationalite=demande.nom_pays_nationalite or '',  # from DemandeManager annotation
                email=demande.submitted_profile.get('coordinates').get('email'),
                pays=demande.submitted_profile.get('coordinates').get('country'),
                nom_pays=demande.nom_pays or '',  # from DemandeManager annotation
                code_postal=demande.submitted_profile.get('coordinates').get('postal_code'),
                ville=demande.submitted_profile.get('coordinates').get('city'),
                lieu_dit=demande.submitted_profile.get('coordinates').get('place'),
                rue=demande.submitted_profile.get('coordinates').get('street'),
                numero_rue=demande.submitted_profile.get('coordinates').get('street_number'),
                boite_postale=demande.submitted_profile.get('coordinates').get('postal_box'),
            ),
            # TODO use the related fields when they will be available
            pre_admission_acceptee_le=None,
            admission_acceptee_le=None,
        )
