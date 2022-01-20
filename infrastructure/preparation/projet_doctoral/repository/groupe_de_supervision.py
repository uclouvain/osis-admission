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

from admission.auth.roles.ca_member import CommitteeMember
from admission.auth.roles.promoter import Promoter
from admission.contrib.models import DoctorateAdmission, SupervisionActor
from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import \
    PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.domain.model._cotutelle import Cotutelle, pas_de_cotutelle
from admission.ddd.preparation.projet_doctoral.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.preparation.projet_doctoral.domain.model._promoteur import PromoteurIdentity
from admission.ddd.preparation.projet_doctoral.domain.model._signature_membre_CA import SignatureMembreCA
from admission.ddd.preparation.projet_doctoral.domain.model._signature_promoteur import SignaturePromoteur, \
    ChoixEtatSignature
from admission.ddd.preparation.projet_doctoral.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
)
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import PropositionIdentity
from admission.ddd.preparation.projet_doctoral.dtos import CotutelleDTO
from admission.ddd.preparation.projet_doctoral.repository.i_groupe_de_supervision import \
    IGroupeDeSupervisionRepository
from base.models.person import Person
from osis_signature.models import Process, StateHistory


class GroupeDeSupervisionRepository(IGroupeDeSupervisionRepository):
    @classmethod
    def get_by_proposition_id(cls, proposition_id: 'PropositionIdentity') -> 'GroupeDeSupervision':
        proposition = DoctorateAdmission.objects.get(uuid=proposition_id.uuid)
        if not proposition.supervision_group_id:
            groupe = Process.objects.create()
        else:
            groupe = proposition.supervision_group

        if proposition.cotutelle is not None:
            cotutelle = Cotutelle(
                motivation=proposition.cotutelle_motivation,
                institution=proposition.cotutelle_institution,
                demande_ouverture=proposition.cotutelle_opening_request,
                convention=proposition.cotutelle_convention,
                autres_documents=proposition.cotutelle_other_documents,
            )
        else:
            cotutelle = None

        return GroupeDeSupervision(
            entity_id=GroupeDeSupervisionIdentity(uuid=groupe.uuid),
            proposition_id=PropositionIdentityBuilder.build_from_uuid(proposition.uuid),
            signatures_promoteurs=[
                SignaturePromoteur(promoteur_id=PromoteurIdentity(actor.person.global_id),
                                   etat=ChoixEtatSignature[actor.state],
                                   commentaire_externe=actor.comment,
                                   commentaire_interne=actor.supervisionactor.internal_comment,
                                   )
                for actor in groupe.actors.filter(supervisionactor__type__in=[
                    ActorType.PROMOTER.name,
                ])
            ],
            signatures_membres_CA=[
                SignatureMembreCA(membre_CA_id=MembreCAIdentity(actor.person.global_id),
                                  etat=ChoixEtatSignature[actor.state],
                                  commentaire_externe=actor.comment,
                                  commentaire_interne=actor.supervisionactor.internal_comment,
                                  )
                for actor in groupe.actors.filter(supervisionactor__type=ActorType.CA_MEMBER.name)
            ],
            cotutelle=cotutelle,
        )

    @classmethod
    def get(cls, entity_id: 'GroupeDeSupervisionIdentity') -> 'GroupeDeSupervision':
        raise NotImplementedError

    @classmethod
    def get_cotutelle_dto(cls, uuid_proposition: str) -> 'CotutelleDTO':
        proposition_id = PropositionIdentityBuilder.build_from_uuid(uuid_proposition)
        groupe = cls.get_by_proposition_id(proposition_id=proposition_id)
        return CotutelleDTO(
            cotutelle=None if groupe.cotutelle is None else groupe.cotutelle != pas_de_cotutelle,
            motivation=groupe.cotutelle and groupe.cotutelle.motivation or '',
            institution=groupe.cotutelle and groupe.cotutelle.institution or '',
            demande_ouverture=groupe.cotutelle and groupe.cotutelle.demande_ouverture or [],
            convention=groupe.cotutelle and groupe.cotutelle.convention or [],
            autres_documents=groupe.cotutelle and groupe.cotutelle.autres_documents or [],
        )

    @classmethod
    def search(
            cls,
            entity_ids: Optional[List['GroupeDeSupervisionIdentity']] = None,
            matricule_membre: str = None,
            **kwargs
    ) -> List['GroupeDeSupervision']:
        if matricule_membre:
            propositions = DoctorateAdmission.objects.filter(
                supervision_group__actors__person__global_id=matricule_membre,
            ).distinct('pk').order_by('-pk')
            return [cls.get_by_proposition_id(pid) for pid in propositions]
        raise NotImplementedError

    @classmethod
    def delete(cls, entity_id: 'GroupeDeSupervisionIdentity', **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def save(cls, entity: 'GroupeDeSupervision') -> None:
        proposition = DoctorateAdmission.objects.get(uuid=entity.proposition_id.uuid)
        if not proposition.supervision_group_id:
            proposition.supervision_group = groupe = Process.objects.create()
        else:
            groupe = proposition.supervision_group

        # Delete actors not in the current signatures
        new_promoteurs_persons = Person.objects.filter(
            global_id__in=[a.promoteur_id.matricule for a in entity.signatures_promoteurs],
        )
        current_promoteurs = groupe.actors.filter(supervisionactor__type=ActorType.PROMOTER.name)
        current_promoteurs.exclude(person__in=new_promoteurs_persons).delete()

        new_membre_CA_persons = Person.objects.filter(
            global_id__in=[a.membre_CA_id.matricule for a in entity.signatures_membres_CA],
        )
        current_members = groupe.actors.filter(supervisionactor__type=ActorType.CA_MEMBER.name)
        current_members.exclude(person__in=new_membre_CA_persons).delete()

        # Update existing actors
        for actor in current_promoteurs:
            membre = next(a for a in entity.signatures_promoteurs  # pragma: no branch
                          if a.promoteur_id.matricule == actor.person.global_id)
            if actor.state != membre.etat.name:
                StateHistory.objects.create(state=membre.etat.name, actor_id=actor.id)
                if membre.etat.name in [ChoixEtatSignature.APPROVED.name, ChoixEtatSignature.REFUSED.name]:
                    actor.comment = membre.commentaire_externe
                    actor.supervisionactor.internal_comment = membre.commentaire_interne
                    actor.supervisionactor.rejection_reason = membre.motif_refus
                    actor.supervisionactor.save()
                    actor.save()

        for actor in current_members:
            membre = next(a for a in entity.signatures_membres_CA  # pragma: no branch
                          if a.membre_CA_id.matricule == actor.person.global_id)
            if actor.state != membre.etat.name:
                StateHistory.objects.create(state=membre.etat.name, actor_id=actor.id)
                if membre.etat.name in [ChoixEtatSignature.APPROVED.name, ChoixEtatSignature.REFUSED.name]:
                    actor.comment = membre.commentaire_externe
                    actor.supervisionactor.internal_comment = membre.commentaire_interne
                    actor.supervisionactor.rejection_reason = membre.motif_refus
                    actor.supervisionactor.save()
                    actor.save()

        # Add missing actors
        promoteurs_ids = current_promoteurs.values_list('person__global_id', flat=True)
        for person in new_promoteurs_persons:
            if person.global_id not in promoteurs_ids:
                SupervisionActor.objects.create(
                    person=person,
                    type=ActorType.PROMOTER.name,
                    process_id=groupe.uuid,
                )
                Promoter.objects.get_or_create(person=person)

        membre_CA_ids = current_members.values_list('person__global_id', flat=True)
        for person in new_membre_CA_persons:
            if person.global_id not in membre_CA_ids:
                SupervisionActor.objects.create(
                    person=person,
                    type=ActorType.CA_MEMBER.name,
                    process_id=groupe.uuid,
                )
                CommitteeMember.objects.get_or_create(person=person)

        proposition.cotutelle = None if entity.cotutelle is None else bool(entity.cotutelle.motivation)
        if entity.cotutelle:
            proposition.cotutelle_motivation = entity.cotutelle.motivation
            proposition.cotutelle_institution = entity.cotutelle.institution
            proposition.cotutelle_opening_request = entity.cotutelle.demande_ouverture
            proposition.cotutelle_convention = entity.cotutelle.convention
            proposition.cotutelle_other_documents = entity.cotutelle.autres_documents
        proposition.save()
