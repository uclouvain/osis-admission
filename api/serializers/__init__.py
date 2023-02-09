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

from .dashboard import DashboardSerializer
from .project import *
from .cotutelle import *
from .person import *
from .coordonnees import CoordonneesSerializer
from .secondary_studies import HighSchoolDiplomaSerializer
from .languages_knowledge import *
from .supervision import *
from .curriculum import (
    EducationalExperienceYearSerializer,
    CurriculumDetailsSerializer,
    ProfessionalExperienceSerializer,
    DoctoratCompleterCurriculumCommandSerializer,
    ContinuingEducationCompleterCurriculumCommandSerializer,
    GeneralEducationCompleterCurriculumCommandSerializer,
)
from .approvals import (
    ApprouverPropositionCommandSerializer,
    RefuserPropositionCommandSerializer,
    ApprouverPropositionParPdfCommandSerializer,
)
from .confirmation import *
from .doctorate import *
from .accounting import (
    DoctorateEducationAccountingDTOSerializer,
    GeneralEducationAccountingDTOSerializer,
    CompleterComptabilitePropositionDoctoraleCommandSerializer,
    CompleterComptabilitePropositionGeneraleCommandSerializer,
)
from .scholarship import ScholarshipSerializer
from .campus import CampusSerializer
from .training_choice import (
    InitierPropositionContinueCommandSerializer,
    InitierPropositionGeneraleCommandSerializer,
    ModifierChoixFormationContinueCommandSerializer,
    ModifierTypeAdmissionDoctoraleCommandSerializer,
    ModifierChoixFormationGeneraleCommandSerializer,
)
from .specific_question import (
    SpecificQuestionSerializer,
    ModifierQuestionsSpecifiquesFormationGeneraleCommandSerializer,
    ModifierQuestionsSpecifiquesFormationContinueCommandSerializer,
)
from .submission import PropositionErrorsSerializer, SubmitPropositionSerializer
