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
import datetime
from typing import List, Optional

from django.conf import settings
from django.db.models import (
    BooleanField,
    Case,
    ExpressionWrapper,
    F,
    IntegerField,
    Prefetch,
    Q,
    Value,
    When,
)
from django.db.models.functions import Coalesce, NullIf
from django.utils.translation import get_language

from admission.contrib.models import AdmissionViewer
from admission.contrib.models.base import BaseAdmission, BaseAdmissionProxy
from admission.ddd.admission.domain.service.i_filtrer_toutes_demandes import IListerToutesDemandes
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO, VisualiseurAdmissionDTO
from admission.ddd.admission.enums.statut import CHOIX_STATUT_TOUTE_PROPOSITION
from admission.views import PaginatedList


class ListerToutesDemandes(IListerToutesDemandes):
    @classmethod
    def filtrer(
        cls,
        annee_academique: Optional[int] = None,
        numero: Optional[int] = None,
        noma: Optional[str] = '',
        matricule_candidat: Optional[str] = '',
        etat: Optional[str] = '',
        type: Optional[str] = '',
        site_inscription: Optional[str] = '',
        entites: Optional[List[str]] = None,
        types_formation: Optional[List[str]] = None,
        formation: Optional[str] = '',
        bourse_internationale: Optional[str] = '',
        bourse_erasmus_mundus: Optional[str] = '',
        bourse_double_diplomation: Optional[str] = '',
        demandeur: Optional[str] = '',
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
    ) -> PaginatedList[DemandeRechercheDTO]:
        language_is_french = get_language() == settings.LANGUAGE_CODE_FR

        prefetch_viewers_queryset = (
            AdmissionViewer.objects.filter(viewed_at__gte=datetime.datetime.now() - datetime.timedelta(days=1))
            .select_related('person')
            .order_by('-viewed_at')
        )

        roles = []
        if demandeur:
            prefetch_viewers_queryset = prefetch_viewers_queryset.exclude(person__uuid=demandeur)

        qs = (
            BaseAdmissionProxy.objects.with_training_management_and_reference()
            .annotate_other_admissions_in_progress()
            .annotate(
                status=Coalesce(
                    NullIf(F('continuingeducationadmission__status'), Value('')),
                    NullIf(F('doctorateadmission__status'), Value('')),
                    NullIf(F('generaleducationadmission__status'), Value('')),
                ),
                is_vip=ExpressionWrapper(
                    Q(doctorateadmission__international_scholarship_id__isnull=False)
                    | Q(doctorateadmission__erasmus_mundus_scholarship_id__isnull=False)
                    | Q(generaleducationadmission__international_scholarship_id__isnull=False)
                    | Q(generaleducationadmission__erasmus_mundus_scholarship_id__isnull=False)
                    | Q(generaleducationadmission__double_degree_scholarship_id__isnull=False),
                    output_field=BooleanField(),
                ),
            )
            .select_related(
                'candidate__country_of_citizenship',
                'last_update_author__user',
                'training__academic_year',
                'training__enrollment_campus',
                'training__education_group_type',
            )
            .prefetch_related(
                Prefetch(
                    'admissionviewer_set',
                    prefetch_viewers_queryset,
                    to_attr='other_admission_viewers',
                ),
            )
        )

        # Add filters
        if annee_academique:
            qs = qs.filter(determined_academic_year__year=annee_academique)
        if numero:
            qs = qs.filter(reference=numero)
        if noma:
            qs = qs.filter(candidate__student__registration_id=noma)
        if matricule_candidat:
            qs = qs.filter(candidate__global_id=matricule_candidat)
        if type:
            qs = qs.filter(type_demande=type)
        if site_inscription:
            qs = qs.filter(training__enrollment_campus__uuid=site_inscription)
        if entites:
            qs = qs.filter(Q(sigle_entite_gestion__in=entites) | Q(training_management_faculty__in=entites))
        if demandeur:
            qs = qs.filter_according_to_roles(demandeur)
        if types_formation:
            qs = qs.filter(training__education_group_type__name__in=types_formation)
        if formation:
            terms = formation.split()
            training_filters = Q()
            for term in terms:
                # The term can be a part of the acronym or of the training title
                training_filters &= Q(Q(training__acronym__icontains=term) | Q(training__title__icontains=term))
            qs = qs.filter(training_filters)
        if etat:
            qs = qs.filter(status=etat)
        else:
            qs = qs.exclude(Q(status__in=cls.STATUTS_A_FILTRER_PAR_DEFAUT))
        if bourse_internationale:
            qs = qs.filter(
                Q(doctorateadmission__international_scholarship_id=bourse_internationale)
                | Q(generaleducationadmission__international_scholarship_id=bourse_internationale),
            )
        if bourse_erasmus_mundus:
            qs = qs.filter(
                Q(doctorateadmission__erasmus_mundus_scholarship_id=bourse_erasmus_mundus)
                | Q(generaleducationadmission__erasmus_mundus_scholarship_id=bourse_erasmus_mundus),
            )
        if bourse_double_diplomation:
            qs = qs.filter(generaleducationadmission__double_degree_scholarship_id=bourse_double_diplomation)

        field_order = []
        if champ_tri:
            if champ_tri == 'type_demande':
                qs = qs.annotate(
                    ordered_status=Case(
                        *(When(status=member[0], then=i) for i, member in enumerate(CHOIX_STATUT_TOUTE_PROPOSITION)),
                        output_field=IntegerField(),
                    )
                )

            field_order = {
                'numero_demande': ['formatted_reference'],
                'nom_candidat': ['candidate__last_name', 'candidate__first_name'],
                'formation': ['training__acronym'],
                'nationalite_candidat': [
                    'candidate__country_of_citizenship__{}'.format('name' if language_is_french else 'name_en')
                ],
                'vip': ['is_vip'],
                'type_demande': ['ordered_status'],
                'derniere_modification_le': ['modified_at'],
                'derniere_modification_par': ['last_update_author__user__username'],
                'date_confirmation': ['submitted_at'],
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
            result.append(cls.load_dto_from_model(admission, language_is_french))

        return result

    @classmethod
    def load_dto_from_model(cls, admission: BaseAdmission, language_is_french: bool) -> DemandeRechercheDTO:
        return DemandeRechercheDTO(
            uuid=admission.uuid,
            numero_demande=admission.formatted_reference,  # From annotation
            nom_candidat=admission.candidate.last_name,
            prenom_candidat=admission.candidate.first_name,
            noma_candidat=admission.candidate.last_registration_id,
            plusieurs_demandes=admission.has_other_admission_in_progress,  # From annotation
            sigle_formation=admission.training.acronym,
            code_formation=admission.training.partial_acronym,
            intitule_formation=getattr(admission.training, 'title' if language_is_french else 'title_english'),
            type_formation=admission.training.education_group_type.name,
            lieu_formation=admission.teaching_campus,
            nationalite_candidat=getattr(
                admission.candidate.country_of_citizenship,
                'name' if language_is_french else 'name_en',
            )
            if admission.candidate.country_of_citizenship
            else '',
            nationalite_ue_candidat=admission.candidate.country_of_citizenship
            and admission.candidate.country_of_citizenship.european_union,
            vip=admission.is_vip,
            etat_demande=admission.status,  # From annotation
            type_demande=admission.type_demande,
            derniere_modification_le=admission.modified_at,
            derniere_modification_par=admission.last_update_author.user.username
            if admission.last_update_author_id
            else '',
            derniere_modification_par_candidat=admission.candidate_id == admission.last_update_author_id,
            dernieres_vues_par=[
                VisualiseurAdmissionDTO(
                    nom=viewer.person.last_name,
                    prenom=viewer.person.first_name,
                    date=viewer.viewed_at,
                )
                for viewer in admission.other_admission_viewers
            ],
            date_confirmation=admission.submitted_at,
        )
