# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
from typing import Optional, List, Dict

from django.conf import settings
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.utils.translation import get_language

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    BourseRecherche,
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_lister_demandes import IListerDemandesService
from admission.ddd.admission.doctorat.preparation.dtos.liste import DemandeRechercheDTO
from admission.infrastructure.utils import get_entities_with_descendants_ids
from admission.models import DoctorateAdmission
from admission.views import PaginatedList


class ListerDemandesService(IListerDemandesService):
    @classmethod
    def lister(
        cls,
        annee_academique: Optional[int] = None,
        numero: Optional[int] = None,
        matricule_candidat: Optional[str] = '',
        nationalite: Optional[str] = '',
        etats: Optional[List[str]] = None,
        type: Optional[str] = '',
        cdds: Optional[List[str]] = None,
        commission_proximite: Optional[str] = '',
        sigles_formations: Optional[List[str]] = None,
        matricule_promoteur: Optional[str] = '',
        type_financement: Optional[str] = '',
        bourse_recherche: Optional[str] = '',
        cotutelle: Optional[bool] = None,
        date_soumission_debut: Optional[datetime.datetime] = None,
        date_soumission_fin: Optional[datetime.datetime] = None,
        mode_filtres_etats_checklist: Optional[str] = '',
        filtres_etats_checklist: Optional[Dict[str, List[str]]] = None,
        demandeur: Optional[str] = '',
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
    ) -> PaginatedList[DemandeRechercheDTO]:
        current_language = get_language() or settings.LANGUAGE_CODE

        qs = (
            DoctorateAdmission.objects.select_related(
                "training__academic_year",
                "candidate__country_of_citizenship",
                "determined_academic_year",
                "last_update_author",
            )
            .annotate_training_management_entity()
            .annotate_with_reference(with_management_faculty=False)
            .annotate(
                scholarship=Coalesce('international_scholarship__short_name', 'other_international_scholarship'),
            )
        )

        # Add filters
        if annee_academique:
            qs = qs.filter(
                Q(determined_academic_year__year=annee_academique)
                | Q(determined_academic_year__isnull=True, training__academic_year__year=annee_academique)
            )

        if numero:
            qs = qs.filter(reference=numero)

        if matricule_candidat:
            qs = qs.filter(candidate__global_id=matricule_candidat)

        if nationalite:
            qs = qs.filter(candidate__country_of_citizenship__iso_code=nationalite)

        if etats:
            qs = qs.filter(status__in=etats)

        if type:
            qs = qs.filter(type=type)

        if cdds:
            related_entities = get_entities_with_descendants_ids(cdds)
            qs = qs.filter(training__management_entity_id__in=related_entities)

        if commission_proximite:
            qs = qs.filter(proximity_commission=commission_proximite)

        if sigles_formations:
            qs = qs.filter(training__acronym__in=sigles_formations)

        if matricule_promoteur:
            qs = qs.filter(supervision_group__actors__person__global_id=matricule_promoteur)

        if type_financement:
            qs = qs.filter(financing_type=type_financement)

        if bourse_recherche:
            if bourse_recherche == BourseRecherche.OTHER.name:
                qs = qs.exclude(other_international_scholarship='')
            else:
                qs = qs.filter(international_scholarship_id=bourse_recherche)

        if cotutelle is not None:
            qs = qs.filter(cotutelle=cotutelle)

        if date_soumission_debut:
            qs = qs.filter(submitted_at__gte=date_soumission_debut)

        if date_soumission_fin:
            qs = qs.filter(submitted_at__lte=date_soumission_fin)

        if demandeur:
            qs = qs.filter_according_to_roles(demandeur, permission='admission.view_doctorate_enrolment_applications')

        country_title = {
            settings.LANGUAGE_CODE_FR: 'name',
            settings.LANGUAGE_CODE_EN: 'name_en',
        }[current_language]

        field_order = []
        if champ_tri:
            if champ_tri == 'etat_demande':
                qs = qs.annotate_ordered_enum('status', 'ordered_status', ChoixStatutPropositionDoctorale)

            field_order = {
                'numero_demande': ['formatted_reference'],
                'nom_candidat': ['candidate__last_name', 'candidate__first_name'],
                'nationalite': [f'candidate__country_of_citizenship__{country_title}'],
                'code_bourse': ['scholarship'],
                'formation': ['training__acronym'],
                'etat_demande': ['ordered_status'],
                'fac_decision': [],
                'sic_decision': [],
                'date_confirmation': ['submitted_at'],
                'derniere_modification': ['modified_at'],
                'derniere_modification_par': ['last_update_author__last_name', 'last_update_author__first_name'],
                'pre_admission': ['type'],
                'cotutelle': ['cotutelle'],
            }[champ_tri]

            if tri_inverse:
                field_order = ['-' + field for field in field_order]

        qs = qs.order_by(*field_order, 'id')

        result = PaginatedList()

        if page and taille_page:
            result.total_count = qs.count()
            bottom = (page - 1) * taille_page
            top = page * taille_page
            qs = qs[bottom:top]
        else:
            result.total_count = len(qs)

        for admission in qs:
            result.append(cls.load_dto_from_model(admission, current_language))

        return result

    @classmethod
    def load_dto_from_model(cls, admission: DoctorateAdmission, current_language: str) -> 'DemandeRechercheDTO':
        country_title = {
            settings.LANGUAGE_CODE_FR: 'name',
            settings.LANGUAGE_CODE_EN: 'name_en',
        }[current_language]

        training_title = {
            settings.LANGUAGE_CODE_FR: 'title',
            settings.LANGUAGE_CODE_EN: 'title_english',
        }[current_language]

        country_data = (
            {
                'code_pays_nationalite_candidat': admission.candidate.country_of_citizenship.iso_code,
                'nom_pays_nationalite_candidat': getattr(admission.candidate.country_of_citizenship, country_title),
            }
            if admission.candidate.country_of_citizenship
            else {}
        )

        last_author_data = (
            {
                'prenom_auteur_derniere_modification': admission.last_update_author.first_name,
                'nom_auteur_derniere_modification': admission.last_update_author.last_name,
            }
            if admission.last_update_author_id
            else {}
        )

        return DemandeRechercheDTO(
            uuid=admission.uuid,
            numero_demande=admission.formatted_reference,  # From annotation
            etat_demande=admission.status,
            nom_candidat=admission.candidate.last_name,
            prenom_candidat=admission.candidate.first_name,
            sigle_formation=admission.training.acronym,
            code_formation=admission.training.partial_acronym,
            intitule_formation=getattr(admission.training, training_title),
            decision_fac='TODO',  # TODO
            decision_sic='TODO',  # TODO
            date_confirmation=admission.submitted_at,
            derniere_modification_le=admission.modified_at,
            type_admission=admission.type,
            cotutelle=admission.cotutelle,
            code_bourse=admission.scholarship if admission.scholarship else '',  # From annotation
            **country_data,
            **last_author_data,
        )
