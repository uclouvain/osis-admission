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
from collections import defaultdict
from typing import List, Optional, Union

from django.db.models import F, Prefetch
from django.db.models.functions import Coalesce
from django.utils.translation import get_language, gettext_lazy as _
from osis_signature.enums import SignatureState

from admission.auth.roles.ca_member import CommitteeMember
from admission.auth.roles.promoter import Promoter
from admission.models import DoctorateAdmission, SupervisionActor
from admission.models.enums.actor_type import ActorType
from admission.ddd.admission.doctorat.preparation.builder.proposition_identity_builder import PropositionIdentityBuilder
from admission.ddd.admission.doctorat.preparation.domain.model._cotutelle import Cotutelle, pas_de_cotutelle
from admission.ddd.admission.doctorat.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._promoteur import PromoteurIdentity
from admission.ddd.admission.doctorat.preparation.domain.model._signature_membre_CA import SignatureMembreCA
from admission.ddd.admission.doctorat.preparation.domain.model._signature_promoteur import (
    SignaturePromoteur,
)
from admission.ddd.admission.doctorat.preparation.domain.model.doctorat import DoctoratIdentity
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixEtatSignature,
    ChoixStatutPropositionDoctorale,
    ChoixStatutSignatureGroupeDeSupervision,
)
from admission.ddd.admission.doctorat.preparation.domain.model.groupe_de_supervision import (
    GroupeDeSupervision,
    GroupeDeSupervisionIdentity,
    SignataireIdentity,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.dtos import CotutelleDTO, MembreCADTO, PromoteurDTO
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from base.models.person import Person
from osis_role.contrib.permissions import _get_roles_assigned_to_user
from osis_signature.models import Actor, Process, StateHistory
from reference.models.country import Country


class GroupeDeSupervisionRepository(IGroupeDeSupervisionRepository):
    @classmethod
    def _get_queryset(cls):
        return (
            DoctorateAdmission.objects.select_related('supervision_group')
            .only(
                "uuid",
                "status",
                "supervision_group",
                "cotutelle",
                "cotutelle_motivation",
                "cotutelle_institution_fwb",
                "cotutelle_institution",
                "cotutelle_other_institution_name",
                "cotutelle_other_institution_address",
                "cotutelle_opening_request",
                "cotutelle_convention",
                "cotutelle_other_documents",
            )
            .prefetch_related(
                Prefetch(
                    'supervision_group__actors',
                    Actor.objects.alias(dynamic_last_name=Coalesce(F('last_name'), F('person__last_name')))
                    .select_related('supervisionactor')
                    .order_by('dynamic_last_name'),
                    to_attr='ordered_members',
                )
            )
        )

    @classmethod
    def _load(cls, proposition):
        if proposition.cotutelle is not None:
            cotutelle = Cotutelle(
                motivation=proposition.cotutelle_motivation,
                institution_fwb=proposition.cotutelle_institution_fwb,
                institution=str(proposition.cotutelle_institution) if proposition.cotutelle_institution else "",
                autre_institution_nom=proposition.cotutelle_other_institution_name,
                autre_institution_adresse=proposition.cotutelle_other_institution_address,
                demande_ouverture=proposition.cotutelle_opening_request,
                convention=proposition.cotutelle_convention,
                autres_documents=proposition.cotutelle_other_documents,
            )
        else:
            cotutelle = None

        if not proposition.supervision_group_id:
            proposition.supervision_group = Process.objects.create()
            proposition.save(update_fields=['supervision_group'])

        groupe = proposition.supervision_group
        actors = defaultdict(list)
        for actor in getattr(groupe, 'ordered_members', []):
            actors[actor.supervisionactor.type].append(actor)

        return GroupeDeSupervision(
            entity_id=GroupeDeSupervisionIdentity(uuid=groupe.uuid),
            proposition_id=PropositionIdentityBuilder.build_from_uuid(proposition.uuid),
            signatures_promoteurs=[
                SignaturePromoteur(
                    promoteur_id=PromoteurIdentity(str(actor.uuid)),
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
                    membre_CA_id=MembreCAIdentity(str(actor.uuid)),
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
                    PromoteurIdentity(actor.uuid)
                    for actor in actors.get(ActorType.PROMOTER.name, [])
                    if actor.supervisionactor.is_reference_promoter
                ),
                None,
            ),
            cotutelle=cotutelle,
            statut_signature=ChoixStatutSignatureGroupeDeSupervision.SIGNING_IN_PROGRESS
            if proposition.status == ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name
            else None,
        )

    @classmethod
    def get_by_proposition_id(cls, proposition_id: 'PropositionIdentity') -> 'GroupeDeSupervision':
        proposition = cls._get_queryset().get(uuid=proposition_id.uuid)
        return cls._load(proposition)

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
        return cls.get_cotutelle_dto_from_model(cotutelle=groupe.cotutelle)

    @classmethod
    def search(
        cls,
        entity_ids: Optional[List['GroupeDeSupervisionIdentity']] = None,
        matricule_membre: str = None,
        **kwargs,
    ) -> List['GroupeDeSupervision']:
        if matricule_membre:
            propositions = (
                cls._get_queryset()
                .filter(supervision_group__actors__person__global_id=matricule_membre)
                .distinct('pk')
                .order_by('-pk')
            )
            return [cls._load(proposition) for proposition in propositions]
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

        current_promoteurs = groupe.actors.filter(supervisionactor__type=ActorType.PROMOTER.name)
        current_members = groupe.actors.filter(supervisionactor__type=ActorType.CA_MEMBER.name)

        # Remove old CA members (deleted by refusal)
        current_members.exclude(uuid__in=[s.membre_CA_id.uuid for s in entity.signatures_membres_CA]).delete()

        # Update existing actors
        cls._update_members(current_promoteurs, entity.signatures_promoteurs, entity.promoteur_reference_id)
        cls._update_members(current_members, entity.signatures_membres_CA)

        proposition.cotutelle = None if entity.cotutelle is None else bool(entity.cotutelle.motivation)
        if entity.cotutelle:
            proposition.cotutelle_motivation = entity.cotutelle.motivation
            proposition.cotutelle_institution_fwb = entity.cotutelle.institution_fwb
            proposition.cotutelle_institution = (
                None if not entity.cotutelle.institution else entity.cotutelle.institution
            )
            proposition.cotutelle_other_institution_name = entity.cotutelle.autre_institution_nom
            proposition.cotutelle_other_institution_address = entity.cotutelle.autre_institution_adresse
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
            membre = cls._get_member(signature_list, str(actor.uuid))
            if actor.state != membre.etat.name:
                StateHistory.objects.create(state=membre.etat.name, actor_id=actor.id)
                if membre.etat.name in [ChoixEtatSignature.APPROVED.name, ChoixEtatSignature.DECLINED.name]:
                    actor.comment = membre.commentaire_externe
                    actor.supervisionactor.pdf_from_candidate = membre.pdf
                    actor.supervisionactor.internal_comment = membre.commentaire_interne
                    actor.supervisionactor.rejection_reason = membre.motif_refus
                    actor.supervisionactor.is_reference_promoter = bool(
                        reference_promoter and str(actor.uuid) == str(reference_promoter.uuid)
                    )
                    actor.supervisionactor.save()
                    actor.save()
            if (
                # Actor is no longer the reference promoter
                actor.supervisionactor.is_reference_promoter
                and (not reference_promoter or str(actor.uuid) != str(reference_promoter.uuid))
            ):
                actor.supervisionactor.is_reference_promoter = False
                actor.supervisionactor.save()
            elif (
                # Actor is the reference promoter and need to be updated
                reference_promoter
                and not actor.supervisionactor.is_reference_promoter
                and str(actor.uuid) == str(reference_promoter.uuid)
            ):
                actor.supervisionactor.is_reference_promoter = True
                actor.supervisionactor.save()

    @classmethod
    def _get_member(cls, signatures: list, uuid: str) -> Union[SignaturePromoteur, SignatureMembreCA]:
        if isinstance(signatures[0], SignaturePromoteur):
            return next(s for s in signatures if s.promoteur_id.uuid == uuid)  # pragma: no branch
        return next(s for s in signatures if s.membre_CA_id.uuid == uuid)  # pragma: no branch

    @classmethod
    def add_member(
        cls,
        groupe_id: 'GroupeDeSupervisionIdentity',
        proposition_status: 'ChoixStatutPropositionDoctorale',
        type: Optional[ActorType] = None,
        matricule: Optional[str] = '',
        first_name: Optional[str] = '',
        last_name: Optional[str] = '',
        email: Optional[str] = '',
        is_doctor: bool = False,
        institute: Optional[str] = '',
        city: Optional[str] = '',
        country_code: Optional[str] = '',
        language: Optional[str] = '',
    ) -> 'SignataireIdentity':
        groupe = Process.objects.get(uuid=groupe_id.uuid)
        person = Person.objects.get(global_id=matricule) if matricule else None
        new_actor = SupervisionActor.objects.create(
            process=groupe,
            person=person,
            type=type.name,
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_doctor=is_doctor,
            institute=institute,
            city=city,
            country=Country.objects.get(iso_code=country_code) if country_code else None,
            language=language,
        )
        if type == ActorType.PROMOTER:
            group_name, model = 'promoters', Promoter
            signataire_id = PromoteurIdentity(str(new_actor.uuid))
        else:
            group_name, model = 'committee_members', CommitteeMember
            signataire_id = MembreCAIdentity(str(new_actor.uuid))
        if proposition_status != ChoixStatutPropositionDoctorale.EN_BROUILLON:
            new_actor.switch_state(SignatureState.INVITED)
        # Make sure the person has relevant role and group
        if person and group_name not in _get_roles_assigned_to_user(person.user):
            model.objects.update_or_create(person=person)
        return signataire_id

    @classmethod
    def remove_member(cls, groupe_id: 'GroupeDeSupervisionIdentity', signataire: 'SignataireIdentity') -> None:
        SupervisionActor.objects.filter(process__uuid=groupe_id.uuid, uuid=signataire.uuid).delete()

    @classmethod
    def get_members(cls, groupe_id: 'GroupeDeSupervisionIdentity') -> List[Union['PromoteurDTO', 'MembreCADTO']]:
        actors = SupervisionActor.objects.select_related('person__tutor').filter(
            process__uuid=groupe_id.uuid,
        )
        members = []
        for actor in actors:
            klass = PromoteurDTO if actor.type == ActorType.PROMOTER.name else MembreCADTO
            members.append(
                klass(
                    uuid=actor.uuid,
                    matricule=actor.person and actor.person.global_id,
                    nom=actor.last_name,
                    prenom=actor.first_name,
                    email=actor.email,
                    est_docteur=True if not actor.is_external and hasattr(actor.person, 'tutor') else actor.is_doctor,
                    institution=_('ucl') if not actor.is_external else actor.institute,
                    ville=actor.city,
                    pays=actor.country_id
                    and getattr(actor.country, 'name_en' if get_language() == 'en' else 'name')
                    or '',
                    est_externe=actor.is_external,
                )
            )
        return members

    @classmethod
    def edit_external_member(
        cls,
        groupe_id: 'GroupeDeSupervisionIdentity',
        membre_id: 'SignataireIdentity',
        first_name: Optional[str] = '',
        last_name: Optional[str] = '',
        email: Optional[str] = '',
        is_doctor: Optional[bool] = False,
        institute: Optional[str] = '',
        city: Optional[str] = '',
        country_code: Optional[str] = '',
        language: Optional[str] = '',
    ) -> None:
        SupervisionActor.objects.filter(process__uuid=groupe_id.uuid, uuid=membre_id.uuid).update(
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_doctor=is_doctor,
            institute=institute,
            city=city,
            country=Country.objects.get(iso_code=country_code) if country_code else None,
            language=language,
        )
