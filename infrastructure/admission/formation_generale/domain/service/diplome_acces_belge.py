# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.formation_generale.domain.model.enums import DiplomeAccesBelge
from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.service.i_diplome_acces_belge import IDiplomeAccesBelge
from admission.ddd.admission.shared_kernel.domain.service.i_deliberation_translator import IDeliberationTranslator
from admission.ddd.admission.shared_kernel.domain.service.i_inscriptions_translator import (
    IInscriptionsTranslatorService,
)
from admission.ddd.admission.shared_kernel.dtos import EtudesSecondairesAdmissionDTO
from admission.ddd.admission.shared_kernel.enums.type_demande import TypeDemande
from admission.models import GeneralEducationAdmission
from ddd.logic.deliberation.cloture.queries import RechercherDeliberationsProgrammesAnnuelsActeesQuery
from ddd.logic.deliberation.propositions.domain.model._decision import Decision
from ddd.logic.deliberation.propositions.domain.model._impact_progression import BAMA15
from ddd.logic.shared_kernel.profil.dtos.examens import ExamenDTO
from osis_profile.models import EXAM_TYPE_PREMIER_CYCLE_LABEL_FR, EducationalExperience, Exam, ProfessionalExperience
from osis_profile.models.education import HighSchoolDiploma
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience


class DiplomeAccesBelgeService(IDiplomeAccesBelge):
    @classmethod
    def est_diplome_acces_belge(
        cls,
        proposition: Proposition,
        type_demande: TypeDemande,
        etude_secondaire_dto: EtudesSecondairesAdmissionDTO,
        examen_dto: ExamenDTO,
        deliberation_translator: IDeliberationTranslator,
    ) -> DiplomeAccesBelge:
        admission = (
            GeneralEducationAdmission.objects.annotate_with_student_registration_id()
            .select_related('training__education_group_type')
            .get(uuid=proposition.entity_id.uuid)
        )
        deliberations = deliberation_translator.recuperer_deliberations(
            noma_etudiant=admission.student_registration_id,  # From annotation
        )
        high_school_diploma = HighSchoolDiploma.objects.filter(person=admission.candidate).first()
        exams = Exam.objects.select_related('type').filter(person=admission.candidate)
        professional_experiences = ProfessionalExperience.objects.filter(person=admission.candidate)
        educational_experiences = EducationalExperience.objects.filter(person=admission.candidate)

        est_en_poursuite = proposition.est_en_poursuite
        est_de_type_inscription = type_demande == TypeDemande.INSCRIPTION
        est_premier_cycle = admission.training.education_group_type.cycle == 1
        est_second_cycle = admission.training.education_group_type.cycle == 2
        a_secondaire_belge = etude_secondaire_dto.diplome_belge is not None
        a_examen_d_acces = bool(examen_dto.uuid)
        a_curext_valide_sans_secondaire = (
            all(
                professional_experience.validation_status == ChoixStatutValidationExperience.VALIDEE.name
                for professional_experience in professional_experiences
            )
            and all(
                educational_experience.validation_status == ChoixStatutValidationExperience.VALIDEE.name
                for educational_experience in educational_experiences
            )
            and all(
                exam.validation_status == ChoixStatutValidationExperience.VALIDEE.name
                for exam in exams
                if exam.type.label_fr != EXAM_TYPE_PREMIER_CYCLE_LABEL_FR
            )
        )
        a_secondaire_valide = (
            high_school_diploma is None
            or high_school_diploma.validation_status == ChoixStatutValidationExperience.VALIDEE.name
        ) and all(
            exam.validation_status == ChoixStatutValidationExperience.VALIDEE.name
            for exam in exams
            if exam.type.label_fr == EXAM_TYPE_PREMIER_CYCLE_LABEL_FR
        )
        a_diplome_uclouvain = any(
            deliberation.decision == Decision.REUSSITE.name
            or deliberation.etat_cycle_annualise.bama15 == BAMA15.EST_BAMA15.name
            for deliberation in deliberations
        )

        est_diplome_acces_belge = (
            not est_en_poursuite
            and est_de_type_inscription
            and (
                (est_premier_cycle and (a_secondaire_belge or a_examen_d_acces) and a_curext_valide_sans_secondaire)
                or (est_second_cycle and a_diplome_uclouvain and a_examen_d_acces and a_secondaire_valide)
            )
        )
        return DiplomeAccesBelge.OUI if est_diplome_acces_belge else DiplomeAccesBelge.NON
