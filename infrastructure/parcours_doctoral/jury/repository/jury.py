# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional, List

from django.db import transaction
from django.db.models import Prefetch, Q

from admission.contrib.models import DoctorateAdmission, JuryMember, SupervisionActor
from admission.contrib.models.enums.actor_type import ActorType
from admission.ddd.parcours_doctoral.jury.domain.model.enums import RoleJury
from admission.ddd.parcours_doctoral.jury.domain.model.jury import Jury, JuryIdentity, MembreJury
from admission.ddd.parcours_doctoral.jury.dtos.jury import JuryDTO, MembreJuryDTO
from admission.ddd.parcours_doctoral.jury.repository.i_jury import IJuryRepository
from admission.ddd.parcours_doctoral.jury.validator.exceptions import (
    JuryNonTrouveException,
    MembreNonTrouveDansJuryException,
)
from base.models.person import Person
from osis_common.ddd.interface import EntityIdentity, ApplicationService, RootEntity
from reference.models.country import Country

INSTITUTION_UCL = "UCLouvain"


class JuryRepository(IJuryRepository):
    @classmethod
    def delete(cls, entity_id: EntityIdentity, **kwargs: ApplicationService) -> None:
        raise NotImplementedError

    @classmethod
    def search(cls, entity_ids: Optional[List[EntityIdentity]] = None, **kwargs) -> List[RootEntity]:
        raise NotImplementedError

    @classmethod
    def _get_queryset(cls):
        return DoctorateAdmission.objects.only(
            "uuid",
            "thesis_language",
            "thesis_proposed_title",
            "defense_method",
            "defense_indicative_date",
            "defense_language",
            "comment_about_jury",
            "accounting_situation",
            "jury_approval",
        ).prefetch_related(
            Prefetch(
                'jury_members',
                queryset=JuryMember.objects.select_related(
                    'promoter__country',
                    'promoter__person',
                    'person',
                    'country',
                ),
            )
        )

    @classmethod
    def _get(cls, entity_id: 'JuryIdentity') -> 'DoctorateAdmission':
        try:
            doctorate = cls._get_queryset().get(uuid=entity_id.uuid)
        except DoctorateAdmission.DoesNotExist:
            raise JuryNonTrouveException
        # Initialize promoters members if needed
        if not doctorate.jury_members.all():
            JuryMember.objects.bulk_create(
                [
                    JuryMember(
                        role=RoleJury.MEMBRE.name,
                        doctorate=doctorate,
                        promoter_id=promoter,
                    )
                    for promoter in doctorate.supervision_group.actors.filter(
                        supervisionactor__type=ActorType.PROMOTER.name
                    ).values_list('pk', flat=True)
                ]
            )
            # reload with members
            doctorate = cls._get_queryset().get(uuid=entity_id.uuid)
        return doctorate

    @classmethod
    def get_dto(cls, entity_id: 'JuryIdentity') -> 'JuryDTO':
        return cls._load_jury_dto(cls._get(entity_id))

    @classmethod
    def get_membre_dto(cls, entity_id: 'JuryIdentity', membre_uuid: str) -> MembreJuryDTO:
        jury = cls.get_dto(entity_id)
        for membre in jury.membres:
            if str(membre.uuid) == membre_uuid:
                return membre
        raise MembreNonTrouveDansJuryException(jury=jury, uuid_membre=membre_uuid)

    @classmethod
    def get(cls, entity_id: 'JuryIdentity') -> 'Jury':
        return cls._load_jury(cls._get(entity_id))

    @classmethod
    @transaction.atomic
    def save(cls, entity: 'Jury') -> 'JuryIdentity':
        DoctorateAdmission.objects.filter(uuid=str(entity.entity_id.uuid)).update(
            thesis_proposed_title=entity.titre_propose,
            cotutelle=entity.cotutelle,
            cotutelle_institution=entity.institution_cotutelle if entity.institution_cotutelle else None,
            defense_method=entity.formule_defense,
            defense_indicative_date=entity.date_indicative,
            thesis_language=entity.langue_redaction,
            defense_language=entity.langue_soutenance,
            comment_about_jury=entity.commentaire,
            accounting_situation=entity.situation_comptable,
            jury_approval=entity.approbation_pdf,
        )

        if entity.membres is not None:
            doctorate = DoctorateAdmission.objects.get(uuid=entity.entity_id.uuid)
            for membre in entity.membres:
                if membre.est_promoteur:
                    promoter = SupervisionActor.objects.get(id=membre.matricule)
                    JuryMember.objects.update_or_create(
                        uuid=membre.uuid,
                        doctorate=doctorate,
                        defaults={
                            'role': membre.role,
                            'promoter': promoter,
                            'person': None,
                            'institute': '',
                            'other_institute': membre.autre_institution,
                            'country': None,
                            'last_name': '',
                            'first_name': '',
                            'title': '',
                            'non_doctor_reason': '',
                            'gender': '',
                            'email': '',
                        },
                    )
                elif membre.matricule:
                    person = Person.objects.get(global_id=membre.matricule)
                    JuryMember.objects.update_or_create(
                        uuid=membre.uuid,
                        doctorate=doctorate,
                        defaults={
                            'role': membre.role,
                            'promoter': None,
                            'person': person,
                            'institute': '',
                            'other_institute': membre.autre_institution,
                            'country': None,
                            'last_name': '',
                            'first_name': '',
                            'title': '',
                            'non_doctor_reason': '',
                            'gender': '',
                            'email': '',
                        },
                    )
                else:
                    country = Country.objects.filter(Q(iso_code=membre.pays) | Q(name=membre.pays)).first()
                    JuryMember.objects.update_or_create(
                        uuid=membre.uuid,
                        doctorate=doctorate,
                        defaults={
                            'role': membre.role,
                            'promoter': None,
                            'person': None,
                            'institute': membre.institution,
                            'other_institute': membre.autre_institution,
                            'country': country,
                            'last_name': membre.nom,
                            'first_name': membre.prenom,
                            'title': membre.titre,
                            'non_doctor_reason': membre.justification_non_docteur,
                            'gender': membre.genre,
                            'email': membre.email,
                        },
                    )
            doctorate.jury_members.exclude(uuid__in=[membre.uuid for membre in entity.membres]).delete()
        return entity.entity_id

    @classmethod
    def _load_jury_dto(cls, doctorate: DoctorateAdmission) -> JuryDTO:
        jury = cls._load_jury(doctorate)

        return JuryDTO(
            uuid=jury.entity_id.uuid,
            titre_propose=jury.titre_propose,
            cotutelle=jury.cotutelle,
            institution_cotutelle=jury.institution_cotutelle,
            membres=[
                MembreJuryDTO(
                    uuid=membre.uuid,
                    role=membre.role,
                    est_promoteur=membre.est_promoteur,
                    matricule=membre.matricule,
                    institution=membre.institution,
                    autre_institution=membre.autre_institution,
                    pays=membre.pays,
                    nom=membre.nom,
                    prenom=membre.prenom,
                    titre=membre.titre,
                    justification_non_docteur=membre.justification_non_docteur,
                    genre=membre.genre,
                    email=membre.email,
                )
                for membre in jury.membres
            ],
            formule_defense=jury.formule_defense,
            date_indicative=jury.date_indicative,
            langue_redaction=jury.langue_redaction,
            langue_soutenance=jury.langue_soutenance,
            commentaire=jury.commentaire,
            situation_comptable=jury.situation_comptable,
            approbation_pdf=jury.approbation_pdf,
        )

    @classmethod
    def _load_jury(
        cls,
        doctorate: 'DoctorateAdmission',
    ) -> Jury:
        def _get_membrejury_from_model(membre: JuryMember) -> MembreJury:
            if membre.promoter is not None:
                if membre.promoter.person is not None:
                    return MembreJury(
                        uuid=str(membre.uuid),
                        role=membre.role,
                        est_promoteur=True,
                        matricule=str(membre.promoter.id),
                        institution=INSTITUTION_UCL,
                        autre_institution=membre.other_institute,
                        pays=str(membre.promoter.person.country_of_citizenship)
                        if membre.promoter.person.country_of_citizenship
                        else '',
                        nom=membre.promoter.person.last_name,
                        prenom=membre.promoter.person.first_name,
                        titre='',
                        justification_non_docteur='',
                        genre=membre.promoter.person.gender,
                        email=membre.promoter.person.email,
                    )
                else:
                    return MembreJury(
                        uuid=str(membre.uuid),
                        role=membre.role,
                        est_promoteur=True,
                        matricule=str(membre.promoter.id),
                        institution=membre.promoter.institute,
                        autre_institution=membre.other_institute,
                        pays=str(membre.promoter.country),
                        nom=membre.promoter.last_name,
                        prenom=membre.promoter.first_name,
                        titre='',
                        justification_non_docteur='',
                        genre='',
                        email=membre.promoter.email,
                    )
            elif membre.person is not None:
                return MembreJury(
                    uuid=str(membre.uuid),
                    role=membre.role,
                    est_promoteur=False,
                    matricule=membre.person.global_id,
                    institution=INSTITUTION_UCL,
                    autre_institution=membre.other_institute,
                    pays=str(membre.person.country_of_citizenship) if membre.person.country_of_citizenship else '',
                    nom=membre.person.last_name,
                    prenom=membre.person.first_name,
                    titre='',
                    justification_non_docteur='',
                    genre=membre.person.gender,
                    email=membre.person.email,
                )
            else:
                return MembreJury(
                    uuid=str(membre.uuid),
                    role=membre.role,
                    est_promoteur=False,
                    matricule='',
                    institution=membre.institute,
                    autre_institution=membre.other_institute,
                    pays=str(membre.country),
                    nom=membre.last_name,
                    prenom=membre.first_name,
                    titre=membre.title,
                    justification_non_docteur=membre.non_doctor_reason,
                    genre=membre.gender,
                    email=membre.email,
                )

        return Jury(
            entity_id=JuryIdentity(uuid=str(doctorate.uuid)),
            titre_propose=doctorate.thesis_proposed_title,
            cotutelle=doctorate.cotutelle,
            institution_cotutelle=doctorate.cotutelle_institution if doctorate.cotutelle_institution else '',
            formule_defense=doctorate.defense_method,
            date_indicative=doctorate.defense_indicative_date,
            langue_redaction=doctorate.thesis_language,
            langue_soutenance=doctorate.defense_language,
            commentaire=doctorate.comment_about_jury,
            situation_comptable=doctorate.accounting_situation,
            approbation_pdf=doctorate.jury_approval,
            membres=[_get_membrejury_from_model(membre) for membre in doctorate.jury_members.all()],
        )
