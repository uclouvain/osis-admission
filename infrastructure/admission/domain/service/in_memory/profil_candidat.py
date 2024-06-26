# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
from typing import List

from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import CandidatNonTrouveException
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.dtos.resume import ResumeCandidatDTO
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    ExperienceNonAcademiqueDTO,
    AnneeExperienceAcademiqueDTO, ExperienceAcademiqueDTO,
)
from infrastructure.shared_kernel.profil.repository.in_memory.profil import (
    ExperienceAcademique,
    ExperienceNonAcademique, _IdentificationDTO,
)


class ProfilCandidatInMemoryTranslator(IProfilCandidatTranslator):
    profil_candidats: List[_IdentificationDTO] = []
    etudes_secondaires = {}
    experiences_academiques: List[ExperienceAcademique] = []
    experiences_non_academiques: List[ExperienceNonAcademique] = []

    @classmethod
    def get_curriculum(
        cls,
        matricule: str,
        annee_courante: int,
        uuid_proposition: str,
        experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES,
    ) -> 'CurriculumAdmissionDTO':
        try:
            candidate = next(c for c in cls.profil_candidats if c.matricule == matricule)

            experiences_dtos = []
            for experience in cls.experiences_academiques:
                if experience.personne == matricule:
                    experiences_dtos.append(
                        ExperienceAcademiqueDTO(
                            uuid=experience.uuid,
                            pays=experience.pays,
                            annees=[
                                AnneeExperienceAcademiqueDTO(
                                    uuid=annee.uuid,
                                    annee=annee.annee,
                                    resultat=annee.resultat,
                                    releve_notes=annee.releve_notes,
                                    traduction_releve_notes=annee.traduction_releve_notes,
                                    credits_acquis=annee.credits_inscrits,
                                    credits_inscrits=annee.credits_acquis,
                                    avec_bloc_1=annee.avec_bloc_1,
                                    avec_complement=annee.avec_complement,
                                    credits_acquis_communaute_fr=annee.credits_inscrits_communaute_fr,
                                    credits_inscrits_communaute_fr=annee.credits_acquis_communaute_fr,
                                    allegement=annee.allegement,
                                    est_reorientation_102=annee.est_reorientation_102,
                                )
                                for annee in experience.annees
                            ],
                            regime_linguistique=experience.regime_linguistique,
                            type_releve_notes=experience.type_releve_notes,
                            releve_notes=experience.releve_notes,
                            traduction_releve_notes=experience.traduction_releve_notes,
                            diplome=experience.diplome,
                            traduction_diplome=experience.traduction_diplome,
                            a_obtenu_diplome=experience.a_obtenu_diplome,
                            rang_diplome=experience.rang_diplome,
                            date_prevue_delivrance_diplome=experience.date_prevue_delivrance_diplome,
                            titre_memoire=experience.titre_memoire,
                            note_memoire=experience.note_memoire,
                            resume_memoire=experience.resume_memoire,
                            grade_obtenu=experience.grade_obtenu,
                            systeme_evaluation=experience.systeme_evaluation,
                            nom_formation=experience.nom_formation,
                            nom_formation_equivalente_communaute_fr=experience.nom_formation,
                            adresse_institut=experience.adresse_institut,
                            code_institut=experience.code_institut,
                            communaute_institut=experience.communaute_institut,
                            type_institut=experience.type_institut,
                            cycle_formation=experience.cycle_formation,
                            nom_institut=experience.nom_institut,
                            nom_pays=experience.nom_pays,
                            nom_regime_linguistique=experience.nom_regime_linguistique,
                            type_enseignement=experience.type_enseignement,
                            valorisee_par_admissions=[],
                            est_autre_formation=None,
                        ),
                    )

            experiences_non_academiques = [
                ExperienceNonAcademiqueDTO(
                    uuid=experience.uuid,
                    employeur=experience.employeur,
                    date_debut=experience.date_debut,
                    date_fin=experience.date_fin,
                    type=experience.type,
                    certificat=experience.certificat,
                    fonction=experience.fonction,
                    secteur=experience.secteur,
                    autre_activite=experience.autre_activite,
                    valorisee_par_admissions=[],
                )
                for experience in cls.experiences_non_academiques
                if experience.personne == matricule
            ]

            etudes_secondaires = cls.etudes_secondaires.get(matricule)
            annee_etudes_secondaires = etudes_secondaires and etudes_secondaires.annee_diplome_etudes_secondaires

            return CurriculumAdmissionDTO(
                experiences_academiques=experiences_dtos,
                annee_diplome_etudes_secondaires=annee_etudes_secondaires,
                annee_derniere_inscription_ucl=candidate.annee_derniere_inscription_ucl,
                experiences_non_academiques=experiences_non_academiques,
                annee_minimum_a_remplir=cls.get_annee_minimale_a_completer_cv(
                    annee_courante=datetime.date.today().year,
                    annee_diplome_etudes_secondaires=annee_etudes_secondaires,
                    annee_derniere_inscription_ucl=candidate.annee_derniere_inscription_ucl,
                ),
            )
        except StopIteration:
            raise CandidatNonTrouveException



    @classmethod
    def recuperer_toutes_informations_candidat(
        cls,
        matricule: str,
        formation: str,
        annee_courante: int,
        uuid_proposition: str,
        experiences_cv_recuperees: ExperiencesCVRecuperees = ExperiencesCVRecuperees.TOUTES,
    ) -> ResumeCandidatDTO:
        return ResumeCandidatDTO(
            identification=cls.get_identification(matricule),
            coordonnees=cls.get_coordonnees(matricule),
            curriculum=cls.get_curriculum(matricule, annee_courante, uuid_proposition),
            etudes_secondaires=cls.get_etudes_secondaires(matricule),
            connaissances_langues=cls.get_connaissances_langues(matricule),
        )
