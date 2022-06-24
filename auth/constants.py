# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
# ############################################################################

# Association between a read-only tab name (path name) and a permission
READ_ACTIONS_BY_TAB = {
    # Personal data
    'coordonnees': 'admission.view_doctorateadmission_coordinates',
    'cotutelle': 'admission.view_doctorateadmission_cotutelle',
    'person': 'admission.view_doctorateadmission_person',
    # Previous experience
    'curriculum': 'admission.view_doctorateadmission_curriculum',
    'education': 'admission.view_doctorateadmission_secondary_studies',
    'languages': 'admission.view_doctorateadmission_languages',
    # Project
    'project': 'admission.view_doctorateadmission_project',
    'supervision': 'admission.view_doctorateadmission_supervision',
    # Confirmation paper
    'confirmation': 'admission.view_doctorateadmission_confirmation',
    'extension-request': 'admission.view_doctorateadmission_confirmation',
    # History
    'history': 'admission.view_historyentry',
    'history-all': 'admission.view_historyentry',
    # Mails
    'send-mail': 'admission.send_message',
    # Training
    'training': 'admission.change_activity',
}

# Association between a write-only tab name (path name) and a permission
UPDATE_ACTIONS_BY_TAB = {
    # Personal data
    'coordonnees': 'admission.change_doctorateadmission_coordinates',
    'cotutelle': 'admission.change_doctorateadmission_cotutelle',
    'person': 'admission.change_doctorateadmission_person',
    # Previous experience
    'curriculum': 'admission.change_doctorateadmission_curriculum',
    'education': 'admission.change_doctorateadmission_secondary_studies',
    'languages': 'admission.change_doctorateadmission_languages',
    # Project
    'project': 'admission.change_doctorateadmission_project',
    'supervision': 'admission.change_doctorateadmission_supervision',
    # Confirmation paper
    'confirmation': 'admission.change_doctorateadmission_confirmation',
    'extension-request': 'admission.change_doctorateadmission_confirmation_extension',
    # History
    'history': 'admission.change_historyentry',
    'history-all': 'admission.change_historyentry',
    # Mails
    'send-mail': 'admission.send_message',
    # Training
    'training': 'admission.change_activity',
}
