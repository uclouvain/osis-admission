# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict, List, Optional

from django.conf import settings
from django.db.models import Case, F, OuterRef, Prefetch, Q, Subquery, Value, When
from django.db.models.fields import CharField
from django.db.models.functions import Coalesce, Concat
from django.utils.translation import get_language, gettext

from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixEdition,
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_continue.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
    ConfigurationStatutChecklist,
)
from admission.ddd.admission.formation_continue.domain.service.i_lister_demandes import (
    IListerDemandesService,
)
from admission.ddd.admission.formation_continue.dtos.liste import DemandeRechercheDTO
from admission.infrastructure.utils import get_entities_with_descendants_ids
from admission.models import ContinuingEducationAdmission, EPCInjection
from admission.models.epc_injection import EPCInjectionStatus
from admission.views import PaginatedList


class ListerDemandesService(IListerDemandesService):
    @classmethod
    def lister(
        cls,
        annee_academique: Optional[int] = None,
        edition: Optional[str] = '',
        numero: Optional[int] = None,
        matricule_candidat: Optional[str] = '',
        etats: Optional[List[str]] = None,
        facultes: Optional[List[str]] = None,
        types_formation: Optional[List[str]] = None,
        sigles_formations: Optional[List] = None,
        inscription_requise: Optional[bool] = None,
        injection_epc_en_erreur: Optional[bool] = None,
        paye: Optional[bool] = None,
        marque_d_interet: Optional[bool] = None,
        mode_filtres_etats_checklist: Optional[str] = '',
        filtres_etats_checklist: Optional[Dict[str, List[str]]] = None,
        demandeur: Optional[str] = '',
        tri_inverse: bool = False,
        champ_tri: Optional[str] = None,
        page: Optional[int] = None,
        taille_page: Optional[int] = None,
    ) -> PaginatedList[DemandeRechercheDTO]:
        language_is_french = get_language() == settings.LANGUAGE_CODE_FR

        # Base queryset
        qs = (
            ContinuingEducationAdmission.objects.with_training_management_and_reference()
            .annotate_admission_epc_injection_status()
            .annotate(
                last_update_author_name=Case(
                    When(Q(last_update_author=F('candidate')), then=Value(gettext('Candidate'))),
                    When(Q(last_update_author__isnull=True), then=Value('')),
                    default=Concat('last_update_author__first_name', Value(' '), 'last_update_author__last_name'),
                    output_field=CharField(),
                ),
            )
            .select_related(
                'candidate',
                'training__academic_year',
                'training__specificiufcinformations',
            )
            .prefetch_related('candidate__student_set')
        )

        # Filter the queryset
        if annee_academique:
            qs = qs.filter(
                Q(determined_academic_year__year=annee_academique)
                | Q(determined_academic_year__isnull=True, training__academic_year__year=annee_academique)
            )

        if edition:
            qs = qs.filter(edition__in=edition)

        if numero:
            qs = qs.filter(reference=numero)

        if matricule_candidat:
            qs = qs.filter(candidate__global_id=matricule_candidat)

        if etats:
            qs = qs.filter(status__in=etats)

        if types_formation:
            qs = qs.filter(training__education_group_type__name__in=types_formation)

        if sigles_formations:
            qs = qs.filter(training__acronym__in=sigles_formations)

        if inscription_requise is not None:
            qs = qs.filter(training__specificiufcinformations__registration_required=inscription_requise)

        if paye is not None:
            qs = qs.filter(in_payement_order=paye)

        if marque_d_interet:
            qs = qs.filter(interested_mark=marque_d_interet)

        if injection_epc_en_erreur is True:
            qs = qs.filter(last_epc_injection_status__in=EPCInjectionStatus.error_or_pending_statuses())
        elif injection_epc_en_erreur is False:
            qs = qs.exclude(last_epc_injection_status__in=EPCInjectionStatus.error_or_pending_statuses())

        if facultes:
            related_entities = get_entities_with_descendants_ids(facultes)
            qs = qs.filter(training__management_entity_id__in=related_entities)

        if demandeur:
            qs = qs.filter_according_to_roles(demandeur, permission='admission.view_continuing_enrolment_applications')

        if mode_filtres_etats_checklist and filtres_etats_checklist:

            json_path_to_checks = defaultdict(set)
            all_checklist_filters = Q()

            for tab_name, status_values in filtres_etats_checklist.items():
                if not status_values:
                    continue

                current_tab: Optional[Dict[str, Dict[str, ConfigurationStatutChecklist]]] = (
                    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT.get(tab_name)
                )

                if not current_tab:
                    continue

                for status_value in status_values:
                    current_status_filter: Optional[ConfigurationStatutChecklist] = current_tab.get(status_value)

                    if not current_status_filter:
                        continue

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
                        current_checklist_filters &= Q(
                            **{
                                f'checklist__current__{tab_name}__extra__contains': current_status_filter.extra,
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

        # Sort the queryset
        field_order = []
        if champ_tri:
            if champ_tri == 'etat_demande':
                qs = qs.annotate_ordered_enum('status', 'ordered_status', ChoixStatutPropositionContinue)
            elif champ_tri == 'edition':
                qs = qs.annotate_ordered_enum('edition', 'ordered_edition', ChoixEdition)

            field_order = {
                'numero_demande': ['formatted_reference'],
                'nom_candidat': ['candidate__last_name', 'candidate__first_name'],
                'courriel_candidat': ['candidate__email'],
                'formation': ['training__acronym'],
                'edition': ['ordered_edition'],
                'faculte': ['training_management_faculty'],
                'paye': ['in_payement_order'],
                'etat_demande': ['ordered_status'],
                'etat_injection_epc': ['last_epc_injection_status'],
                'date_confirmation': ['submitted_at'],
                'derniere_modification_le': ['modified_at'],
                'derniere_modification_par': ['last_update_author_name'],
            }[champ_tri]

            if tri_inverse:
                field_order = ['-' + field for field in field_order]

        qs = qs.order_by(*field_order, 'id')

        # Paginate the queryset
        if page is not None and taille_page is not None:
            result = PaginatedList(complete_list=qs.all().values_list('uuid', flat=True))
            bottom = (page - 1) * taille_page
            top = page * taille_page
            qs = qs[bottom:top]
        else:
            result = PaginatedList(id_attribute='uuid')

        # Convert the queryset to a list of DTOs

        # Fields that have translation versions
        translated_fields_names = (
            {
                'training_title': 'title',
            }
            if language_is_french
            else {
                'training_title': 'title_english',
            }
        )

        for admission in qs:
            result.append(cls.load_dto_from_model(admission, translated_fields_names))

        return result

    @classmethod
    def load_dto_from_model(
        cls,
        admission: ContinuingEducationAdmission,
        translated_fields_names: Dict[str, str],
    ) -> DemandeRechercheDTO:
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
            courriel_candidat=admission.candidate.private_email,
            sigle_formation=admission.training.acronym,
            code_formation=admission.training.partial_acronym,
            intitule_formation=getattr(admission.training, translated_fields_names['training_title']),
            inscription_au_role_obligatoire=(
                admission.training.specificiufcinformations.registration_required
                if getattr(admission.training, 'specificiufcinformations', None)
                else None
            ),
            edition=admission.edition,
            sigle_faculte=admission.training_management_faculty,  # From annotation
            paye=admission.in_payement_order,
            etat_demande=admission.status,
            etat_injection_epc=admission.last_epc_injection_status,  # From annotation
            date_confirmation=admission.submitted_at,
            derniere_modification_le=admission.modified_at,
            derniere_modification_par=admission.last_update_author_name,  # From annotation
        )
