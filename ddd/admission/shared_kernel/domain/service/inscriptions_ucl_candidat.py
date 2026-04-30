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

from admission.ddd.admission.formation_generale.domain.model.enums import PoursuiteDeCycle
from admission.ddd.admission.shared_kernel.domain.model.formation import FormationIdentity
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
from admission.ddd.admission.shared_kernel.dtos.inscription_ucl_candidat import (
    InscriptionUCLCandidatDTO,
    PeriodeReinscriptionDTO,
)
from base.models.enums.education_group_types import TrainingType
from ddd.logic.deliberation.propositions.domain.model._decision import Decision
from ddd.logic.diffusion_des_notes.domain.validator.exceptions import DateDiffusionDeNotesFormationPasTrouveException
from ddd.logic.financabilite.domain.service.algorithmes import VETE1BA
from epc.models.enums.etat_concours_attestation import EtatConcoursAttestation
from epc.models.enums.reussite_bloc1 import ReussiteBloc1
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
                    est_premiere_annee_bachelier=inscription.est_premiere_annee_bachelier,
                    etat_concours_attestation=inscription.etat_concours_attestation,
                    noma=inscription.noma,
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
    ) -> bool:
        # Récupérer l'année académique à vérifier
        calendrier_administratif = annee_inscription_formation_translator.recuperer_calendrier_administratif_courant()

        annee_cible = calendrier_administratif.annee - 1

        # Récupérer les inscriptions qui doivent être délibérées
        inscriptions = inscriptions_translator.recuperer_inscriptions_deliberables(
            matricule_candidat=matricule_candidat,
            annee=annee_cible,
        )

        if not inscriptions:
            return True

        nomas = [inscription.noma for inscription in inscriptions]

        # Récupérer les informations relatives aux délibérations
        deliberations_cycles = deliberation_translator.recuperer_deliberations_cycles(
            nomas=nomas,
            annee=annee_cible,
        )

        deliberations_annuellees = deliberation_translator.recuperer_deliberations_annuelles(
            nomas=nomas,
            annee=annee_cible,
        )

        date_fin_periode_inscription_examen_derniere_session = (
            inscriptions_evaluations_translator.recuperer_date_fin_periode_inscription_etudiants_derniere_session(
                annee=annee_cible,
            )
        )

        date_du_jour = datetime.date.today()

        est_apres_fin_periode_inscription_examen_derniere_session = (
            date_du_jour > date_fin_periode_inscription_examen_derniere_session
        )

        inscriptions_examens_derniere_session = (
            inscriptions_evaluations_translator.recuperer_inscriptions_etudiants_derniere_session(
                nomas=nomas,
                annee=annee_cible,
            )
            if est_apres_fin_periode_inscription_examen_derniere_session
            else set()
        )

        for inscription in inscriptions:
            identifiant_inscription = (inscription.noma, inscription.sigle)

            deliberation_cycle = deliberations_cycles.get(identifiant_inscription)
            deliberation_annuelle_par_session = deliberations_annuellees.get(identifiant_inscription, {})

            # Le cycle et l'année ne sont pas réussies
            if (not deliberation_cycle or not deliberation_cycle.est_diplome) and not any(
                deliberation_session.decision == Decision.REUSSITE.name
                for deliberation_session in deliberation_annuelle_par_session.values()
            ):
                # <= 15/7/N
                if not est_apres_fin_periode_inscription_examen_derniere_session:
                    return False

                # > 15/7/N, avec inscription à la dernière session
                if identifiant_inscription in inscriptions_examens_derniere_session:
                    deliberation_derniere_session = deliberation_annuelle_par_session.get(3)

                    if not deliberation_derniere_session:
                        # Pas de décision de délibération pour la dernière session
                        return False

                    try:
                        date_diffusion_notes_derniere_session = (
                            diffusion_notes_translator.recuperer_date_diffusion_notes_derniere_session(
                                sigle_formation=inscription.sigle,
                                est_premiere_annee_bachelier=inscription.est_premiere_annee_bachelier,
                                noma=inscription.noma,
                                annee=inscription.annee,
                            )
                        )

                        # Les notes n'ont pas été diffusées
                        if date_du_jour < date_diffusion_notes_derniere_session:
                            return False

                    except DateDiffusionDeNotesFormationPasTrouveException:
                        # Les notes n'ont pas été diffusées
                        return False

        return True

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

    @classmethod
    def est_en_poursuite_cycle_bachelier(
        cls,
        inscriptions_ucl_candidat: list[InscriptionUCLCandidatDTO],
        formation_id: FormationIdentity,
        type_formation: TrainingType,
        deliberation_translator: IDeliberationTranslator,
    ) -> PoursuiteDeCycle:
        if type_formation != TrainingType.BACHELOR:
            return PoursuiteDeCycle.TO_BE_DETERMINED

        inscription_bachelier_annee_precedente = next(
            (
                inscription
                for inscription in inscriptions_ucl_candidat
                if inscription.sigle_formation == formation_id.sigle and inscription.annee == formation_id.annee - 1
            ),
            None,
        )

        if inscription_bachelier_annee_precedente:
            if not inscription_bachelier_annee_precedente.est_premiere_annee_bachelier:
                return PoursuiteDeCycle.YES

            deliberations_annuelles = deliberation_translator.recuperer_deliberations_annuelles(
                nomas=[inscription_bachelier_annee_precedente.noma],
                annee=inscription_bachelier_annee_precedente.annee,
                sigle_formation=inscription_bachelier_annee_precedente.sigle_formation,
            )

            bloc_1_reussi = any(
                deliberation_session
                and deliberation_session.etat_cycle_annualise
                and deliberation_session.etat_cycle_annualise.reussite_bloc1 == ReussiteBloc1.REUSSITE_BLOC1.name
                for deliberation in deliberations_annuelles.values()
                for deliberation_session in deliberation.values()
            )

            if bloc_1_reussi and (
                formation_id.sigle != VETE1BA
                or inscription_bachelier_annee_precedente.etat_concours_attestation
                == EtatConcoursAttestation.ACCORDEE.name
            ):
                return PoursuiteDeCycle.YES

        return PoursuiteDeCycle.NO
