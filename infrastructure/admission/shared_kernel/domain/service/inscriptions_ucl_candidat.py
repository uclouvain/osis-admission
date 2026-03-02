# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.db.models import F, QuerySet

from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_ucl_candidat import (
    IInscriptionsUCLCandidatService,
)
from admission.ddd.admission.shared_kernel.dtos.inscription_ucl_candidat import (
    InscriptionUCLCandidatDTO,
    PeriodeReinscriptionDTO,
)
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.academic_type import AcademicTypes
from base.models.enums.education_group_types import TrainingType
from base.models.session_exam_calendar import SessionExamCalendar
from ddd.logic.deliberation.cloture.dto.deliberation import (
    DeliberationCycleDTO,
    DeliberationProgrammeAnnuelDTO,
)
from ddd.logic.deliberation.cloture.queries import (
    RechercherDeliberationCycleQuery,
    RechercherDeliberationsProgrammesAnnuelsActeesQuery,
)
from ddd.logic.deliberation.propositions.domain.model._decision import Decision
from ddd.logic.diffusion_des_notes.domain.validator.exceptions import DateDiffusionDeNotesFormationPasTrouveException
from ddd.logic.diffusion_des_notes.dto.date_diffusion_de_notes_individuelle import DateDiffusionDeNotesDTO
from ddd.logic.diffusion_des_notes.queries import GetDateDiffusionDeNotesQuery
from ddd.logic.formation_catalogue.commands import SearchFormationsCommand
from ddd.logic.formation_catalogue.dtos.training import TrainingDto
from ddd.logic.inscription_aux_evaluations.shared_kernel.dto.formulaire_inscription import FormulaireInscriptionDTO
from ddd.logic.inscription_aux_evaluations.shared_kernel.queries import RechercherFormulairesQuery
from epc.models.enums.etat_inscription import EtatInscriptionFormation
from epc.models.enums.statut_inscription_programme_annuel import StatutInscriptionProgrammAnnuel
from epc.models.inscription_programme_annuel import InscriptionProgrammeAnnuel


class InscriptionsUCLCandidatService(IInscriptionsUCLCandidatService):
    @classmethod
    def enrolment_qs(
        cls,
        global_id: str,
        years: list[int] | None = None,
        sigle_formation: str = '',
    ) -> QuerySet[InscriptionProgrammeAnnuel]:
        qs = InscriptionProgrammeAnnuel.objects.filter(
            etat_inscription__in=[
                EtatInscriptionFormation.INSCRIT_AU_ROLE.name,
                EtatInscriptionFormation.PROVISOIRE.name,
                EtatInscriptionFormation.CESSATION.name,
            ],
            programme__offer__academic_type__in=[
                AcademicTypes.ACADEMIC.name,
                AcademicTypes.NON_ACADEMIC_CREF.name,
            ],
            statut__in=[
                StatutInscriptionProgrammAnnuel.ETUDIANT_UCL.name,
            ],
            programme_cycle__etudiant__person__global_id=global_id,
        )

        if years:
            qs = qs.filter(programme__offer__academic_year__year__in=years)

        if sigle_formation:
            qs = qs.filter(programme__offer__acronym=sigle_formation)

        return qs

    @classmethod
    def recuperer(
        cls,
        matricule_candidat: str,
        annees: list[int] | None = None,
    ) -> list[InscriptionUCLCandidatDTO]:
        from infrastructure.messages_bus import message_bus_instance

        enrolment_qs = cls.enrolment_qs(
            global_id=matricule_candidat,
            years=annees,
        ).annotate(
            noma=F('programme_cycle__etudiant__registration_id'),
            sigle_formation=F('programme__offer__acronym'),
            annee_formation=F('programme__offer__academic_year__year'),
        )

        trainings_ids: list[tuple[str, int]] = []
        nomas: list[str] = []

        for enrolment in enrolment_qs:
            trainings_ids.append((enrolment.sigle_formation, enrolment.annee_formation))
            nomas.append(enrolment.noma)

        trainings: list[TrainingDto] = message_bus_instance.invoke(SearchFormationsCommand(sigles_annees=trainings_ids))

        trainings_by_identifier = {(training.acronym, training.year): training for training in trainings}

        cycles_deliberations: list[DeliberationCycleDTO] = message_bus_instance.invoke(
            RechercherDeliberationCycleQuery(nomas=nomas)
        )

        cycles_deliberations_dict = {
            (deliberation.noma, deliberation.sigle_formation): deliberation for deliberation in cycles_deliberations
        }

        enrolments = []

        for enrolment in enrolment_qs:
            current_training = trainings_by_identifier.get((enrolment.sigle_formation, enrolment.annee_formation))
            cycle_deliberation_decision = cycles_deliberations_dict.get((enrolment.noma, enrolment.sigle_formation))

            enrolments.append(
                InscriptionUCLCandidatDTO(
                    sigle_formation=enrolment.sigle_formation,
                    intitule_formation_fr=current_training.title_fr,
                    intitule_formation_en=current_training.title_en,
                    annee=enrolment.annee_formation,
                    est_diplome=cycle_deliberation_decision.est_diplome if cycle_deliberation_decision else False,
                    lieu_enseignement=current_training.main_teaching_campus_name,
                    type_formation=current_training.type,
                )
            )

        return enrolments

    @classmethod
    def est_inscrit_recemment(
        cls,
        matricule_candidat: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        administrative_year = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant().annee
        return cls.enrolment_qs(
            global_id=matricule_candidat,
            years=[administrative_year, administrative_year - 1],
        ).exists()

    @classmethod
    def est_en_poursuite(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
    ) -> bool:
        return cls.enrolment_qs(
            global_id=matricule_candidat,
            sigle_formation=sigle_formation,
        ).exists()

    @classmethod
    def est_en_poursuite_directe(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        administrative_year = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant().annee
        return cls.enrolment_qs(
            global_id=matricule_candidat,
            sigle_formation=sigle_formation,
            years=[administrative_year - 1],
        ).exists()

    @classmethod
    def est_delibere(
        cls,
        matricule_candidat: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> bool:
        from infrastructure.messages_bus import message_bus_instance

        # Get the academic year to check
        administrative_calendar = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant()

        target_year = administrative_calendar.annee - 1

        # Get the enrolments that must be deliberated
        enrolment_qs = (
            cls.enrolment_qs(
                global_id=matricule_candidat,
                years=[target_year],
            )
            .exclude(
                etat_inscription=EtatInscriptionFormation.CESSATION.name,
            )
            .exclude(
                programme__offer__education_group_type__name__in=TrainingType.doctorate_types(),
            )
            .annotate(
                sigle_formation=F('programme__offer__acronym'),
                noma=F('programme_cycle__etudiant__registration_id'),
            )
            .values('sigle_formation', 'noma', 'est_premiere_annee_bachelier')
        )

        if not enrolment_qs:
            return True

        # Get the information about the deliberations
        all_nomas = [enrolment['noma'] for enrolment in enrolment_qs]

        # Get cycle deliberations by (noma, training_acronym)
        cycles_deliberations: list[DeliberationCycleDTO] = message_bus_instance.invoke(
            RechercherDeliberationCycleQuery(nomas=all_nomas, annee=target_year)
        )

        cycles_deliberations_dict = {
            (deliberation.noma, deliberation.sigle_formation): deliberation for deliberation in cycles_deliberations
        }

        # Get annual deliberations by session by (noma, training_acronym)
        annual_deliberations: list[DeliberationProgrammeAnnuelDTO] = message_bus_instance.invoke(
            RechercherDeliberationsProgrammesAnnuelsActeesQuery(nomas=all_nomas, annee=target_year)
        )

        annual_deliberations_dict: dict[tuple[str, str], dict[int, DeliberationProgrammeAnnuelDTO | None]] = {}
        for deliberation in annual_deliberations:
            deliberation_id = (deliberation.noma, deliberation.sigle_formation)
            if deliberation_id in annual_deliberations_dict:
                annual_deliberations_dict[deliberation_id][deliberation.numero_session] = deliberation
            else:
                annual_deliberations_dict[deliberation_id] = {deliberation.numero_session: deliberation}

        # Get the end date of the exam enrollment last session
        exam_enrollment_last_session_end_date = (
            SessionExamCalendar.objects.filter(
                academic_calendar__reference=AcademicCalendarTypes.EXAM_ENROLLMENTS.name,
                academic_calendar__data_year__year=target_year,
                number_session=3,
            )
            .values_list('academic_calendar__end_date', flat=True)
            .get()
        )

        today_date = datetime.date.today()

        after_last_session_enrollment_period = today_date > exam_enrollment_last_session_end_date

        # Get the enrolments of the exams of the last session (only if it can be necessary)
        if after_last_session_enrollment_period:
            last_session_exam_enrolments: list[FormulaireInscriptionDTO] = message_bus_instance.invoke(
                RechercherFormulairesQuery(
                    annee=target_year,
                    nomas=all_nomas,
                    session=3,
                )
            )
            last_session_exam_enrolments_set = {
                (formulaire.noma, formulaire.sigle_formation) for formulaire in last_session_exam_enrolments
            }
        else:
            last_session_exam_enrolments_set = set()

        for enrolment in enrolment_qs:
            deliberation_id = (enrolment['noma'], enrolment['sigle_formation'])

            current_cycle_deliberation = cycles_deliberations_dict.get(deliberation_id)
            current_annual_deliberations = annual_deliberations_dict.get(deliberation_id, {})

            # The cycle and the year are not yet successful
            if (not current_cycle_deliberation or not current_cycle_deliberation.est_diplome) and not any(
                annual_deliberation.decision == Decision.REUSSITE.name
                for annual_deliberation in current_annual_deliberations.values()
            ):
                # <= 15/7/N
                if not after_last_session_enrollment_period:
                    return False

                # > 15/7/N, with enrolment to the last session
                if deliberation_id in last_session_exam_enrolments_set:
                    last_session_annual_deliberation = current_annual_deliberations.get(3)

                    if not last_session_annual_deliberation or not last_session_annual_deliberation.decision:
                        # No deliberation decision for the last session
                        return False

                    try:
                        marks_diffusion_date: DateDiffusionDeNotesDTO = message_bus_instance.invoke(
                            GetDateDiffusionDeNotesQuery(
                                sigle_formation=enrolment['sigle_formation'],
                                premiere_annee=enrolment['est_premiere_annee_bachelier'],
                                noma=enrolment['noma'],
                                annee=target_year,
                                numero_session=3,
                            )
                        )

                        # The marks have not been submitted
                        if today_date < marks_diffusion_date.date:
                            return False

                    except DateDiffusionDeNotesFormationPasTrouveException:
                        # The marks have not been submitted
                        return False

        return True

    @classmethod
    def recuperer_informations_periode_de_reinscription(
        cls,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
    ) -> PeriodeReinscriptionDTO:
        administrative_calendar = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant()

        session_exam_calendar_start_date = (
            SessionExamCalendar.objects.filter(
                academic_calendar__reference=AcademicCalendarTypes.DELIBERATION.name,
                academic_calendar__data_year__year=administrative_calendar.annee - 1,
                number_session=2,
            )
            .values_list('academic_calendar__start_date', flat=True)
            .first()
        )

        return PeriodeReinscriptionDTO(
            date_debut=session_exam_calendar_start_date,
            date_fin=administrative_calendar.date_fin,
            annee_formation=administrative_calendar.annee,
        )
