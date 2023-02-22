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

/**
 * Display the number of items selected
 */
$.fn.select2.amd.define('select2/multi-checkboxes/selection', [
    'select2/utils',
    'select2/selection/multiple',
    'select2/selection/placeholder',
    'select2/selection/single',
    'select2/selection/eventRelay',
  ],
  function (Utils, MultipleSelection, Placeholder, SingleSelection, EventRelay) {
    var adapter = Utils.Decorate(MultipleSelection, Placeholder);
    adapter = Utils.Decorate(adapter, EventRelay);

    adapter.prototype.render = function () {
      var $selection = SingleSelection.prototype.render.call(this);
      $selection.addClass('form-control');
      return $selection;
    };

    adapter.prototype.update = function (data) {
      var $rendered = this.$selection.find('.select2-selection__rendered');
      var formatted = '';

      if (data.length === 0) {
        formatted = this.options.get('placeholder') || '';
        $rendered.prop('title', formatted);
      } else {
        var itemsData = {
          selected: data || [],
          all: this.$element.find('option') || [],
        };
        formatted = this.display(itemsData, $rendered);
        // Display HTML on title with selected values on hover
        $rendered.prop('title', itemsData.selected.map(e => e.text).join(', '));
      }

      $rendered.empty().append(formatted);
    };

    return adapter;
  });

/**
 * A result adapter to display checkboxes as a state
 */
$.fn.select2.amd.define('select2/multi-checkboxes/results', [
    'jquery',
    'select2/utils',
    'select2/results',
  ],
  function ($, Utils, _Results) {
    function Results () {
      Results.__super__.constructor.apply(this, arguments);
    }

    Utils.Extend(Results, _Results);

    Results.prototype.highlightFirstItem = function () {
      /** This is a simpler version that __super__ */
      this.ensureHighlightVisible();
    };

    Results.prototype.bind = function (container) {
      container.on('open', function () {
        var $options = this.$results.find('.select2-results__option[aria-selected]');
        $options.filter('[aria-selected=true]').first().trigger('mouseenter');
      });

      Results.__super__.bind.apply(this, arguments);
    };

    Results.prototype.sort = function (data) {
      /** Sort first by common sorting function, then display selected results first */
      var sorter = this.options.get('sorter');
      var sortedData = sorter(data);

      return sortedData.filter(i => i.selected).concat(sortedData.filter(i => !i.selected));
    };

    Results.prototype.template = function (result, container) {
      /** Renders a single result */
      var template = this.options.get('templateResult');
      var escapeMarkup = this.options.get('escapeMarkup');

      var content = template(result, container);
      $(container).addClass('multi-checkboxes_wrap');

      if (content == null) {
        container.style.display = 'none';
      } else if (typeof content === 'string') {
        container.innerHTML = escapeMarkup(content);
      } else {
        $(container).append(content);
      }
    };

    return Results;
  });

/**
 * Decorate the dropdown to add SelectAll checkbox and resize
 */
$.fn.select2.amd.define('select2/multi-checkboxes/dropdown', [
    'jquery',
    'select2/utils',
    'select2/dropdown',
    'select2/dropdown/search',
    'select2/dropdown/attachBody',
  ],
  function ($, Utils, Dropdown, DropdownSearch, AttachBody) {
    function SelectAllDecorator (decorated, $element, options) {
      decorated.call(this, $element, options);
    }

    SelectAllDecorator.prototype.bind = function (decorated, container, $container) {
      var self = this;
      this.container = container;

      decorated.call(this, container, $container);

      this.$selectAllOption.text(container.options.options.selectAllLabel)

      // Bind selection events to update selectAll option label
      container.on('unselect', function () {
        self.$selectAllOption.text(container.options.options.selectAllLabel);
      });
      container.on('select', function () {
        container.dataAdapter.current(function (data) {
          var options = self.$element.find('option');
          if (data.length === options.length) {
            // All options selected, unselect all
            self.$selectAllOption.text(container.options.options.unselectAllLabel);
          }
        });
      });
    };

    SelectAllDecorator.prototype.render = function (decorated) {
      var self = this;
      var $dropdown = decorated.call(this);
      this.$dropdown.addClass('multi-checkboxes_dropdown');

      // Add a container to mimick result display
      var $selectAllContainer = $(`<span class="select2-results">
        <ul class="select2-results__options select2-results__selectall" aria-expanded="true" aria-hidden="false"></ul>
      </span>`);

      // Add selectAll option
      this.$selectAllOption = $('<li class="select2-results__option multi-checkboxes_wrap" aria-selected="false"></li>');
      this.$selectAllOption.on('mouseenter', function () {
        self.$selectAllOption.addClass('select2-results__option--highlighted');
      });
      this.$selectAllOption.on('mouseleave', function () {
        self.$selectAllOption.removeClass('select2-results__option--highlighted');
      });
      this.$selectAllOption.on('click', function () {
        // On click, select all, or unselect if all is selected
        var options = self.$element.find('option');
        self.container.dataAdapter.current(function (data) {
          // If all options selected, unselect all, else select all
          var eventName = (data.length === options.length) ? 'unselect' : 'select';
          $.map(options, o => self.container.trigger(eventName, { data: Utils.GetData(o, 'data') }));
        });
      });

      $selectAllContainer.find('ul').append(this.$selectAllOption);
      $dropdown.prepend($selectAllContainer);
      return $dropdown;
    };

    function ResizeDecorator (decorated, $element, options) {
      decorated.call(this, $element, options);
    }

    ResizeDecorator.prototype._resizeDropdown = function (decorated) {
      /** Set the max-width relative to dropdown parent's */
      decorated.call(this);

      if (this.options.get('dropdownAutoWidth')) {
        this.$dropdown.css('maxWidth', this.$dropdownParent.outerWidth(false) + 'px');
      }
    };

    return Utils.Decorate(
      Utils.Decorate(
        Utils.Decorate(
          Utils.Decorate(
            Dropdown,
            DropdownSearch,
          ),
          SelectAllDecorator,
        ),
        AttachBody,
      ),
      ResizeDecorator,
    );
  });

/**
 * Actually fire the select2 widget, based on function name (select2-multi-checkboxes)
 */
(function ($) {
  $.fn.select2.amd.require(
    [
      'select2/multi-checkboxes/dropdown',
      'select2/multi-checkboxes/selection',
      'select2/multi-checkboxes/results',
    ],
    function (DropdownAdapter, SelectionAdapter, ResultsAdapter) {
      $('[data-autocomplete-light-function=select2-multi-checkboxes]').each(function () {
        var $select = $(this);
        var dropdownParentSelector = $select.data('dropdownParentSelector');
        $select.select2({
          selectAllLabel: $select.data('selectAllLabel') ?? 'Select all',
          unselectAllLabel: $select.data('unselectAllLabel') ?? 'Unselect all',
          placeholder: $select.data('placeholder') ?? 'Select items',
          dropdownParent: (dropdownParentSelector && $(dropdownParentSelector)) ?? null,
          dropdownAutoWidth: $select.data('dropdownAutoWidth') ?? true,
          minimumResultsForSearch: $select.data('minimumResultsForSearch') ?? 10,
          closeOnSelect: false,
          templateSelection: function (data) {
            if ($select.data('selectionTemplate')) {
              return $select.data('selectionTemplate').replace('{items}', data.selected.length).replace('{total}', data.all.length);
            }
            return data.selected.length + ' items selected';
          },
          dropdownAdapter: DropdownAdapter,
          selectionAdapter: SelectionAdapter,
          resultsAdapter: ResultsAdapter,
        });
      });
    },
  );
}(jQuery));
