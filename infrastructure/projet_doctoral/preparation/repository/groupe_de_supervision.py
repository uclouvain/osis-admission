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
from collections import defaultdict
from typing import List, Optional, Union

from admission.auth.roles.ca_member import CommitteeMember
from admission.auth.roles.promoter import Promoter
from admission.contrib.models import DoctorateAdmission, SupervisionActor
from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.projet_doctoral.doctorat.domain.model.doctorat import DoctoratIdentity
from admission.ddd.projet_doctoral.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.projet_doctoral.preparation.domain.model._cotutelle import Cotutelle, pas_de_cotutelle
from admission.ddd.projet_doctoral.preparation.domain.model._enums import (
    ChoixStatutProposition,
    ChoixStatutSignatureGroupeDeSupervision,
)
from admission.ddd.projet_doctoral.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._signature_membre_CA import SignatureMembreCA
from admission.ddd.projet_doctoral.preparation.domain.model._signature_promoteur import (
    ChoixEtatSignature,
    SignaturePromoteur,
)
from admission.ddd.projet_doctoral.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
)
from admission.ddd.projet_doctoral.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.projet_doctoral.preparation.dtos import CotutelleDTO
from admission.ddd.projet_doctoral.preparation.repository.i_groupe_de_supervision import IGroupeDeSupervisionRepository
from base.models.person import Person
from osis_signature.models import Process, StateHistory


class GroupeDeSupervisionRepository(IGroupeDeSupervisionRepository):
    @classmethod
    def get_by_proposition_id(cls, proposition_id: 'PropositionIdentity') -> 'GroupeDeSupervision':
        proposition = DoctorateAdmission.objects.select_related('supervision_group').get(uuid=proposition_id.uuid)
        if not proposition.supervision_group_id:
            groupe = Process.objects.create()
        else:
            groupe = proposition.supervision_group

        if proposition.cotutelle is not None:
            cotutelle = Cotutelle(
                motivation=proposition.cotutelle_motivation,
                institution_fwb=proposition.cotutelle_institution_fwb,
                institution=proposition.cotutelle_institution,
                demande_ouverture=proposition.cotutelle_opening_request,
                convention=proposition.cotutelle_convention,
                autres_documents=proposition.cotutelle_other_documents,
            )
        else:
            cotutelle = None

        # Single, ordered query for all actors
        actors = defaultdict(list)
        for actor in groupe.actors.select_related('supervisionactor', 'person').order_by('person__last_name'):
            actors[actor.supervisionactor.type].append(actor)

        return GroupeDeSupervision(
            entity_id=GroupeDeSupervisionIdentity(uuid=groupe.uuid),
            proposition_id=PropositionIdentityBuilder.build_from_uuid(proposition.uuid),
            signatures_promoteurs=[
                SignaturePromoteur(
                    promoteur_id=PromoteurIdentity(actor.person.global_id),
                    etat=ChoixEtatSignature[actor.state],
                    date=actor.last_state_date,
                    commentaire_externe=actor.comment,
                    commentaire_interne=actor.supervisionactor.internal_comment,
                    motif_refus=actor.supervisionactor.rejection_reason,
                    pdf=actor.supervisionactor.pdf_from_candidate,
                )
                for actor in actors.get(ActorType.PROMOTER.name, [])
            ],
            signatures_membres_CA=[
                SignatureMembreCA(
                    membre_CA_id=MembreCAIdentity(actor.person.global_id),
                    etat=ChoixEtatSignature[actor.state],
                    date=actor.last_state_date,
                    commentaire_externe=actor.comment,
                    commentaire_interne=actor.supervisionactor.internal_comment,
                    pdf=actor.supervisionactor.pdf_from_candidate,
                )
                for actor in actors.get(ActorType.CA_MEMBER.name, [])
            ],
            promoteur_reference_id=next(
                (
                    PromoteurIdentity(actor.person.global_id)
                    for actor in actors.get(ActorType.PROMOTER.name, [])
                    if actor.supervisionactor.is_reference_promoter
                ),
                None,
            ),
            cotutelle=cotutelle,
            statut_signature=ChoixStatutSignatureGroupeDeSupervision.SIGNING_IN_PROGRESS
            if proposition.status == ChoixStatutProposition.SIGNING_IN_PROGRESS.name
            else None,
        )

    @classmethod
    def get_by_doctorat_id(cls, doctorat_id: 'DoctoratIdentity') -> 'GroupeDeSupervision':
        return cls.get_by_proposition_id(PropositionIdentityBuilder.build_from_uuid(doctorat_id.uuid))

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
            institution_fwb=groupe.cotutelle and groupe.cotutelle.institution_fwb,
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
        **kwargs,
    ) -> List['GroupeDeSupervision']:
        if matricule_membre:
            propositions = (
                DoctorateAdmission.objects.filter(supervision_group__actors__person__global_id=matricule_membre)
                .distinct('pk')
                .order_by('-pk')
            )
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
        cls._update_members(current_promoteurs, entity.signatures_promoteurs, entity.promoteur_reference_id)
        cls._update_members(current_members, entity.signatures_membres_CA)

        # Add missing actors
        promoteurs_ids = current_promoteurs.values_list('person__global_id', flat=True)
        for person in new_promoteurs_persons:
            if person.global_id not in promoteurs_ids:
                SupervisionActor.objects.create(
                    person=person,
                    type=ActorType.PROMOTER.name,
                    process_id=groupe.uuid,
                    is_reference_promoter=bool(
                        entity.promoteur_reference_id and entity.promoteur_reference_id.matricule == person.global_id
                    ),
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
            proposition.cotutelle_institution_fwb = entity.cotutelle.institution_fwb
            proposition.cotutelle_institution = entity.cotutelle.institution
            proposition.cotutelle_opening_request = entity.cotutelle.demande_ouverture
            proposition.cotutelle_convention = entity.cotutelle.convention
            proposition.cotutelle_other_documents = entity.cotutelle.autres_documents
        proposition.save()

    @classmethod
    def _update_members(
        cls,
        member_list: list,
        signature_list: Union[List[SignaturePromoteur], List[SignatureMembreCA]],
        reference_promoter: Optional[PromoteurIdentity] = None,
    ):
        for actor in member_list:
            membre = cls._get_member_from_matricule(signature_list, actor.person.global_id)
            if actor.state != membre.etat.name:
                StateHistory.objects.create(state=membre.etat.name, actor_id=actor.id)
                if membre.etat.name in [ChoixEtatSignature.APPROVED.name, ChoixEtatSignature.DECLINED.name]:
                    actor.comment = membre.commentaire_externe
                    actor.supervisionactor.pdf_from_candidate = membre.pdf
                    actor.supervisionactor.internal_comment = membre.commentaire_interne
                    actor.supervisionactor.rejection_reason = membre.motif_refus
                    actor.supervisionactor.is_reference_promoter = bool(
                        reference_promoter and membre.promoteur_id == reference_promoter
                    )
                    actor.supervisionactor.save()
                    actor.save()
            # Actor is no longer the reference promoter
            if actor.supervisionactor.is_reference_promoter and (
                not reference_promoter or actor.person.global_id != reference_promoter.matricule
            ):
                actor.supervisionactor.is_reference_promoter = False
                actor.supervisionactor.save()
            elif (
                # Actor is the reference promoter and need to be updated
                reference_promoter
                and not actor.supervisionactor.is_reference_promoter
                and actor.person.global_id == reference_promoter.matricule
            ):
                actor.supervisionactor.is_reference_promoter = True
                actor.supervisionactor.save()

    @classmethod
    def _get_member_from_matricule(cls, signatures: list, matricule) -> Union[SignaturePromoteur, SignatureMembreCA]:
        if isinstance(signatures[0], SignaturePromoteur):
            return next(a for a in signatures if a.promoteur_id.matricule == matricule)  # pragma: no branch
        return next(a for a in signatures if a.membre_CA_id.matricule == matricule)  # pragma: no branch
