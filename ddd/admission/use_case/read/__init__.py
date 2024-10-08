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
from .lister_demandes_service import lister_demandes
from .recuperer_connaissances_langues_service import recuperer_connaissances_langues
from .recuperer_etudes_secondaires_service import recuperer_etudes_secondaires
from .recuperer_experience_academique_service import recuperer_experience_academique
from .recuperer_experience_non_academique_service import recuperer_experience_non_academique
from .recuperer_questions_specifiques_proposition_service import recuperer_questions_specifiques_proposition
from .recuperer_titres_acces_selectionnables_proposition_service import (
    recuperer_titres_acces_selectionnables_proposition,
)
