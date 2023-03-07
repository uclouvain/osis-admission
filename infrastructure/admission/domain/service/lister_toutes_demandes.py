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

from django.conf import settings
from django.db.models import Q, F, Value, Exists, ExpressionWrapper, BooleanField, OuterRef
from django.db.models.functions import Coalesce, NullIf
from django.utils.translation import get_language

from admission.contrib.models.base import BaseAdmission, BaseAdmissionProxy
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    STATUTS_PROPOSITION_AVANT_SOUMISSION,
)
from admission.ddd.admission.domain.service.i_filtrer_toutes_demandes import IListerToutesDemandes
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale


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
    ) -> List[DemandeRechercheDTO]:
        qs = (
            BaseAdmissionProxy.objects.with_training_management_and_reference()
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
                has_other_admission_in_progress=Exists(
                    BaseAdmission.objects.filter(candidate_id=OuterRef('candidate_id'))
                    .filter(
                        Q(generaleducationadmission__status=ChoixStatutPropositionGenerale.EN_BROUILLON.name)
                        | Q(continuingeducationadmission__status=ChoixStatutPropositionContinue.EN_BROUILLON.name)
                        | Q(doctorateadmission__status__in=STATUTS_PROPOSITION_AVANT_SOUMISSION),
                    )
                    .exclude(pk=OuterRef('pk')),
                ),
            )
            .select_related(
                'candidate__country_of_citizenship',
                'training__academic_year',
                'training__enrollment_campus',
                'training__education_group_type',
            )
        )
        # Add filters
        if annee_academique:
            qs = qs.filter(training__academic_year__year=annee_academique)
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
        if types_formation:
            qs = qs.filter(training__education_group_type__name__in=types_formation)
        if formation:
            terms = formation.split()
            training_filters = Q()
            for term in terms:
                # The term can be a part of the acronym or of the training title
                training_filters &= Q(Q(training__acronym__contains=term) | Q(training__title__contains=term))
            qs = qs.filter(training_filters)
        if etat:
            qs = qs.filter(generaleducationadmission__status=etat)
        else:
            qs = qs.exclude(Q(status__in=cls.DEFAULT_STATUSES_TO_FILTER))
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

        result = qs.all()
        return [cls.load_dto_from_model(admission) for admission in result]

    @classmethod
    def load_dto_from_model(cls, admission: BaseAdmission) -> DemandeRechercheDTO:
        default_language = get_language() == settings.LANGUAGE_CODE
        return DemandeRechercheDTO(
            uuid=admission.uuid,
            numero_demande=admission.formatted_reference,  # From annotation
            nom_candidat=admission.candidate.last_name,
            prenom_candidat=admission.candidate.first_name,
            noma_candidat=admission.candidate.last_registration_id,
            plusieurs_demandes=admission.has_other_admission_in_progress,  # From annotation
            sigle_formation=admission.training.acronym,
            sigle_partiel_formation=admission.training.partial_acronym,
            intitule_formation=getattr(admission.training, 'title' if default_language else 'title_english'),
            type_formation=admission.training.education_group_type.name,
            lieu_formation=admission.teaching_campus,
            nationalite_candidat=getattr(
                admission.candidate.country_of_citizenship, 'name' if default_language else 'name_en'
            )
            if admission.candidate.country_of_citizenship
            else '',
            nationalite_ue_candidat=admission.candidate.country_of_citizenship
            and admission.candidate.country_of_citizenship.european_union,
            vip=admission.is_vip,
            etat_demande=admission.status,  # From annotation
            type_demande=admission.type_demande,
            derniere_modification_le=admission.modified_at,
            derniere_modification_par='',  # TODO
            derniere_modification_par_candidat=False,  # TODO
            derniere_vue_par='',  # TODO
            date_confirmation=admission.submitted_at,
        )
