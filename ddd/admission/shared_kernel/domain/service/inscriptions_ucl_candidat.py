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

from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_diffusion_notes_translator import IDiffusionNotesTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_formation_translator import IBaseFormationTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_evaluations_translator import (
    IInscriptionsEvaluationsTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.domain.service.i_noma_translator import INomasTranslator
from admission.ddd.admission.shared_kernel.dtos.eligibilite_reinscription import EligibiliteReinscriptionDTO
from admission.ddd.admission.shared_kernel.dtos.inscription_ucl_candidat import (
    InscriptionUCLCandidatDTO,
    PeriodeReinscriptionDTO,
)
from osis_common.ddd import interface


class InscriptionsUCLCandidatService(interface.DomainService):
    @classmethod
    def recuperer(
        cls,
        matricule_candidat: str,
        inscriptions_translator: IInscriptionsTranslatorService,
        formation_translator: IBaseFormationTranslator,
        deliberation_translator: IDeliberationTranslator,
        annees: list[int] | None = None,
    ) -> list[InscriptionUCLCandidatDTO]:
        inscriptions = inscriptions_translator.recuperer(
            matricule_candidat=matricule_candidat,
            annees=annees,
        )

        if not inscriptions:
            return []

        identifiants_formations: list[tuple[str, int]] = []
        nomas: list[str] = []

        for inscription in inscriptions:
            identifiants_formations.append((inscription.sigle, inscription.annee))
            nomas.append(inscription.noma)

        formations = formation_translator.recuperer_informations_formations_inscrites(
            sigles_annees=identifiants_formations,
        )

        deliberations_cycles = deliberation_translator.recuperer_deliberations_cycles(nomas=nomas)

        inscriptions_candidat: list[InscriptionUCLCandidatDTO] = []

        for inscription in inscriptions:
            formation_courante = formations.get((inscription.sigle, inscription.annee))
            deliberation_cycle = deliberations_cycles.get((inscription.noma, inscription.sigle))

            inscriptions_candidat.append(
                InscriptionUCLCandidatDTO(
                    sigle_formation=inscription.sigle,
                    intitule_formation_fr=formation_courante.intitule_fr,
                    intitule_formation_en=formation_courante.intitule_en,
                    annee=inscription.annee,
                    est_diplome=deliberation_cycle.est_diplome if deliberation_cycle else False,
                    lieu_enseignement=formation_courante.lieu_enseignement,
                    type_formation=formation_courante.type,
                )
            )

        return inscriptions_candidat

    @classmethod
    def est_eligible_a_la_reinscription(
        cls,
        matricule_candidat: str,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
        inscriptions_translator: IInscriptionsTranslatorService,
        deliberation_translator: IDeliberationTranslator,
        diffusion_notes_translator: IDiffusionNotesTranslator,
        inscriptions_evaluations_translator: IInscriptionsEvaluationsTranslator,
        formation_translator: IBaseFormationTranslator,
    ) -> EligibiliteReinscriptionDTO:
        # Récupérer l'année académique à vérifier
        calendrier_administratif = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant()

        annee_cible = calendrier_administratif.annee - 1

        # Récupérer les inscriptions qui doivent être délibérées
        inscriptions = inscriptions_translator.recuperer_inscriptions_deliberables(
            matricule_candidat=matricule_candidat,
            annee=annee_cible,
        )

        if not inscriptions:
            return EligibiliteReinscriptionDTO.est_eligible()

        formations = formation_translator.recuperer_informations_formations_inscrites(
            sigles_annees=[(inscription.sigle, inscription.annee) for inscription in inscriptions],
            uclouvain_est_institution_reference=True,
        )

        # Récupérer les informations relatives aux délibérations
        date_fin_periode_inscription_examen_derniere_session = (
            inscriptions_evaluations_translator.recuperer_date_fin_periode_inscription_etudiants_derniere_session(
                annee=annee_cible,
            )
        )

        date_du_jour = datetime.date.today()

        est_apres_fin_periode_inscription_examen_derniere_session = (
            date_du_jour > date_fin_periode_inscription_examen_derniere_session
        )

        candidat_en_attente_fin_inscriptions_examens_session_3 = False

        for inscription in inscriptions:
            # Si la formation n'est pas connue et / ou uclouvain non référent -> éligible
            if (inscription.sigle, inscription.annee) not in formations:
                continue

            sessions_avec_deliberations_finalisees = (
                deliberation_translator.recuperer_sessions_avec_deliberations_finalisees(
                    noma=inscription.noma,
                    sigle_formation=inscription.sigle,
                    annee=inscription.annee,
                )
            )

            sessions_avec_autorisation_diffusion_resultats = (
                diffusion_notes_translator.recuperer_sessions_avec_autorisation_diffusion_resultats(
                    noma=inscription.noma,
                    sigle_formation=inscription.sigle,
                    annee=inscription.annee,
                )
            )

            # Si les délibération d'un étudiant pour un programme annuel sont finalisées et la diffusion des
            # résultats est autorisée -> éligible
            if (
                sessions_avec_deliberations_finalisees
                and sessions_avec_autorisation_diffusion_resultats
                and sessions_avec_deliberations_finalisees == sessions_avec_autorisation_diffusion_resultats
            ):
                continue

            # Si après la date de fin de "Inscriptions aux examens - Session d'examens n°3" (>15/07)
            if est_apres_fin_periode_inscription_examen_derniere_session:
                progressions_potentielles_session_3 = (
                    deliberation_translator.recuperer_progressions_potentielles_troisieme_session(
                        noma=inscription.noma,
                        sigle_formation=inscription.sigle,
                        annee=inscription.annee,
                    )
                )

                # Si progression potentielle en septembre -> Non éligible à la réinscription (cadenas rouge)
                if progressions_potentielles_session_3:
                    return EligibiliteReinscriptionDTO.est_non_eligible_et_en_attente_resultats(annee=annee_cible)

                # Si pas de progression potentielle en septembre

                # > et diffusion des résultats autorisée -> éligible
                if (
                    max(sessions_avec_deliberations_finalisees, default=None)
                    in sessions_avec_autorisation_diffusion_resultats
                ):
                    continue

                # > et diffusion des résultats non autorisée -> Non éligible à la réinscription (cadenas rouge)
                return EligibiliteReinscriptionDTO.est_non_eligible_et_en_attente_resultats(annee=annee_cible)

            # Sinon -> Non éligible à la réinscription
            else:
                # Cadenas orange si au-moins une décision sur le programme annuel
                if sessions_avec_deliberations_finalisees:
                    candidat_en_attente_fin_inscriptions_examens_session_3 = True

                # Sinon cadenas rouge
                else:
                    return EligibiliteReinscriptionDTO.est_non_eligible_et_en_attente_resultats(annee=annee_cible)

        if candidat_en_attente_fin_inscriptions_examens_session_3:
            return EligibiliteReinscriptionDTO.est_non_eligible_et_en_attente_fin_periode_inscription_examens(
                date_fin_periode_inscription_examens=date_fin_periode_inscription_examen_derniere_session
            )

        return EligibiliteReinscriptionDTO.est_eligible()

    @classmethod
    def recuperer_informations_periode_de_reinscription(
        cls,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
        deliberation_translator: IDeliberationTranslator,
    ) -> PeriodeReinscriptionDTO:
        calendrier_administratif = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant()

        date_debut_periode_deliberation_deuxieme_session = (
            deliberation_translator.recuperer_date_debut_periode_deliberation_deuxieme_session(
                annee=calendrier_administratif.annee - 1,
            )
        )

        return PeriodeReinscriptionDTO(
            date_debut=date_debut_periode_deliberation_deuxieme_session,
            date_fin=calendrier_administratif.date_fin,
            annee_formation=calendrier_administratif.annee,
        )

    @classmethod
    def periode_de_reinscription_en_cours(
        cls,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
        deliberation_translator: IDeliberationTranslator,
    ) -> bool:
        periode_reinscription = cls.recuperer_informations_periode_de_reinscription(
            annee_inscription_formation_translator=annee_inscription_formation_translator,
            deliberation_translator=deliberation_translator,
        )
        today_date = datetime.date.today()
        return periode_reinscription.date_debut <= today_date <= periode_reinscription.date_fin

    @classmethod
    def est_diplome(
        cls,
        matricule_candidat: str,
        sigle_formation: str,
        deliberation_translator: IDeliberationTranslator,
        nomas_translator: INomasTranslator,
    ) -> bool:
        nomas = nomas_translator.recuperer(matricule_candidat=matricule_candidat)

        if not nomas:
            return False

        deliberations_cycle = deliberation_translator.recuperer_deliberations_cycles(
            nomas=nomas,
            sigle_formation=sigle_formation,
        )

        return any(deliberation.est_diplome for deliberation in deliberations_cycle.values())

    @classmethod
    def a_suivi_formation(cls, sigle_formation: str, inscriptions: list[InscriptionUCLCandidatDTO]):
        return any(inscription.sigle_formation == sigle_formation for inscription in inscriptions)
