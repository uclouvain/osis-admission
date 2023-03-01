# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List

from admission.ddd.admission.doctorat.preparation.domain.model.proposition import Proposition as PropositionDoctorat
from admission.ddd.admission.doctorat.preparation.domain.service.verifier_curriculum import (
    VerifierCurriculumDoctorat,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.validator_by_business_action import (
    ComptabiliteValidatorList,
    CurriculumValidatorList,
    LanguesConnuesValidatorList,
)
from admission.ddd.admission.domain.model._candidat_adresse import CandidatAdresse
from admission.ddd.admission.domain.model._candidat_signaletique import CandidatSignaletique
from admission.ddd.admission.domain.model.formation import Formation
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.verifier_curriculum import VerifierCurriculum
from admission.ddd.admission.domain.validator.validator_by_business_action import (
    CoordonneesValidatorList,
    IdentificationValidatorList,
)
from admission.ddd.admission.formation_continue.domain.validator.validator_by_business_actions import (
    FormationContinueCurriculumValidatorList,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition as FormationGeneraleProposition,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition as PropositionGenerale
from admission.ddd.admission.formation_generale.domain.validator.validator_by_business_actions import (
    FormationGeneraleCurriculumValidatorList,
    FormationGeneraleComptabiliteValidatorList,
    EtudesSecondairesValidatorList,
    BachelierEtudesSecondairesValidatorList,
)
from base.models.enums.education_group_types import TrainingType
from osis_common.ddd import interface


class ProfilCandidat(interface.DomainService):
    @classmethod
    def verifier_identification(cls, matricule: str, profil_candidat_translator: 'IProfilCandidatTranslator') -> None:
        identification = profil_candidat_translator.get_identification(matricule)
        IdentificationValidatorList(
            identite_signaletique=CandidatSignaletique(
                annee_naissance=identification.annee_naissance,
                date_naissance=identification.date_naissance,
                pays_nationalite=identification.pays_nationalite,
                photo_identite=identification.photo_identite,
                prenom=identification.prenom,
                langue_contact=identification.langue_contact,
                sexe=identification.sexe,
                nom=identification.nom,
                genre=identification.genre,
                pays_naissance=identification.pays_naissance,
                lieu_naissance=identification.lieu_naissance,
                etat_civil=identification.etat_civil,
            ),
            date_naissance=identification.date_naissance,
            annee_naissance=identification.annee_naissance,
            numero_registre_national_belge=identification.numero_registre_national_belge,
            numero_carte_identite=identification.numero_carte_identite,
            carte_identite=identification.carte_identite,
            numero_passeport=identification.numero_passeport,
            passeport=identification.passeport,
            noma_derniere_inscription_ucl=identification.noma_derniere_inscription_ucl,
            annee_derniere_inscription_ucl=identification.annee_derniere_inscription_ucl,
            pays_residence=identification.pays_residence,
        ).validate()

    @classmethod
    def verifier_coordonnees(cls, matricule: str, profil_candidat_translator: 'IProfilCandidatTranslator') -> None:
        coordonnees = profil_candidat_translator.get_coordonnees(matricule)

        CoordonneesValidatorList(
            domicile_legal=CandidatAdresse(
                code_postal=coordonnees.domicile_legal.code_postal,
                ville=coordonnees.domicile_legal.ville,
                pays=coordonnees.domicile_legal.pays,
                rue=coordonnees.domicile_legal.rue,
                numero=coordonnees.domicile_legal.numero_rue,
            )
            if coordonnees.domicile_legal
            else None,
            adresse_correspondance=CandidatAdresse(
                code_postal=coordonnees.adresse_correspondance.code_postal,
                ville=coordonnees.adresse_correspondance.ville,
                pays=coordonnees.adresse_correspondance.pays,
                rue=coordonnees.adresse_correspondance.rue,
                numero=coordonnees.adresse_correspondance.numero_rue,
            )
            if coordonnees.adresse_correspondance
            else None,
        ).validate()

    @classmethod
    def verifier_langues_connues(cls, matricule: str, profil_candidat_translator: 'IProfilCandidatTranslator') -> None:
        codes_langues_connues = profil_candidat_translator.get_langues_connues(matricule)

        LanguesConnuesValidatorList(
            codes_langues_connues=codes_langues_connues,
        ).validate()

    @classmethod
    def verifier_etudes_secondaires(
        cls,
        matricule: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        formation: Formation,
    ) -> None:
        etudes_secondaires = profil_candidat_translator.get_etudes_secondaires(matricule, formation.type)

        if etudes_secondaires.valorisees:
            # Des études secondaires valorisées par une admission sont considérées valides pour les futures admissions
            return

        if formation.type == TrainingType.BACHELOR:
            est_potentiel_vae = profil_candidat_translator.est_potentiel_vae(matricule)
            BachelierEtudesSecondairesValidatorList(
                diplome_etudes_secondaires=etudes_secondaires.diplome_etudes_secondaires,
                annee_diplome_etudes_secondaires=etudes_secondaires.annee_diplome_etudes_secondaires,
                diplome_belge=etudes_secondaires.diplome_belge,
                diplome_etranger=etudes_secondaires.diplome_etranger,
                alternative_secondaires=etudes_secondaires.alternative_secondaires,
                est_potentiel_vae=est_potentiel_vae,
                formation=formation,
            ).validate()
        else:
            EtudesSecondairesValidatorList(
                diplome_etudes_secondaires=etudes_secondaires.diplome_etudes_secondaires,
                annee_diplome_etudes_secondaires=etudes_secondaires.annee_diplome_etudes_secondaires,
            ).validate()

    @classmethod
    def verifier_curriculum(
        cls,
        matricule: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_courante: int,
        curriculum_pdf: List[str],
    ) -> None:
        curriculum = profil_candidat_translator.get_curriculum(
            matricule=matricule,
            annee_courante=annee_courante,
        )

        experiences_academiques_incompletes = VerifierCurriculumDoctorat.recuperer_experiences_academiques_incompletes(
            experiences=curriculum.experiences_academiques,
        )

        CurriculumValidatorList(
            annee_courante=annee_courante,
            experiences_academiques=curriculum.experiences_academiques,
            experiences_academiques_incompletes=experiences_academiques_incompletes,
            annee_diplome_etudes_secondaires=curriculum.annee_diplome_etudes_secondaires,
            annee_derniere_inscription_ucl=curriculum.annee_derniere_inscription_ucl,
            fichier_pdf=curriculum_pdf,
            dates_experiences_non_academiques=curriculum.dates_experiences_non_academiques,
        ).validate()

    @classmethod
    def verifier_curriculum_formation_generale(
        cls,
        proposition: FormationGeneraleProposition,
        type_formation: TrainingType,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_courante: int,
    ) -> None:
        curriculum = profil_candidat_translator.get_curriculum(
            matricule=proposition.matricule_candidat,
            annee_courante=annee_courante,
        )
        experiences_academiques_incompletes = VerifierCurriculum.recuperer_experiences_academiques_incompletes(
            experiences=curriculum.experiences_academiques,
        )

        FormationGeneraleCurriculumValidatorList(
            annee_courante=annee_courante,
            experiences_academiques=curriculum.experiences_academiques,
            experiences_academiques_incompletes=experiences_academiques_incompletes,
            annee_diplome_etudes_secondaires=curriculum.annee_diplome_etudes_secondaires,
            annee_derniere_inscription_ucl=curriculum.annee_derniere_inscription_ucl,
            fichier_pdf=proposition.curriculum,
            dates_experiences_non_academiques=curriculum.dates_experiences_non_academiques,
            type_formation=type_formation,
            equivalence_diplome=proposition.equivalence_diplome,
            sigle_formation=proposition.formation_id.sigle,
        ).validate()

    @classmethod
    def verifier_curriculum_formation_continue(
        cls,
        matricule: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
    ) -> None:
        existence_experiences_cv = profil_candidat_translator.get_existence_experiences_curriculum(matricule=matricule)

        FormationContinueCurriculumValidatorList(
            a_experience_academique=existence_experiences_cv.a_experience_academique,
            a_experience_non_academique=existence_experiences_cv.a_experience_non_academique,
        ).validate()

    @classmethod
    def verifier_comptabilite_doctorat(
        cls,
        proposition: PropositionDoctorat,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_courante: int,
    ):
        conditions_comptabilite = profil_candidat_translator.get_conditions_comptabilite(
            matricule=proposition.matricule_candidat,
            annee_courante=annee_courante,
        )

        ComptabiliteValidatorList(
            a_frequente_recemment_etablissement_communaute_fr=(
                conditions_comptabilite.a_frequente_recemment_etablissement_communaute_fr
            ),
            comptabilite=proposition.comptabilite,
            pays_nationalite_ue=conditions_comptabilite.pays_nationalite_ue,
        ).validate()

    @classmethod
    def verifier_comptabilite_formation_generale(
        cls,
        proposition: PropositionGenerale,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_courante: int,
    ):
        conditions_comptabilite = profil_candidat_translator.get_conditions_comptabilite(
            matricule=proposition.matricule_candidat,
            annee_courante=annee_courante,
        )
        FormationGeneraleComptabiliteValidatorList(
            pays_nationalite_ue=conditions_comptabilite.pays_nationalite_ue,
            a_frequente_recemment_etablissement_communaute_fr=(
                conditions_comptabilite.a_frequente_recemment_etablissement_communaute_fr
            ),
            comptabilite=proposition.comptabilite,
        ).validate()
