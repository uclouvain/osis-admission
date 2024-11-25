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
from collections import defaultdict
from typing import List, Optional, Dict, Set

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
    Exists,
    OuterRef,
)
from django.db.models.functions import Coalesce, NullIf
from django.utils.translation import get_language

from admission.ddd.admission.domain.service.i_filtrer_toutes_demandes import IListerToutesDemandes
from admission.ddd.admission.dtos.liste import DemandeRechercheDTO, VisualiseurAdmissionDTO
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.enums.liste import TardiveModificationReorientationFiltre
from admission.ddd.admission.enums.statut import CHOIX_STATUT_TOUTE_PROPOSITION
from admission.ddd.admission.formation_generale.domain.model.enums import (
    PoursuiteDeCycle,
    OngletsChecklist,
)
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
    ConfigurationStatutChecklist,
)
from admission.infrastructure.utils import get_entities_with_descendants_ids
from admission.models import AdmissionViewer
from admission.models.base import BaseAdmission
from admission.models.epc_injection import EPCInjectionType, EPCInjectionStatus
from admission.views import PaginatedList
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from osis_profile import BE_ISO_CODE
from osis_profile.models import EducationalExperienceYear
from osis_profile.models.enums.curriculum import Result


class ListerToutesDemandes(IListerToutesDemandes):
    @classmethod
    def filtrer(
        cls,
        annee_academique: Optional[int] = None,
        numero: Optional[int] = None,
        noma: Optional[str] = '',
        matricule_candidat: Optional[str] = '',
        etats: Optional[List[str]] = None,
        type: Optional[str] = '',
        site_inscription: Optional[str] = '',
        entites: Optional[List[str]] = None,
        types_formation: Optional[List[str]] = None,
        formation: Optional[str] = '',
        bourse_internationale: Optional[str] = '',
        bourse_erasmus_mundus: Optional[str] = '',
        bourse_double_diplomation: Optional[str] = '',
        quarantaine: Optional[bool] = None,
        demandeur: Optional[str] = '',
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
        mode_filtres_etats_checklist: Optional[str] = '',
        filtres_etats_checklist: Optional[Dict[str, List[str]]] = '',
        tardif_modif_reorientation: Optional[str] = '',
    ) -> PaginatedList[DemandeRechercheDTO]:
        language_is_french = get_language() == settings.LANGUAGE_CODE_FR

        prefetch_viewers_queryset = (
            AdmissionViewer.objects.filter(viewed_at__gte=datetime.datetime.now() - datetime.timedelta(hours=1))
            .select_related('person')
            .order_by('-viewed_at')
        )

        if demandeur:
            prefetch_viewers_queryset = prefetch_viewers_queryset.exclude(person__uuid=demandeur)

        qs = (
            BaseAdmission.objects.with_training_management_and_reference()
            .annotate_several_admissions_in_progress()
            .annotate(
                status=Coalesce(
                    NullIf(F('continuingeducationadmission__status'), Value('')),
                    NullIf(F('doctorateadmission__status'), Value('')),
                    NullIf(F('generaleducationadmission__status'), Value('')),
                ),
                is_vip=ExpressionWrapper(
                    Q(doctorateadmission__international_scholarship_id__isnull=False)
                    | Q(generaleducationadmission__international_scholarship_id__isnull=False)
                    | Q(generaleducationadmission__erasmus_mundus_scholarship_id__isnull=False)
                    | Q(generaleducationadmission__double_degree_scholarship_id__isnull=False),
                    output_field=BooleanField(),
                ),
                est_premiere_annee=ExpressionWrapper(
                    Q(training__education_group_type__name=TrainingType.BACHELOR.name)
                    & ~Q(generaleducationadmission__cycle_pursuit=PoursuiteDeCycle.YES.name),
                    output_field=BooleanField(),
                ),
                cycle_pursuit=Case(
                    When(
                        Q(training__education_group_type__name=TrainingType.BACHELOR.name)
                        & Exists(
                            EducationalExperienceYear.objects.filter(
                                Q(result=Result.SUCCESS.name) | Q(result=Result.SUCCESS_WITH_RESIDUAL_CREDITS.name),
                                educational_experience__person=OuterRef('candidate'),
                                educational_experience__country__iso_code=BE_ISO_CODE,
                            )
                        ),
                        then=F('generaleducationadmission__cycle_pursuit'),
                    ),
                    default=Value(''),
                ),
                late_enrollment=F('generaleducationadmission__late_enrollment'),
                is_external_reorientation=F('generaleducationadmission__is_external_reorientation'),
                is_external_modification=F('generaleducationadmission__is_external_modification'),
            )
            .select_related(
                'candidate__country_of_citizenship',
                'last_update_author',
                'determined_academic_year',
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
                'candidate__student_set',
                'candidate__personmergeproposal',
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
        if noma:
            candidate_from_noma = (
                Person.objects.filter(
                    Q(student__registration_id=noma) | Q(personmergeproposal__registration_id_sent_to_digit=noma)
                ).only('id')
            ).first()
            qs = qs.filter(candidate_id=candidate_from_noma.id) if candidate_from_noma else qs.none()
        if matricule_candidat:
            qs = qs.filter(candidate__global_id=matricule_candidat)
        if type:
            qs = qs.filter(type_demande=type)
        if site_inscription:
            qs = qs.filter(training__enrollment_campus__uuid=site_inscription)
        if entites:
            related_entities = get_entities_with_descendants_ids(entites)
            qs = qs.filter(training__management_entity_id__in=related_entities)
        if demandeur:
            qs = qs.filter_according_to_roles(demandeur)
        if types_formation:
            qs = qs.filter(training__education_group_type__name__in=types_formation)
        if formation:
            terms = formation.split()
            training_filters = Q()
            for term in terms:
                if term.endswith('-1'):
                    training_filters &= Q(est_premiere_annee=True)
                    term = term[:-2]
                # The term can be a part of the acronym or of the training title
                training_filters &= Q(Q(training__acronym__icontains=term) | Q(training__title__icontains=term))
            qs = qs.filter(training_filters)
        if etats:
            qs = qs.filter(status__in=etats)
        if bourse_internationale:
            qs = qs.filter(
                Q(doctorateadmission__international_scholarship_id=bourse_internationale)
                | Q(generaleducationadmission__international_scholarship_id=bourse_internationale),
            )
        if bourse_erasmus_mundus:
            qs = qs.filter(generaleducationadmission__erasmus_mundus_scholarship_id=bourse_erasmus_mundus)
        if bourse_double_diplomation:
            qs = qs.filter(generaleducationadmission__double_degree_scholarship_id=bourse_double_diplomation)

        if quarantaine in [True, False]:
            # Validation de la quarantaine queryset
            if quarantaine:
                qs = qs.filter_in_quarantine()
            else:
                qs = qs.exclude(id__in=qs.filter_in_quarantine().values('id'))

        if tardif_modif_reorientation:
            related_field = {
                TardiveModificationReorientationFiltre.INSCRIPTION_TARDIVE.name: 'late_enrollment',
                TardiveModificationReorientationFiltre.MODIFICATION_INSCRIPTION.name: 'is_external_modification',
                TardiveModificationReorientationFiltre.REORIENTATION.name: 'is_external_reorientation',
            }[tardif_modif_reorientation]

            qs = qs.filter(**{f'{related_field}': True})

        if mode_filtres_etats_checklist and filtres_etats_checklist:

            json_path_to_checks = defaultdict(set)
            all_checklist_filters = Q()

            # Manage the case of the "AUTHENTIFICATION" and "BESOIN_DEROGATION" filters which are hierarchical
            # If one sub item is selected, the parent must be unselected as the parent itself includes all sub items
            # (AND query if both parent and sub items are selected)
            selected_parent_identifiers_by_tab: Dict[str, Set[str]] = defaultdict(set)

            for (tab_name, prefix_identifier,) in [
                (
                    OngletsChecklist.experiences_parcours_anterieur.name,
                    'AUTHENTIFICATION',
                ),
                (
                    OngletsChecklist.financabilite.name,
                    'BESOIN_DEROGATION',
                ),
                (
                    OngletsChecklist.decision_sic.name,
                    'BESOIN_DEROGATION',
                ),
            ]:
                current_filters = filtres_etats_checklist.get(tab_name)
                if any(f'{prefix_identifier}.' in current_filter for current_filter in current_filters):
                    try:
                        current_filters.remove(prefix_identifier)
                        selected_parent_identifiers_by_tab[tab_name].add(prefix_identifier)
                    except ValueError:
                        pass

            for tab_name, status_values in filtres_etats_checklist.items():
                if not status_values:
                    continue

                current_tab: Optional[
                    Dict[str, Dict[str, ConfigurationStatutChecklist]]
                ] = ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT.get(tab_name)

                if not current_tab:
                    continue

                selected_parent_identifiers = selected_parent_identifiers_by_tab.get(tab_name)

                for status_value in status_values:
                    current_status_filter: Optional[ConfigurationStatutChecklist] = current_tab.get(status_value)

                    if not current_status_filter:
                        continue

                    if (
                        current_status_filter.identifiant_parent
                        and selected_parent_identifiers
                        and current_status_filter.identifiant_parent in selected_parent_identifiers
                    ):
                        # For the sub statuses, if the parent is selected, we filter on both items (AND query)
                        current_status_filter = current_status_filter.merge_statuses(
                            current_tab[current_status_filter.identifiant_parent]
                        )

                    # Specific cases
                    if tab_name == OngletsChecklist.experiences_parcours_anterieur.name:
                        # > For the past experiences, we search if one of them match the criteria
                        fields_to_filter = {}

                        if current_status_filter.statut:
                            fields_to_filter['statut'] = current_status_filter.statut.name
                        if current_status_filter.extra:
                            fields_to_filter['extra'] = current_status_filter.extra

                        current_checklist_filters = Q(
                            checklist__current__parcours_anterieur__enfants__contains=[fields_to_filter],
                        )

                        json_path_to_checks['checklist__current__parcours_anterieur'].add('enfants')
                        json_path_to_checks['checklist__current'].add('parcours_anterieur')
                        json_path_to_checks['checklist'].add('current')

                    else:
                        current_checklist_filters = Q()
                        with_json_checklist_filter = False

                        # Filter on the checklist tab status
                        if current_status_filter.statut:
                            current_checklist_filters = Q(
                                **{
                                    f'checklist__current__{tab_name}__statut': current_status_filter.statut.name,
                                }
                            )
                            json_path_to_checks[f'checklist__current__{tab_name}'].add('statut')
                            with_json_checklist_filter = True

                        # Filter on the checklist tab extra if necessary
                        if current_status_filter.extra:
                            current_extra = {**current_status_filter.extra}

                            if tab_name == OngletsChecklist.decision_sic.name:
                                # Filter on the dispensation needed status if necessary
                                dispensation_needed = current_extra.pop('etat_besoin_derogation', None)

                                if dispensation_needed:
                                    current_checklist_filters &= Q(
                                        generaleducationadmission__dispensation_needed=dispensation_needed,
                                    )
                            elif tab_name == OngletsChecklist.financabilite.name:
                                # Filter on the dispensation status if necessary
                                dispensation_needed = current_extra.pop('etat_besoin_derogation', None)

                                if dispensation_needed:
                                    current_checklist_filters &= Q(
                                        generaleducationadmission__financability_dispensation_status=(
                                            dispensation_needed
                                        ),
                                    )

                            if current_extra:
                                current_checklist_filters &= Q(
                                    **{
                                        f'checklist__current__{tab_name}__extra__contains': current_extra,
                                    }
                                )
                                json_path_to_checks[f'checklist__current__{tab_name}'].add('extra')
                                with_json_checklist_filter = True

                        if with_json_checklist_filter:
                            json_path_to_checks['checklist__current'].add(tab_name)
                            json_path_to_checks['checklist'].add('current')

                    all_checklist_filters |= current_checklist_filters

            if mode_filtres_etats_checklist == ModeFiltrageChecklist.EXCLUSION.name:
                # We exclude the admissions whose the specific keys have the specified values
                all_checklist_filters = ~all_checklist_filters

                # We exclude the admissions whose the specific keys are missing (for unconfirmed admission,
                # other admission contexts etc.)
                for base_key, missing_keys in json_path_to_checks.items():
                    all_checklist_filters |= ~Q(**{f'{base_key}__has_keys': missing_keys})

            qs = qs.filter(all_checklist_filters)

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

        # Paginate the queryset
        if page and taille_page:
            result = PaginatedList(complete_list=qs.all().values_list('uuid', flat=True))
            bottom = (page - 1) * taille_page
            top = page * taille_page
            qs = qs[bottom:top]
        else:
            result = PaginatedList(id_attribute='uuid')

        for admission in qs:
            result.append(cls.load_dto_from_model(admission, language_is_french))

        return result

    @classmethod
    def load_dto_from_model(cls, admission: BaseAdmission, language_is_french: bool) -> DemandeRechercheDTO:
        if (
            hasattr(admission.candidate, 'personmergeproposal')
            and admission.candidate.personmergeproposal.registration_id_sent_to_digit
        ):
            noma_candidat = admission.candidate.personmergeproposal.registration_id_sent_to_digit
        elif admission.candidate.student_set.exists():
            noma_candidat = admission.candidate.student_set.first().registration_id
        else:
            noma_candidat = ""

        return DemandeRechercheDTO(
            uuid=admission.uuid,
            numero_demande=admission.formatted_reference,  # From annotation
            nom_candidat=admission.candidate.last_name,
            prenom_candidat=admission.candidate.first_name,
            noma_candidat=noma_candidat,
            plusieurs_demandes=admission.has_several_admissions_in_progress,  # From annotation
            sigle_formation=admission.training.acronym,
            code_formation=admission.training.partial_acronym,
            intitule_formation=getattr(admission.training, 'title' if language_is_french else 'title_english'),
            type_formation=admission.training.education_group_type.name,
            annee_formation=admission.training.academic_year.year,
            lieu_formation=admission.teaching_campus,  # From annotation
            est_inscription_tardive=admission.late_enrollment,  # From annotation
            est_reorientation_inscription_externe=admission.is_external_reorientation,  # From annotation
            est_modification_inscription_externe=admission.is_external_modification,  # From annotation
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
            derniere_modification_par='{first_name} {last_name}'.format(
                first_name=admission.last_update_author.first_name,
                last_name=admission.last_update_author.last_name,
            )
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
            est_premiere_annee=admission.est_premiere_annee,
            poursuite_de_cycle=admission.cycle_pursuit,
            annee_calculee=admission.determined_academic_year.year if admission.determined_academic_year else None,
            adresse_email_candidat=admission.candidate.private_email,
            reponses_questions_specifiques=admission.specific_question_answers,
        )
