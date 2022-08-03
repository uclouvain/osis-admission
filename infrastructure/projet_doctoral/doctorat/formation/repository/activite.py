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
from typing import List, Mapping, Optional

from admission.contrib.models.doctoral_training import Activity
from admission.ddd.projet_doctoral.doctorat.builder.doctorat_identity import DoctoratIdentityBuilder
from admission.ddd.projet_doctoral.doctorat.formation.builder.activite_identity_builder import ActiviteIdentityBuilder
from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import (
    CategorieActivite,
    ChoixStatutPublication,
    ChoixTypeEpreuve,
    StatutActivite,
)
from admission.ddd.projet_doctoral.doctorat.formation.domain.model.activite import Activite, ActiviteIdentity
from admission.ddd.projet_doctoral.doctorat.formation.domain.validator.exceptions import ActiviteNonTrouvee
from admission.ddd.projet_doctoral.doctorat.formation.dtos import *
from admission.ddd.projet_doctoral.doctorat.formation.repository.i_activite import IActiviteRepository


class ActiviteRepository(IActiviteRepository):
    @classmethod
    def get(cls, entity_id: 'ActiviteIdentity') -> 'Activite':
        activity = Activity.objects.select_related('doctorate', 'parent').get(uuid=entity_id.uuid)
        return cls._get(activity, entity_id)

    @classmethod
    def get_multiple(cls, entity_ids: List['ActiviteIdentity']) -> Mapping['ActiviteIdentity', 'Activite']:
        ret = {}
        for activity in cls._get_queryset(entity_ids):
            entity_id = ActiviteIdentityBuilder.build_from_uuid(activity.uuid)
            ret[entity_id] = cls._get(activity, entity_id)
        if len(entity_ids) != len(ret):  # pragma: no cover
            raise ActiviteNonTrouvee
        return ret

    @classmethod
    def get_dto(cls, entity_id: 'ActiviteIdentity') -> ActiviteDTO:
        activity = Activity.objects.select_related('doctorate', 'parent').get(uuid=entity_id.uuid)
        return cls._get_dto(activity)

    @classmethod
    def get_dtos(cls, entity_ids: List['ActiviteIdentity']) -> Mapping['ActiviteIdentity', ActiviteDTO]:
        ret = {}
        for activity in cls._get_queryset(entity_ids):
            entity_id = ActiviteIdentityBuilder.build_from_uuid(activity.uuid)
            ret[entity_id] = cls._get_dto(activity)
        if len(entity_ids) != len(ret):  # pragma: no cover
            raise ActiviteNonTrouvee
        return ret

    @classmethod
    def _get_queryset(cls, entity_ids):
        return Activity.objects.select_related('doctorate', 'parent').filter(
            uuid__in=[entity_id.uuid for entity_id in entity_ids]
        )

    @classmethod
    def _get(cls, activity, entity_id=None):
        return Activite(
            entity_id=entity_id or ActiviteIdentityBuilder.build_from_uuid(activity.uuid),
            doctorat_id=DoctoratIdentityBuilder.build_from_uuid(activity.doctorate.uuid),
            ects=activity.ects,
            categorie=CategorieActivite[activity.category],
            statut=StatutActivite[activity.status],
            parent_id=ActiviteIdentityBuilder.build_from_uuid(activity.parent.uuid) if activity.parent_id else None,
            categorie_parente=CategorieActivite[activity.parent.category] if activity.parent_id else None,
        )

    @classmethod
    def _get_dto(cls, activity: Activity) -> ActiviteDTO:
        categorie = CategorieActivite[activity.category]
        categorie_parente = CategorieActivite[activity.parent.category] if activity.parent_id else None
        if categorie_parente == CategorieActivite.CONFERENCE and categorie == CategorieActivite.COMMUNICATION:
            return ConferenceCommunicationDTO(
                type=activity.type,
                titre=activity.title,
                comite_selection=activity.committee,
                reference_dial=activity.dial_reference,
                preuve_acceptation=activity.acceptation_proof,
                resume=activity.summary,
                attestation_communication=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie_parente == CategorieActivite.CONFERENCE and categorie == CategorieActivite.PUBLICATION:
            return ConferencePublicationDTO(
                type=activity.type,
                intitule=activity.title,
                auteurs=activity.authors,
                role=activity.role,
                nom_revue_maison_edition=activity.journal,
                preuve_acceptation=activity.acceptation_proof,
                comite_selection=activity.committee,
                mots_cles=activity.keywords,
                resume=activity.summary,
                reference_dial=activity.dial_reference,
                commentaire=activity.comment,
            )
        elif categorie_parente == CategorieActivite.SEMINAR and categorie == CategorieActivite.COMMUNICATION:
            return SeminaireCommunicationDTO(
                date=activity.start_date,
                en_ligne=activity.is_online,
                pays=activity.country.iso_code if activity.country else None,
                ville=activity.city,
                institution_organisatrice=activity.organizing_institution,
                site_web=activity.website,
                titre_communication=activity.title,
                orateur_oratrice=activity.authors,
                commentaire=activity.comment,
                attestation_participation=activity.participating_proof,
            )
        elif categorie_parente == CategorieActivite.RESIDENCY and categorie == CategorieActivite.COMMUNICATION:
            return SejourCommunicationDTO(
                type_activite=activity.type,
                type_communication=activity.subtype,
                nom=activity.title,
                date=activity.start_date,
                en_ligne=activity.is_online,
                institution_organisatrice=activity.organizing_institution,
                site_web=activity.website,
                titre_communication=activity.subtitle,
                resume=activity.summary,
                attestation_communication=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.CONFERENCE:
            return ConferenceDTO(
                type=activity.type,
                nom_manifestation=activity.title,
                date_debut=activity.start_date,
                date_fin=activity.end_date,
                nombre_jours=activity.participating_days and float(activity.participating_days),
                en_ligne=activity.is_online,
                pays=activity.country.iso_code if activity.country else None,
                ville=activity.city,
                institution_organisatrice=activity.organizing_institution,
                commentaire=activity.comment,
                site_web=activity.website,
                certificat_participation=activity.participating_proof,
            )
        elif categorie == CategorieActivite.COMMUNICATION:
            return CommunicationDTO(
                type_activite=activity.type,
                type_communication=activity.subtype,
                nom=activity.title,
                date=activity.start_date,
                en_ligne=activity.is_online,
                pays=activity.country.iso_code if activity.country else None,
                ville=activity.city,
                institution_organisatrice=activity.organizing_institution,
                site_web=activity.website,
                titre=activity.subtitle,
                comite_selection=activity.committee,
                reference_dial=activity.dial_reference,
                preuve_acceptation=activity.acceptation_proof,
                resume=activity.summary,
                attestation_communication=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.PUBLICATION:
            return PublicationDTO(
                type=activity.type,
                intitule=activity.title,
                date=activity.start_date,
                auteurs=activity.authors,
                role=activity.role,
                nom_revue_maison_edition=activity.journal,
                preuve_acceptation=activity.acceptation_proof,
                statut_publication=activity.publication_status and ChoixStatutPublication[activity.publication_status],
                mots_cles=activity.keywords,
                resume=activity.summary,
                reference_dial=activity.dial_reference,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.SEMINAR:
            return SeminaireDTO(
                type=activity.type,
                nom=activity.title,
                date_debut=activity.start_date,
                date_fin=activity.end_date,
                volume_horaire=activity.hour_volume,
                attestation_participation=activity.participating_proof,
            )
        elif categorie == CategorieActivite.RESIDENCY:
            return SejourDTO(
                type=activity.type,
                description=activity.subtitle,
                date_debut=activity.start_date,
                date_fin=activity.end_date,
                pays=activity.country.iso_code if activity.country else None,
                ville=activity.city,
                preuve=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.SERVICE:
            return ServiceDTO(
                type=activity.type,
                nom=activity.title,
                date_debut=activity.start_date,
                date_fin=activity.end_date,
                institution=activity.organizing_institution,
                volume_horaire=activity.hour_volume,
                preuve=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.VAE:
            return ValorisationDTO(
                intitule=activity.title,
                description=activity.subtitle,
                preuve=activity.participating_proof,
                cv=activity.summary,
            )
        elif categorie == CategorieActivite.COURSE:
            return CoursDTO(
                type=activity.type,
                nom=activity.title,
                code=activity.subtitle,
                institution=activity.organizing_institution,
                date_debut=activity.start_date,
                date_fin=activity.end_date,
                volume_horaire=activity.hour_volume,
                titulaire=activity.authors,
                certificat=activity.participating_proof,
                commentaire=activity.comment,
            )
        elif categorie == CategorieActivite.PAPER:  # pragma: no branch
            return EpreuveDTO(
                type=activity.type and ChoixTypeEpreuve[activity.type],
                commentaire=activity.comment,
            )

    @classmethod
    def delete(cls, entity_id: 'ActiviteIdentity', **kwargs) -> None:
        Activity.objects.get(uuid=entity_id.uuid).delete()

    @classmethod
    def save(cls, activite: 'Activite') -> None:
        # The only thing that can be modified is status, for now
        Activity.objects.filter(uuid=activite.entity_id.uuid).update(status=activite.statut.name)

    @classmethod
    def search(cls, parent_id: Optional[ActiviteIdentity] = None, **kwargs) -> List[Activite]:
        qs = Activity.objects.select_related('doctorate').filter(parent__uuid=parent_id.uuid)
        return [cls._get(activity) for activity in qs]
