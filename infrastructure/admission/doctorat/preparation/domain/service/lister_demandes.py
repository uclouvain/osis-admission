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
import datetime
from collections import defaultdict
from typing import Dict, List, Optional

from django.conf import settings
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.utils.translation import get_language

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    BourseRecherche,
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.model.statut_checklist import (
    ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT,
    ConfigurationStatutChecklist,
    onglet_decision_cdd,
    onglet_decision_sic,
)
from admission.ddd.admission.doctorat.preparation.domain.service.i_lister_demandes import (
    IListerDemandesService,
)
from admission.ddd.admission.doctorat.preparation.dtos.liste import DemandeRechercheDTO
from admission.ddd.admission.enums.checklist import ModeFiltrageChecklist
from admission.infrastructure.admission.doctorat.preparation.read_view.repository.tableau_bord import (
    TableauBordRepositoryAdmissionMixin,
)
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
        uuid_promoteur: Optional[str] = '',
        type_financement: Optional[str] = '',
        bourse_recherche: Optional[str] = '',
        cotutelle: Optional[bool] = None,
        date_soumission_debut: Optional[datetime.date] = None,
        date_soumission_fin: Optional[datetime.date] = None,
        mode_filtres_etats_checklist: Optional[str] = '',
        filtres_etats_checklist: Optional[Dict[str, List[str]]] = None,
        demandeur: Optional[str] = '',
        fnrs_fria_fresh: Optional[bool] = None,
        indicateur_tableau_bord: Optional[str] = '',
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

        if uuid_promoteur:
            qs = qs.filter(supervision_group__actors__uuid=uuid_promoteur)

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
            qs = qs.filter(submitted_at__lt=date_soumission_fin + datetime.timedelta(days=1))

        if demandeur:
            qs = qs.filter_according_to_roles(demandeur, permission='admission.view_doctorate_enrolment_applications')

        if fnrs_fria_fresh:
            qs = qs.filter(is_fnrs_fria_fresh_csc_linked=fnrs_fria_fresh)

        if indicateur_tableau_bord:
            dashboard_filter = TableauBordRepositoryAdmissionMixin.ADMISSION_DJANGO_FILTER_BY_INDICATOR.get(
                indicateur_tableau_bord,
            )

            if dashboard_filter:
                qs = qs.filter(dashboard_filter)

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

        # Paginate the queryset
        if page and taille_page:
            result = PaginatedList(complete_list=qs.all().values_list('uuid', flat=True))
            bottom = (page - 1) * taille_page
            top = page * taille_page
            qs = qs[bottom:top]
        else:
            result = PaginatedList(id_attribute='uuid')

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

        status_organization_by_tab = {
            OngletsChecklist.decision_sic.name: onglet_decision_sic,
            OngletsChecklist.decision_cdd.name: onglet_decision_cdd,
        }

        status_by_tab = {
            OngletsChecklist.decision_sic.name: '',
            OngletsChecklist.decision_cdd.name: '',
        }

        if admission.checklist and 'current' in admission.checklist:
            for tab in status_by_tab:
                tab_info = admission.checklist['current'].get(tab)

                if tab_info:
                    tab_status = status_organization_by_tab[tab].get_status(
                        status=tab_info.get('statut'),
                        extra=tab_info.get('extra'),
                    )
                    if tab_status:
                        status_by_tab[tab] = tab_status.libelle

        return DemandeRechercheDTO(
            uuid=admission.uuid,
            numero_demande=admission.formatted_reference,  # From annotation
            etat_demande=admission.status,
            nom_candidat=admission.candidate.last_name,
            prenom_candidat=admission.candidate.first_name,
            sigle_formation=admission.training.acronym,
            code_formation=admission.training.partial_acronym,
            intitule_formation=getattr(admission.training, training_title),
            decision_fac=status_by_tab[OngletsChecklist.decision_cdd.name],
            decision_sic=status_by_tab[OngletsChecklist.decision_sic.name],
            date_confirmation=admission.submitted_at,
            derniere_modification_le=admission.modified_at,
            type_admission=admission.type,
            cotutelle=admission.cotutelle,
            code_bourse=admission.scholarship if admission.scholarship else '',  # From annotation
            **country_data,
            **last_author_data,
        )
