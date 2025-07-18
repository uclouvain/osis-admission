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

from .accounting import (
    CompleterComptabilitePropositionDoctoraleCommandSerializer,
    CompleterComptabilitePropositionGeneraleCommandSerializer,
    DoctorateEducationAccountingDTOSerializer,
    GeneralEducationAccountingDTOSerializer,
)
from .approvals import (
    ApprouverPropositionCommandSerializer,
    ApprouverPropositionParPdfCommandSerializer,
    RefuserPropositionCommandSerializer,
)
from .campus import CampusSerializer
from .continuing_education import InformationsSpecifiquesFormationContinueDTOSerializer
from .coordonnees import CoordonneesSerializer
from .cotutelle import *
from .curriculum import (
    ContinuingEducationCompleterCurriculumCommandSerializer,
    CurriculumDetailsSerializer,
    DoctoratCompleterCurriculumCommandSerializer,
    EducationalExperienceYearSerializer,
    GeneralEducationCompleterCurriculumCommandSerializer,
    ProfessionalExperienceSerializer,
)
from .dashboard import DashboardSerializer
from .diplomatic_post import DiplomaticPostSerializer
from .doctorate import *
from .documents import *
from .exam import ExamSerializer
from .languages_knowledge import *
from .payment import *
from .pdf_recap import PDFRecapSerializer
from .person import *
from .person_last_enrolment import PersonLastEnrolmentSerializer
from .project import *
from .secondary_studies import HighSchoolDiplomaSerializer
from .specific_question import (
    ModifierQuestionsSpecifiquesFormationContinueCommandSerializer,
    ModifierQuestionsSpecifiquesFormationGeneraleCommandSerializer,
    SpecificQuestionSerializer,
)
from .submission import PropositionErrorsSerializer, SubmitPropositionSerializer
from .supervision import *
from .training_choice import (
    InitierPropositionContinueCommandSerializer,
    InitierPropositionGeneraleCommandSerializer,
    ModifierChoixFormationContinueCommandSerializer,
    ModifierChoixFormationGeneraleCommandSerializer,
    ModifierTypeAdmissionDoctoraleCommandSerializer,
)
