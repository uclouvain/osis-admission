/*
 *
 * OSIS stands for Open Student Information System. It's an application
 * designed to manage the core business of higher education institutions,
 * such as universities, faculties, institutes and professional schools.
 * The core business involves the administration of students, teachers,
 * courses, programs and so on.
 *
 * Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * A copy of this license - GNU General Public License - is available
 * at the root of the source code of this program.  If not,
 * see http://www.gnu.org/licenses/.
 *
 */

'use strict';
{
    window.AdmissionSelectFilter = {
        init: function(field_id) {
            const FILTERING_CLASS = 'hidden-option-when-filtering';
            const SELECTING_CLASS = 'hidden-option-when-selecting';

            // Original field
            const originalSelectField = document.getElementById(field_id);
            originalSelectField.classList.add('form-control')
            originalSelectField.size = 10;

            // Enable the desired functionalities depending on the specified parameters
            const withSearch = originalSelectField.dataset['withSearch'] === '1';
            const withFreeOptions = originalSelectField.dataset['withFreeOptions'] === '1';
            const freeOptionsPlaceholder = originalSelectField.dataset['freeOptionsPlaceholder'];

            // Add containers
            const parent = originalSelectField.parentNode;
            const fieldContainer = document.createElement('div');
            fieldContainer.className = 'admissionselectfilter-container'

            // Container containing the selectable options
            const fromSelectFieldContainer = document.createElement('fieldset')
            fromSelectFieldContainer.className = 'admissionselectfilter-selectable-container'

            const fromSelectFieldContainerLegend = document.createElement('legend');
            fromSelectFieldContainerLegend.innerText = gettext('Selectable items');

            fromSelectFieldContainer.appendChild(fromSelectFieldContainerLegend)

            // Container containing the selected options
            const originalSelectFieldContainer = document.createElement('fieldset')
            originalSelectFieldContainer.className = 'admissionselectfilter-selected-container'

            const originalSelectFieldContainerLegend = document.createElement('legend');
            originalSelectFieldContainerLegend.innerText = gettext('Selected items');

            originalSelectFieldContainer.appendChild(originalSelectFieldContainerLegend)

            parent.replaceChild(fieldContainer, originalSelectField);

            // Create a copy of the original select field that will contain the not selected values
            const fromSelectField = document.createElement('select');
            fromSelectField.innerHTML = originalSelectField.innerHTML;
            fromSelectField.id = `${originalSelectField.id}_from`;
            fromSelectField.multiple = true;
            fromSelectField.className = 'form-control';
            fromSelectField.size = originalSelectField.size;

            const displayOptGroupsWithContent = function(optGroups) {
                // Only display the optgroups that have visible options
                Array.from(optGroups).forEach(optGroup => {
                    if (optGroup.querySelector('option:not([class*=hidden-option-when-])') === null) {
                        optGroup.classList.add('hidden');
                    } else {
                        optGroup.classList.remove('hidden');
                    }
                });
            }

            fromSelectFieldContainer.appendChild(fromSelectField);
            originalSelectFieldContainer.appendChild(originalSelectField)

            if (withSearch) {
                // Add a search box allowing to filter options in the from select field
                const searchBox = document.createElement('input');
                searchBox.id = `${fromSelectField.id}_search`;
                searchBox.type = 'search';
                searchBox.placeholder = gettext('Search');
                searchBox.className = 'form-control';
                searchBox.title = gettext('Search an element in the list of the selectable items');

                searchBox.addEventListener('input', function(event) {
                    const regex = new RegExp(this.value, 'i')
                    Array.from(fromSelectField.options).forEach(option => {
                        if (regex.test(option.textContent)) {
                            option.classList.remove(FILTERING_CLASS);
                        } else {
                            option.classList.add(FILTERING_CLASS);
                        }
                    });
                    displayOptGroupsWithContent(fromOptGroups);
                });
                fromSelectField.before(searchBox);
            }

            if (withFreeOptions) {
                // Allow to add an option into the original select field
                const addOptionContainer = document.createElement('div');
                addOptionContainer.className = 'admissionselectfilter-add-option';

                const addOptionTextInput = document.createElement('input');
                addOptionTextInput.id = `${originalSelectField.id}_add_value`;
                addOptionTextInput.type = 'text';
                addOptionTextInput.className = 'form-control';
                addOptionTextInput.title = gettext('Add a personalized item in the list of the selected items');
                addOptionTextInput.placeholder = freeOptionsPlaceholder;

                const newElementsContainer = originalSelectField.querySelector('optgroup:last-child') || originalSelectField;

                const addOptionButton = document.createElement('input');
                addOptionButton.type = 'button';
                addOptionButton.value = '+';
                addOptionButton.className = 'btn';

                addOptionButton.addEventListener('click', function(event) {
                    // Add a new option value in the original select
                    const inputText = document.getElementById(addOptionTextInput.id);
                    const newOption = document.createElement('option');
                    const newOptionValue = inputText.value;

                    // Add the new option
                    newOption.value = newOptionValue;
                    newOption.text = newOptionValue;
                    newOption.title = newOptionValue;
                    newOption.selected = true;
                    newElementsContainer.appendChild(newOption);

                    // Reset input text
                    inputText.value = '';

                    // Show the optgroup if it's not already visible
                    displayOptGroupsWithContent([newElementsContainer]);
                    newOption.scrollIntoView();

                    // Prevent to submit the form
                    event.preventDefault()
                });

                addOptionContainer.appendChild(addOptionTextInput);
                addOptionContainer.appendChild(addOptionButton);
                originalSelectField.after(addOptionContainer);
            }

            fieldContainer.appendChild(fromSelectFieldContainer);
            fieldContainer.appendChild(originalSelectFieldContainer);

            const originalOptGroups = originalSelectField.querySelectorAll('optgroup');
            const fromOptGroups = fromSelectField.querySelectorAll('optgroup');

            for (let i = 0; i < originalSelectField.options.length; i++) {
                const originalOption = originalSelectField.options[i];
                const fromOption = fromSelectField.options[i];

                // If an option is selected, display it in the original select, otherwise, in the other one
                if (originalOption.selected) {
                    fromOption.classList.add(SELECTING_CLASS);
                } else {
                    originalOption.classList.add(SELECTING_CLASS);
                }

                fromOption.selected = false;

                // Display the option value on hover
                fromOption.title = fromOption.innerText;
                originalOption.title = originalOption.innerText;
            }

            if (withFreeOptions) {
                // The last optgroup contains the free options that are added from the input text so we just need it
                // in the original select
                fromSelectField.querySelector('optgroup:last-child').remove();
            }

            displayOptGroupsWithContent(originalOptGroups);
            displayOptGroupsWithContent(fromOptGroups);

            const onSelectOriginalOption = function(event) {
                // When a user wants to unselect an option, hide it in the original select and display it in the other one
                const targetedOptions = event.target.tagName === 'OPTION' ? [event.target] : event.target.tagName === 'SELECT' ? Array.from(event.target.selectedOptions) : [];

                if (targetedOptions.length === 0) return

                targetedOptions.forEach(option => {
                    // Original option
                    option.classList.add(SELECTING_CLASS);
                    option.selected = false;

                    // Cloned option
                    const fromOption = fromSelectField.querySelector(`option[value="${option.value}"]`);
                    if (fromOption !== null) {
                        fromOption.classList.remove(SELECTING_CLASS);
                    }
                });

                displayOptGroupsWithContent(originalOptGroups);
                displayOptGroupsWithContent(fromOptGroups);
            };
            const onSelectFromOption = function (event) {
                // When a user wants to select an option, display it in the original select and hide it in the other one
                const targetedOptions = event.target.tagName === 'OPTION' ? [event.target] : event.target.tagName === 'SELECT' ? Array.from(event.target.selectedOptions) : [];

                if (targetedOptions.length === 0) return

                let originalOption = null;

                targetedOptions.forEach(option => {
                    // Original option
                    originalOption = document.querySelector(`#${originalSelectField.id} option[value="${option.value}"]`);
                    originalOption.classList.remove(SELECTING_CLASS);
                    originalOption.selected = true;

                    // Cloned option
                    option.classList.add(SELECTING_CLASS);
                    option.selected = false;

                });

                displayOptGroupsWithContent(originalOptGroups);
                displayOptGroupsWithContent(fromOptGroups);

                originalOption.scrollIntoView()
            }

            // Add event listeners

            // On click
            originalSelectField.addEventListener('dblclick', event => onSelectOriginalOption(event));
            fromSelectField.addEventListener('dblclick', event => onSelectFromOption(event));

            // On key press
            fromSelectField.addEventListener('keydown', event => {
                if (event.key === 'Enter' || event.key === 'ArrowRight') onSelectFromOption(event)
            });
            originalSelectField.addEventListener('keydown', event => {
                if (event.key === 'Enter' || event.key === 'ArrowLeft') onSelectOriginalOption(event)
            });

            // On focus out of the original select, select every visible option to submit its value at form submission
            originalSelectField.addEventListener('focusout', () => {
                Array.from(document.getElementById(originalSelectField.id).options).forEach(option => {
                    if (!option.classList.contains(SELECTING_CLASS)) {
                        option.selected = true;
                    }
                })
            })
        },
    };

    // Initialize the selects
    window.addEventListener('load', function() {
        document.querySelectorAll('select.admissionselectfilter').forEach(function(el) {
            AdmissionSelectFilter.init(el.id);
        });
    });
}
