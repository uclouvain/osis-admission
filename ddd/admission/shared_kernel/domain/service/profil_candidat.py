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
from typing import List, Optional

from admission.ddd.admission.doctorat.preparation.domain.service.verifier_curriculum import VerifierCurriculumDoctorat
from admission.ddd.admission.doctorat.preparation.domain.validator.validator_by_business_action import (
    ComptabiliteValidatorList,
    CurriculumPostSoumissionValidatorList,
    CurriculumValidatorList,
    ExperienceAcademiquePostSoumissionValidatorList,
    LanguesConnuesValidatorList,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.formation_continue.domain.validator.validator_by_business_actions import (
    FormationContinueCurriculumValidatorList,
)
from admission.ddd.admission.formation_generale.domain.model.enums import STATUTS_PROPOSITION_GENERALE_NON_SOUMISE
from admission.ddd.admission.formation_generale.domain.validator.validator_by_business_actions import (
    BachelierEtudesSecondairesValidatorList,
    ChoixFormationValidatorList,
    EtudesSecondairesValidatorList,
    ExamenValidatorList,
    FormationGeneraleComptabiliteValidatorList,
    FormationGeneraleCurriculumPostSoumissionValidatorList,
    FormationGeneraleCurriculumValidatorList,
    FormationGeneraleExperienceAcademiquePostSoumissionValidatorList,
    FormationGeneraleInformationsComplementairesValidatorList,
)
from admission.ddd.admission.shared_kernel.domain.model._candidat_adresse import CandidatAdresse
from admission.ddd.admission.shared_kernel.domain.model._candidat_signaletique import CandidatSignaletique
from admission.ddd.admission.shared_kernel.domain.model.formation import Formation
from admission.ddd.admission.shared_kernel.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.shared_kernel.domain.service.verifier_curriculum import VerifierCurriculum
from admission.ddd.admission.shared_kernel.domain.service.i_annee_inscription_formation import (
    IAnneeInscriptionFormationTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_diffusion_notes_translator import IDiffusionNotesTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_evaluations_translator import (
    IInscriptionsEvaluationsTranslator,
)
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.domain.service.i_noma_translator import INomasTranslator
from admission.ddd.admission.shared_kernel.domain.service.inscriptions_ucl_candidat import (
    InscriptionsUCLCandidatService,
)
from admission.ddd.admission.shared_kernel.domain.validator.validator_by_business_action import (
    CoordonneesValidatorList,
    IdentificationValidatorList,
    QuarantaineValidatorList,
)
from admission.ddd.admission.shared_kernel.dtos.formation import FormationDTO
from admission.ddd.admission.shared_kernel.enums.valorisation_experience import ExperiencesCVRecuperees
from base.models.enums.community import CommunityEnum
from base.models.enums.education_group_types import TrainingType
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear
from ddd.logic.shared_kernel.profil.domain.enums import TypeExperience
from ddd.logic.shared_kernel.profil.domain.service.i_parcours_interne import IExperienceParcoursInterneTranslator
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import ExperienceAcademiqueDTO
from osis_common.ddd import interface
from reference.models.enums.cycle import Cycle


class ProfilCandidat(interface.DomainService):
    @classmethod
    def verifier_identification(
        cls,
        matricule: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        candidat_est_inscrit_recemment_ucl: bool,
    ) -> None:
        if candidat_est_inscrit_recemment_ucl:
            return

        identification = profil_candidat_translator.get_identification(matricule)
        IdentificationValidatorList(
            identite_signaletique=CandidatSignaletique(
                annee_naissance=identification.annee_naissance,
                date_naissance=identification.date_naissance,
                pays_nationalite=identification.pays_nationalite,
                photo_identite=identification.photo_identite,
                prenom=identification.prenom,
                autres_prenoms=identification.autres_prenoms,
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
            date_expiration_passeport=identification.date_expiration_passeport,
            date_expiration_carte_identite=identification.date_expiration_carte_identite,
            passeport=identification.passeport,
            noma_derniere_inscription_ucl=identification.noma_derniere_inscription_ucl,
            annee_derniere_inscription_ucl=identification.annee_derniere_inscription_ucl,
            pays_residence=identification.pays_residence,
        ).validate()

    @classmethod
    def verifier_coordonnees(cls, matricule: str, profil_candidat_translator: 'IProfilCandidatTranslator') -> None:
        coordonnees = profil_candidat_translator.get_coordonnees(matricule)

        CoordonneesValidatorList(
            adresse_email_privee=coordonnees.adresse_email_privee,
            numero_telephone_mobile=coordonnees.numero_mobile,
            domicile_legal=(
                CandidatAdresse(
                    code_postal=coordonnees.domicile_legal.code_postal,
                    ville=coordonnees.domicile_legal.ville,
                    pays=coordonnees.domicile_legal.pays,
                    rue=coordonnees.domicile_legal.rue,
                    numero=coordonnees.domicile_legal.numero_rue,
                )
                if coordonnees.domicile_legal
                else None
            ),
            adresse_correspondance=(
                CandidatAdresse(
                    code_postal=coordonnees.adresse_correspondance.code_postal,
                    ville=coordonnees.adresse_correspondance.ville,
                    pays=coordonnees.adresse_correspondance.pays,
                    rue=coordonnees.adresse_correspondance.rue,
                    numero=coordonnees.adresse_correspondance.numero_rue,
                )
                if coordonnees.adresse_correspondance
                else None
            ),
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
        etudes_secondaires = profil_candidat_translator.get_etudes_secondaires(matricule)

        if formation.type == TrainingType.BACHELOR:
            if not etudes_secondaires.valorisation.diplome_est_modifiable(
                diplome=etudes_secondaires.experience,
                formation=formation.type.name,
            ):
                return

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
            # Des études secondaires valorisées par une admission sont considérées valides pour les futures admissions
            if etudes_secondaires.valorisation.est_valorise:
                return

            EtudesSecondairesValidatorList(
                diplome_etudes_secondaires=etudes_secondaires.diplome_etudes_secondaires,
                annee_diplome_etudes_secondaires=etudes_secondaires.annee_diplome_etudes_secondaires,
            ).validate()

    @classmethod
    def verifier_examens(
        cls,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        uuid_experience: str = None,
        matricule: str = None,
        sigle_formation: str = None,
        annee_formation: int = None,
        uuid_proposition: str = None,
    ) -> None:
        examen = profil_candidat_translator.get_examen(
            uuid_experience,
            matricule,
            sigle_formation,
            annee_formation,
            uuid_proposition,
        )

        ExamenValidatorList(
            requis=examen.requis,
            attestation=examen.attestation,
            annee=examen.annee,
        ).validate()

    @classmethod
    def verifier_curriculum(
        cls,
        matricule: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_courante: int,
        curriculum_pdf: List[str],
        uuid_proposition: str,
        annee_formation: AcademicYear,
    ) -> None:
        curriculum = profil_candidat_translator.get_curriculum(
            matricule=matricule,
            annee_courante=annee_courante,
            uuid_proposition=uuid_proposition,
        )

        experiences_academiques_incompletes = VerifierCurriculumDoctorat.recuperer_experiences_academiques_incompletes(
            experiences=curriculum.experiences_academiques,
        )

        CurriculumValidatorList(
            annee_courante=annee_courante,
            experiences_academiques=curriculum.experiences_academiques,
            experiences_academiques_incompletes=experiences_academiques_incompletes,
            annee_diplome_etudes_secondaires=curriculum.annee_diplome_etudes_secondaires,
            annee_alternative_diplome_etudes_secondaires=curriculum.annee_alternative_diplome_etudes_secondaires,
            annee_derniere_inscription_ucl=curriculum.annee_derniere_inscription_ucl,
            fichier_pdf=curriculum_pdf,
            experiences_non_academiques=curriculum.experiences_non_academiques,
            annee_formation=annee_formation,
        ).validate()

    @classmethod
    def verifier_curriculum_formation_generale(
        cls,
        proposition,
        type_formation: TrainingType,
        annee_courante: int,
        annee_formation: AcademicYear,
        curriculum: CurriculumAdmissionDTO,
    ) -> None:
        experiences_academiques_incompletes = VerifierCurriculum.recuperer_experiences_academiques_incompletes(
            experiences=curriculum.experiences_academiques,
        )

        FormationGeneraleCurriculumValidatorList(
            annee_courante=annee_courante,
            experiences_academiques=curriculum.experiences_academiques,
            experiences_academiques_incompletes=experiences_academiques_incompletes,
            annee_diplome_etudes_secondaires=curriculum.annee_diplome_etudes_secondaires,
            annee_alternative_diplome_etudes_secondaires=curriculum.annee_alternative_diplome_etudes_secondaires,
            annee_derniere_inscription_ucl=curriculum.annee_derniere_inscription_ucl,
            fichier_pdf=proposition.curriculum,
            experiences_non_academiques=curriculum.experiences_non_academiques,
            type_formation=type_formation,
            equivalence_diplome=proposition.equivalence_diplome,
            sigle_formation=proposition.formation_id.sigle,
            annee_formation=annee_formation,
        ).validate()

    @classmethod
    def verifier_curriculum_formation_generale_apres_soumission(
        cls,
        proposition,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        experience_parcours_interne_translator: 'IExperienceParcoursInterneTranslator',
        verification_experiences_completees: bool,
        grade_academique_formation_proposition: str,
        annee_formation: AcademicYear,
        curriculum_dto: Optional[CurriculumAdmissionDTO] = None,
    ) -> None:
        date_soumission = proposition.soumise_le.date()
        annee_precedent_formation = proposition.formation_id.annee - 1

        experiences_parcours_interne = experience_parcours_interne_translator.recuperer(
            matricule=proposition.matricule_candidat,
            avec_credits=False,
        )

        curriculum = (
            profil_candidat_translator.get_curriculum(
                matricule=proposition.matricule_candidat,
                annee_courante=annee_precedent_formation,
                uuid_proposition=proposition.entity_id.uuid,
                experiences_cv_recuperees=ExperiencesCVRecuperees.SEULEMENT_VALORISEES,
            )
            if curriculum_dto is None
            else curriculum_dto
        )

        FormationGeneraleCurriculumPostSoumissionValidatorList(
            date_soumission=date_soumission,
            annee_precedent_formation=annee_precedent_formation,
            experiences_academiques=curriculum.experiences_academiques,
            annee_diplome_etudes_secondaires=curriculum.annee_diplome_etudes_secondaires,
            annee_alternative_diplome_etudes_secondaires=curriculum.annee_alternative_diplome_etudes_secondaires,
            experiences_non_academiques=curriculum.experiences_non_academiques,
            experiences_parcours_interne=experiences_parcours_interne,
            verification_experiences_completees=verification_experiences_completees,
            grade_academique_formation_proposition=grade_academique_formation_proposition,
            annee_formation=annee_formation,
        ).validate()

    @classmethod
    def verifier_experience_academique_curriculum_apres_soumission(
        cls,
        uuid_experience: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        grade_academique_formation: str,
        proposition_id,
        matricule_candidat: str,
    ) -> None:
        experience = profil_candidat_translator.get_experience_academique(
            matricule=matricule_candidat,
            uuid_proposition=proposition_id.uuid,
            uuid_experience=uuid_experience,
        )

        ExperienceAcademiquePostSoumissionValidatorList(
            experience_academique=experience,
            grade_academique_formation_proposition=grade_academique_formation,
        ).validate()

    @classmethod
    def verifier_experience_academique_curriculum(
        cls,
        uuid_experience: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        grade_academique_formation: str,
    ) -> None:
        experience = profil_candidat_translator.get_experience_academique(uuid_experience=uuid_experience)

        ExperienceAcademiquePostSoumissionValidatorList(
            experience_academique=experience,
            grade_academique_formation_proposition=grade_academique_formation,
        ).validate()

    @classmethod
    def verifier_experience_curriculum_formation_generale_apres_soumission(
        cls,
        proposition,
        uuid_experience: str,
        type_experience: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        grade_academique_formation_proposition: str,
    ) -> None:
        if type_experience == TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name:
            experience = profil_candidat_translator.get_experience_academique(
                matricule=proposition.matricule_candidat,
                uuid_proposition=proposition.entity_id.uuid,
                uuid_experience=uuid_experience,
            )

            FormationGeneraleExperienceAcademiquePostSoumissionValidatorList(
                experience_academique=experience,
                grade_academique_formation_proposition=grade_academique_formation_proposition,
            ).validate()

    @classmethod
    def verifier_experience_curriculum_formation_doctorale_apres_soumission(
        cls,
        proposition,
        uuid_experience: str,
        type_experience: str,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        grade_academique_formation_proposition: str,
    ) -> None:
        if type_experience == TypeExperience.FORMATION_ACADEMIQUE_EXTERNE.name:
            experience = profil_candidat_translator.get_experience_academique(
                matricule=proposition.matricule_candidat,
                uuid_proposition=proposition.entity_id.uuid,
                uuid_experience=uuid_experience,
            )

            ExperienceAcademiquePostSoumissionValidatorList(
                experience_academique=experience,
                grade_academique_formation_proposition=grade_academique_formation_proposition,
            ).validate()

    @classmethod
    def verifier_curriculum_formation_doctorale_apres_soumission(
        cls,
        proposition,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        experience_parcours_interne_translator: 'IExperienceParcoursInterneTranslator',
        verification_experiences_completees: bool,
        grade_academique_formation_proposition: str,
        annee_formation: AcademicYear,
        curriculum_dto: Optional[CurriculumAdmissionDTO] = None,
    ) -> None:
        # Le CV est soumis lors de l'envoi de la demande des signatures
        date_soumission = proposition.derniere_demande_signature_avant_soumission_le.date()

        annee_precedent_formation = proposition.formation_id.annee - 1

        experiences_parcours_interne = experience_parcours_interne_translator.recuperer(
            matricule=proposition.matricule_candidat,
            avec_credits=False,
        )

        curriculum = (
            profil_candidat_translator.get_curriculum(
                matricule=proposition.matricule_candidat,
                annee_courante=annee_precedent_formation,
                uuid_proposition=proposition.entity_id.uuid,
                experiences_cv_recuperees=ExperiencesCVRecuperees.SEULEMENT_VALORISEES,
            )
            if curriculum_dto is None
            else curriculum_dto
        )

        CurriculumPostSoumissionValidatorList(
            date_soumission=date_soumission,
            annee_precedent_formation=annee_precedent_formation,
            experiences_academiques=curriculum.experiences_academiques,
            annee_diplome_etudes_secondaires=curriculum.annee_diplome_etudes_secondaires,
            annee_alternative_diplome_etudes_secondaires=curriculum.annee_alternative_diplome_etudes_secondaires,
            experiences_non_academiques=curriculum.experiences_non_academiques,
            experiences_parcours_interne=experiences_parcours_interne,
            verification_experiences_completees=verification_experiences_completees,
            grade_academique_formation_proposition=grade_academique_formation_proposition,
            annee_formation=annee_formation,
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
        proposition,
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
        proposition,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        annee_courante: int,
        formation: Formation,
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
            formation=formation,
        ).validate()

    @classmethod
    def verifier_choix_formation_generale(
        cls,
        proposition,
        formation: Formation,
        annee_inscription_formation_translator: IAnneeInscriptionFormationTranslator,
        inscriptions_translator: IInscriptionsTranslatorService,
        deliberation_translator: IDeliberationTranslator,
        diffusion_notes_translator: IDiffusionNotesTranslator,
        inscriptions_evaluations_translator: IInscriptionsEvaluationsTranslator,
        nomas_translator: INomasTranslator,
    ):
        candidat_est_eligible_a_la_reinscription = InscriptionsUCLCandidatService.est_eligible_a_la_reinscription(
            matricule_candidat=proposition.matricule_candidat,
            annee_inscription_formation_translator=annee_inscription_formation_translator,
            inscriptions_translator=inscriptions_translator,
            deliberation_translator=deliberation_translator,
            diffusion_notes_translator=diffusion_notes_translator,
            inscriptions_evaluations_translator=inscriptions_evaluations_translator,
        )
        candidat_est_diplome_formation = InscriptionsUCLCandidatService.est_diplome(
            matricule_candidat=proposition.matricule_candidat,
            sigle_formation=formation.entity_id.sigle,
            deliberation_translator=deliberation_translator,
            nomas_translator=nomas_translator,
        )
        ChoixFormationValidatorList(
            proposition=proposition,
            formation=formation,
            candidat_est_eligible_a_la_reinscription=candidat_est_eligible_a_la_reinscription,
            candidat_est_diplome_formation=candidat_est_diplome_formation,
        ).validate()

    @classmethod
    def verifier_informations_complementaires_formation_generale(
        cls,
        proposition,
        profil_candidat_translator: 'IProfilCandidatTranslator',
        experiences_academiques: list[ExperienceAcademiqueDTO],
        formation: Formation,
    ):
        identification = profil_candidat_translator.get_identification(proposition.matricule_candidat)
        est_potentiellement_concerne_par_le_bama_15 = cls.est_potentiellement_concerne_par_le_bama_15(
            uuid_proposition=proposition.entity_id.uuid,
            statut_proposition=proposition.statut.name,
            annee_formation=proposition.annee_calculee or proposition.formation_id.annee,
            experiences_academiques=experiences_academiques,
            formation=formation,
        )

        FormationGeneraleInformationsComplementairesValidatorList(
            poste_diplomatique=proposition.poste_diplomatique,
            pays_nationalite=identification.pays_nationalite,
            pays_nationalite_europeen=identification.pays_nationalite_europeen,
            pays_residence=identification.pays_residence,
            experiences_academiques=experiences_academiques,
            est_potentiellement_concerne_par_le_bama_15=est_potentiellement_concerne_par_le_bama_15,
            est_concerne_par_le_bama_15=proposition.est_concerne_par_le_bama_15,
            preuve_bama_15=proposition.preuve_bama_15,
        ).validate()

    @classmethod
    def verifier_quarantaine(
        cls,
        proposition,
        profil_candidat_translator: 'IProfilCandidatTranslator',
    ):
        merge_proposal = profil_candidat_translator.get_merge_proposal(proposition.matricule_candidat)
        QuarantaineValidatorList(
            merge_proposal=merge_proposal,
        ).validate()

    @classmethod
    def est_potentiellement_concerne_par_le_bama_15(
        cls,
        uuid_proposition: str,
        annee_formation: int,
        statut_proposition: str,
        formation: Formation | FormationDTO,
        experiences_academiques: list[ExperienceAcademiqueDTO],
    ):
        demande_non_soumise = statut_proposition in STATUTS_PROPOSITION_GENERALE_NON_SOUMISE
        annee_precedent_formation = annee_formation - 1
        return formation.est_formation_pour_bama_15 and any(
            (demande_non_soumise or xp.valorisee_par_admissions and uuid_proposition in xp.valorisee_par_admissions)
            and xp.cycle_formation == Cycle.FIRST_CYCLE.name
            and xp.communaute_institut == CommunityEnum.FRENCH_SPEAKING.name
            and not xp.a_obtenu_diplome
            and not xp.formation_non_selectionnee_dans_liste_de_reference
            and any(annee for annee in xp.annees if annee.annee == annee_precedent_formation)
            for xp in experiences_academiques
        )
