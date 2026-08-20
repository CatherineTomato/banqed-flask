/*
 * BANQED — Wardrobe and Sales table engine.
 *
 * This is one file on purpose. It contains two parts:
 *
 *   1. BanqDropdown: the searchable menu used for sort, sale status and both
 *      filter pickers. It is the same control the Lodge an Item form uses, so
 *      every menu in the app looks and behaves identically.
 *   2. The table engine: search, filters, sorting and inline editing.
 *
 * Keeping them together means the pages have a single script to load and no
 * cross-file dependency that can half-arrive and leave the page inert.
 *
 * Rows are rendered server-side carrying their values in data-* attributes,
 * so searching, filtering and sorting all happen in the page with no network
 * round trip. Only edits talk to the server, through POST /api/items/<id>.
 */
 
/* ==========================================================================
   Part 1 — BanqDropdown
    */
 
(function (global) {
  "use strict";
 
  const instances = [];
 
  function BanqDropdown(host, config) {
    const options = (config.options || []).slice();
    const multi = Boolean(config.multi);
    const allowAdd = Boolean(config.allowAdd);
    const placeholder = config.placeholder || "Select";
    const searchPlaceholder = config.searchPlaceholder || "Search\u2026";
    const onChange = config.onChange || function () {};
 
    let selected = multi
      ? (config.value || []).slice()
      : (config.value || "");
    let query = "";
    let activeIndex = -1; // which option the arrow keys are pointing at
 
    host.classList.add("dropdown");
    host.innerHTML = "";
 
    const control = document.createElement("div");
    control.className = "dropdown__control";
 
    const input = document.createElement("input");
    input.type = "text";
    input.className = "dropdown__input";
    input.readOnly = true;
    input.autocomplete = "off";
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-expanded", "false");
    if (config.ariaLabel) input.setAttribute("aria-label", config.ariaLabel);
 
    const chevron = document.createElement("span");
    chevron.className = "dropdown__chevron";
    chevron.setAttribute("aria-hidden", "true");
 
    control.appendChild(input);
    control.appendChild(chevron);
 
    const panel = document.createElement("div");
    panel.className = "dropdown__panel";
    panel.hidden = true;
 
    const list = document.createElement("div");
    list.className = "dropdown__options";
    list.setAttribute("role", "listbox");
    panel.appendChild(list);
 
    if (multi) {
      const footer = document.createElement("div");
      footer.className = "dropdown__footer";
      const done = document.createElement("button");
      done.type = "button";
      done.className = "dropdown__done";
      done.textContent = "Done";
      done.addEventListener("mousedown", function (event) {
        event.preventDefault();
        close();
      });
      footer.appendChild(done);
      panel.appendChild(footer);
    }
 
    host.appendChild(control);
    host.appendChild(panel);
 
    // ------------------------------------------------ rendering
 
    function renderValue() {
      input.value = multi ? selected.join(", ") : selected;
      input.placeholder = placeholder;
    }
 
    function renderOptions() {
      list.innerHTML = "";
      const needle = query.trim().toLowerCase();
      const matches = options.filter((o) => o.toLowerCase().includes(needle));
 
      if (matches.length === 0) {
        const wrap = document.createElement("div");
        wrap.className = "dropdown__empty";
 
        const message = document.createElement("p");
        message.className = "dropdown__emptytext";
        message.textContent = query.trim()
          ? `No matches for "${query.trim()}"`
          : "Nothing here yet";
        wrap.appendChild(message);
 
        if (allowAdd && query.trim()) {
          const add = document.createElement("button");
          add.type = "button";
          add.className = "dropdown__addnew";
          add.textContent = `+ Add "${query.trim()}"`;
          add.addEventListener("mousedown", function (event) {
            event.preventDefault();
            addValue(query.trim());
          });
          wrap.appendChild(add);
        }
 
        list.appendChild(wrap);
        return;
      }
 
      matches.forEach(function (option, index) {
        const isOn = multi ? selected.includes(option) : selected === option;
        const row = document.createElement("div");
        row.className = "dropdown__option" + (isOn ? " is-selected" : "");
        if (index === activeIndex) row.classList.add("is-active");
        row.setAttribute("role", "option");
        row.setAttribute("aria-selected", isOn ? "true" : "false");
        row.textContent = option;
        row.addEventListener("mousedown", function (event) {
          event.preventDefault();
          pick(option);
        });
        list.appendChild(row);
      });
    }
 
    // --------------------------------------------------- behaviour
 
    function pick(option) {
      if (multi) {
        const at = selected.indexOf(option);
        if (at >= 0) selected.splice(at, 1);
        else selected.push(option);
        renderOptions();
        // Reflect the running selection even while the menu is open, so it's
        // clear what has been chosen before Done is pressed.
        input.placeholder = selected.length
          ? selected.join(", ")
          : searchPlaceholder;
        onChange(selected.slice());
        return;
      }
      selected = option;
      onChange(selected);
      close();
    }
 
    function addValue(value) {
      if (!options.some((o) => o.toLowerCase() === value.toLowerCase())) {
        options.push(value);
      }
      pick(options.find((o) => o.toLowerCase() === value.toLowerCase()));
      query = "";
      input.value = "";
      renderOptions();
    }
 
    function open() {
      closeAll();
      query = "";
      activeIndex = -1;
      input.readOnly = false;
      input.value = "";
      input.placeholder = searchPlaceholder;
      input.setAttribute("aria-expanded", "true");
      panel.hidden = false;
      renderOptions();
      input.focus();
    }
 
    function close() {
      query = "";
      input.readOnly = true;
      input.setAttribute("aria-expanded", "false");
      panel.hidden = true;
      renderValue();
    }
 
    input.addEventListener("mousedown", function (event) {
      if (!panel.hidden) return;
      event.preventDefault();
      open();
    });
 
    input.addEventListener("input", function () {
      query = input.value;
      activeIndex = -1; // the match list changed, so the old highlight is stale
      renderOptions();
    });
 
    input.addEventListener("keydown", function (event) {
      // Closed menu: Enter, Space or ArrowDown opens it from the keyboard.
      if (panel.hidden) {
        if (event.key === "Enter" || event.key === " " || event.key === "ArrowDown") {
          event.preventDefault();
          open();
        }
        return;
      }

      // Open menu: arrows move the highlight, Enter picks it, Escape closes,
      // Tab closes and lets focus move on to the next field.
      const optionRows = list.querySelectorAll(".dropdown__option");

      if (event.key === "Escape") {
        event.preventDefault();
        close();
      } else if (event.key === "Tab") {
        close();
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        activeIndex = Math.min(activeIndex + 1, optionRows.length - 1);
        renderOptions();
        const active = list.querySelector(".is-active");
        if (active) active.scrollIntoView({ block: "nearest" });
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        activeIndex = Math.max(activeIndex - 1, 0);
        renderOptions();
        const active = list.querySelector(".is-active");
        if (active) active.scrollIntoView({ block: "nearest" });
      } else if (event.key === "Enter") {
        event.preventDefault();
        const target = optionRows[activeIndex] || optionRows[0];
        if (target) pick(target.textContent);
        else if (allowAdd && query.trim()) addValue(query.trim());
      }
    });
 
    renderValue();
    renderOptions();
 
    const api = {
      element: host,
      close: close,
      getValue: function () {
        return multi ? selected.slice() : selected;
      },
      setValue: function (value) {
        selected = multi ? (value || []).slice() : (value || "");
        renderValue();
        renderOptions();
      },
      setOptions: function (next) {
        options.length = 0;
        (next || []).forEach((o) => options.push(o));
        renderOptions();
      }
    };
 
    instances.push(api);
    return api;
  }
 
  function closeAll() {
    instances.forEach((instance) => instance.close());
  }
 
  // Capture phase: an option's own handler re-renders the list, detaching the
  // clicked node, so a bubble-phase check would see it as outside the menu
  // and close the very panel that click was meant to use.
  document.addEventListener("mousedown", function (event) {
    if (!event.target.closest(".dropdown")) closeAll();
  }, true);
 
  global.BanqDropdown = BanqDropdown;
  global.BanqDropdown.closeAll = closeAll;
})(window);
 
 
/* ==========================================================================
   Part 2 — Table engine
    */
 
(function () {
  "use strict";
 
  const root = document.querySelector("[data-table-root]");
  if (!root) return;
 
  const page = root.dataset.page;
  const tbody = root.querySelector("[data-rows]");
  const rows = () => Array.from(tbody.querySelectorAll("[data-row]"));
 
  const searchInput = root.querySelector("[data-search]");
  const filterTrigger = root.querySelector("[data-filter-trigger]");
  const filterPanel = root.querySelector("[data-filter-panel]");
  const filterFieldHost = root.querySelector("[data-filter-field]");
  const filterValueHost = root.querySelector("[data-filter-value]");
  const filterAdd = root.querySelector("[data-filter-add]");
  const filterMin = root.querySelector("[data-filter-min]");
  const filterMax = root.querySelector("[data-filter-max]");
  const filterRangeApply = root.querySelector("[data-filter-range-apply]");
  const filterClear = root.querySelector("[data-filter-clear]");
  const sortHost = root.querySelector("[data-sort]");
  const showSold = root.querySelector("[data-show-sold]");
  const tokenBar = root.querySelector("[data-tokens]");
  const countLabel = root.querySelector("[data-count]");
  const valueLabel = root.querySelector("[data-total-value]");
  const revenueLabel = root.querySelector("[data-revenue]");
  const listedLabel = root.querySelector("[data-listed-value]");
  const emptyState = root.querySelector("[data-empty]");
 
  const FIELD_OPTIONS = JSON.parse(root.dataset.fieldOptions || "{}");
  const FILTER_FIELDS = JSON.parse(root.dataset.filterFields || "[]");
  const SALE_STATUSES = JSON.parse(root.dataset.saleStatuses || "[]");
 
  const labelByField = {};
  FILTER_FIELDS.forEach((f) => { labelByField[f.field] = f.label; });
 
  // field -> [values]; several values on one field match any of them
  const filters = {};
  let valueRange = { min: "", max: "" };
 
  const money = (n) => "\u20AC" + Math.round(n).toLocaleString();
 
  // --------------------------------------- matching
 
  function rowValues(row, field) {
    const key = field.replace(/_([a-z])/g, (m, c) => c.toUpperCase());
    return (row.dataset[key] || "").split("|").map((v) => v.trim()).filter(Boolean);
  }
 
  function matchesFilters(row) {
    return Object.keys(filters).every(function (field) {
      const wanted = filters[field];
      if (!wanted.length) return true;
      return rowValues(row, field).some((value) => wanted.includes(value));
    });
  }
 
  function matchesRange(row) {
    const value = Number(row.dataset.estimatedValue || 0);
    const min = valueRange.min === "" ? null : Number(valueRange.min);
    const max = valueRange.max === "" ? null : Number(valueRange.max);
    if (min !== null && value < min) return false;
    if (max !== null && value > max) return false;
    return true;
  }
 
  function matchesSearch(row) {
    const query = (searchInput ? searchInput.value : "").trim().toLowerCase();
    if (!query) return true;
    return (row.dataset.searchBlob || "").includes(query);
  }
 
  // Sold items are finished business, hidden until asked for.
  function matchesSoldVisibility(row) {
    if (page !== "sales" || !showSold) return true;
    if (showSold.checked) return true;
    return row.dataset.isSold !== "true";
  }
 
  /* Every figure in the header describes what is on screen right now, so
     filtering to black dresses shows the count and value of black dresses. */
  function apply() {
    let visible = 0;
    let totalValue = 0;
    let revenue = 0;
    let listedValue = 0;
 
    rows().forEach(function (row) {
      const show = matchesFilters(row) && matchesRange(row) &&
        matchesSearch(row) && matchesSoldVisibility(row);
      row.hidden = !show;
 
      const detail = row.nextElementSibling;
      if (detail && detail.hasAttribute("data-detail-row") && !show) {
        detail.hidden = true;
        row.classList.remove("is-expanded");
      }
 
      if (!show) return;
 
      visible += 1;
      totalValue += Number(row.dataset.estimatedValue || 0);
      if (row.dataset.isSold === "true") {
        revenue += Number(row.dataset.soldFor || 0);
      } else {
        listedValue += Number(row.dataset.listingPrice || 0);
      }
    });
 
    if (countLabel) countLabel.textContent = visible.toLocaleString();
    if (valueLabel) valueLabel.textContent = money(totalValue);
    if (revenueLabel) revenueLabel.textContent = money(revenue);
    if (listedLabel) listedLabel.textContent = money(listedValue);
    if (emptyState) emptyState.hidden = visible !== 0;
  }
 
  //------------------ tokens
 
  function renderTokens() {
    if (!tokenBar) return;
    tokenBar.innerHTML = "";
 
    Object.keys(filters).forEach(function (field) {
      filters[field].forEach(function (value) {
        const label = (labelByField[field] || field) + ": " + value;
        tokenBar.appendChild(makeToken(label, function () {
          filters[field] = filters[field].filter((v) => v !== value);
          if (!filters[field].length) delete filters[field];
          renderTokens();
          apply();
        }));
      });
    });
 
    if (valueRange.min !== "" || valueRange.max !== "") {
      const min = valueRange.min === "" ? "0" : valueRange.min;
      const max = valueRange.max === "" ? "any" : valueRange.max;
      tokenBar.appendChild(makeToken(`Value: \u20AC${min}\u2013${max}`, function () {
        valueRange = { min: "", max: "" };
        if (filterMin) filterMin.value = "";
        if (filterMax) filterMax.value = "";
        renderTokens();
        apply();
      }));
    }
 
    if (searchInput && searchInput.value.trim()) {
      tokenBar.appendChild(makeToken(`Search: ${searchInput.value.trim()}`, function () {
        searchInput.value = "";
        renderTokens();
        apply();
      }));
    }
 
    tokenBar.hidden = tokenBar.children.length === 0;
  }
 
  function makeToken(text, onRemove) {
    const token = document.createElement("button");
    token.type = "button";
    token.className = "token";
    token.setAttribute("aria-label", "Remove filter " + text);
 
    const label = document.createElement("span");
    label.textContent = text;
 
    const cross = document.createElement("span");
    cross.className = "token__x";
    cross.setAttribute("aria-hidden", "true");
    cross.textContent = "\u00D7";
 
    token.appendChild(label);
    token.appendChild(cross);
    token.addEventListener("click", onRemove);
    return token;
  }
 
  // ------------------------------------------------------------ filter menus
 
  let fieldMenu = null;
  let valueMenu = null;
 
  if (filterFieldHost && filterValueHost) {
    fieldMenu = BanqDropdown(filterFieldHost, {
      options: FILTER_FIELDS.map((f) => f.label),
      value: FILTER_FIELDS.length ? FILTER_FIELDS[0].label : "",
      placeholder: "Choose a field",
      searchPlaceholder: "Search fields\u2026",
      ariaLabel: "Filter field",
      onChange: refreshValueMenu
    });
 
    valueMenu = BanqDropdown(filterValueHost, {
      options: [],
      multi: true,
      placeholder: "Choose values",
      searchPlaceholder: "Search values\u2026",
      ariaLabel: "Filter values"
    });
 
    refreshValueMenu();
  }
 
  function currentFilterField() {
    const label = fieldMenu ? fieldMenu.getValue() : "";
    const match = FILTER_FIELDS.find((f) => f.label === label);
    return match ? match.field : "";
  }
 
  function refreshValueMenu() {
    if (!valueMenu) return;
    const field = currentFilterField();
    valueMenu.setOptions(FIELD_OPTIONS[field] || []);
    valueMenu.setValue([]);
  }
 
  if (filterAdd) {
    filterAdd.addEventListener("click", function () {
      const field = currentFilterField();
      const values = valueMenu ? valueMenu.getValue() : [];
      if (!field || !values.length) return;
 
      filters[field] = filters[field] || [];
      values.forEach(function (value) {
        if (!filters[field].includes(value)) filters[field].push(value);
      });
 
      valueMenu.setValue([]);
      renderTokens();
      apply();
    });
  }
 
  if (filterRangeApply) {
    filterRangeApply.addEventListener("click", function () {
      valueRange = { min: filterMin.value.trim(), max: filterMax.value.trim() };
      renderTokens();
      apply();
    });
  }
 
  if (filterClear) {
    filterClear.addEventListener("click", function () {
      Object.keys(filters).forEach((key) => delete filters[key]);
      valueRange = { min: "", max: "" };
      if (filterMin) filterMin.value = "";
      if (filterMax) filterMax.value = "";
      if (searchInput) searchInput.value = "";
      if (valueMenu) valueMenu.setValue([]);
      renderTokens();
      apply();
    });
  }
 
  if (filterTrigger && filterPanel) {
    filterTrigger.addEventListener("click", function () {
      const opening = filterPanel.hidden;
      filterPanel.hidden = !opening;
      filterTrigger.setAttribute("aria-expanded", String(opening));
      filterTrigger.classList.toggle("is-open", opening);
    });
  }
 
  if (searchInput) {
    searchInput.addEventListener("input", function () {
      renderTokens();
      apply();
    });
  }
 
  if (showSold) showSold.addEventListener("change", apply);
 
  // ------------------------------------------- sort
 
  const SORTS = page === "sales"
    ? [
        { label: "Name A\u2013Z", field: "itemName", dir: "asc", type: "text" },
        { label: "Name Z\u2013A", field: "itemName", dir: "desc", type: "text" },
        { label: "Recently listed", field: "dateListed", dir: "desc", type: "text" },
        { label: "Recently sold", field: "dateSold", dir: "desc", type: "text" },
        { label: "Fastest to sell", field: "daysToSell", dir: "asc", type: "number" },
        { label: "Listing price, high to low", field: "listingPrice", dir: "desc", type: "number" },
        { label: "Sold for, high to low", field: "soldFor", dir: "desc", type: "number" }
      ]
    : [
        { label: "Name A\u2013Z", field: "itemName", dir: "asc", type: "text" },
        { label: "Name Z\u2013A", field: "itemName", dir: "desc", type: "text" },
        { label: "Value, high to low", field: "estimatedValue", dir: "desc", type: "number" },
        { label: "Value, low to high", field: "estimatedValue", dir: "asc", type: "number" },
        { label: "Category A\u2013Z", field: "category", dir: "asc", type: "text" },
        { label: "Brand A\u2013Z", field: "brand", dir: "asc", type: "text" },
        { label: "Wear frequency", field: "wearFrequency", dir: "asc", type: "text" }
      ];
 
  if (sortHost) {
    BanqDropdown(sortHost, {
      options: SORTS.map((s) => s.label),
      placeholder: "Sort",
      searchPlaceholder: "Search sorts\u2026",
      ariaLabel: "Sort items",
      onChange: function (label) {
        const rule = SORTS.find((s) => s.label === label);
        if (rule) sortRows(rule);
      }
    });
  }
 
  function sortRows(rule) {
    // Detail rows travel with the row they belong to, so move them as pairs.
    const pairs = rows().map(function (row) {
      const detail = row.nextElementSibling;
      return {
        row: row,
        detail: detail && detail.hasAttribute("data-detail-row") ? detail : null
      };
    });
 
    pairs.sort(function (a, b) {
      let result;
      if (rule.type === "number") {
        result = (Number(a.row.dataset[rule.field]) || 0) -
                 (Number(b.row.dataset[rule.field]) || 0);
      } else {
        result = String(a.row.dataset[rule.field] || "")
          .localeCompare(String(b.row.dataset[rule.field] || ""),
                         undefined, { sensitivity: "base" });
      }
      return rule.dir === "desc" ? -result : result;
    });
 
    pairs.forEach(function (pair) {
      tbody.appendChild(pair.row);
      if (pair.detail) tbody.appendChild(pair.detail);
    });
  }
 
  // ----------------------------------------------------------- status menus
 
  root.querySelectorAll("[data-status-host]").forEach(function (host) {
    const row = host.closest("[data-row]");
    BanqDropdown(host, {
      options: SALE_STATUSES,
      value: host.dataset.value || "",
      placeholder: "Set status",
      searchPlaceholder: "Search statuses\u2026",
      ariaLabel: "Sale status",
      onChange: function (value) {
        save(row, "sale_status", value);
      }
    });
  });
 
  // ------------------------------------------------------------ saving edits
 
  async function saveField(id, field, value) {
    const response = await fetch(`/api/items/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [field]: value })
    });
    if (!response.ok) throw new Error("Save failed");
    return response.json();
  }
 
  function flash(row, message, isError) {
    const note = row.querySelector("[data-row-note]");
    if (!note) return;
    note.textContent = message;
    note.classList.toggle("is-error", Boolean(isError));
    note.hidden = false;
    window.setTimeout(function () { note.hidden = true; }, isError ? 4000 : 1600);
  }
 
  async function save(row, field, value) {
    const id = row.dataset.id;
    try {
      const result = await saveField(id, field, value);
      syncRow(row, field, value, result);
      flash(row, "Saved");
 
      if (result.moved) {
        row.classList.add("is-leaving");
        const detail = row.nextElementSibling;
        window.setTimeout(function () {
          if (detail && detail.hasAttribute("data-detail-row")) detail.remove();
          row.remove();
          apply();
        }, 380);
        return;
      }
      apply();
    } catch (error) {
      flash(row, "Could not save \u2014 check your connection", true);
    }
  }
 
  /* Keep the row's own data-attributes in step with what the server now
     holds, so filters, sorting and the header figures stay truthful without
     a page reload. */
  function syncRow(row, field, value, result) {
    const key = field.replace(/_([a-z])/g, (m, c) => c.toUpperCase());
    row.dataset[key] = value == null ? "" : value;
 
    if (result.is_sold !== undefined) row.dataset.isSold = String(result.is_sold);
    if (result.listing_price !== undefined) {
      row.dataset.listingPrice = result.listing_price ?? 0;
    }
    if (result.sold_for !== undefined) row.dataset.soldFor = result.sold_for ?? 0;
 
    // Marking something sold stamps today's date server-side; show it here
    // straight away rather than waiting for a reload. It stays editable.
    const soldInput = row.querySelector('[data-field="date_sold"]');
    if (soldInput && result.date_sold) soldInput.value = result.date_sold;
 
    const listedInput = row.querySelector('[data-field="date_listed"]');
    if (listedInput && result.date_listed) listedInput.value = result.date_listed;
 
    const daysCell = row.querySelector("[data-days-cell]");
    if (daysCell) {
      daysCell.textContent = result.days_to_sell === null || result.days_to_sell === undefined
        ? "\u2014"
        : result.days_to_sell;
      row.dataset.daysToSell = result.days_to_sell ?? "";
    }
 
    const statusHost = row.querySelector("[data-status-host]");
    if (statusHost && result.sale_status !== undefined) {
      statusHost.classList.toggle("is-done", Boolean(result.is_sold));
    }
  }
 
  // Native inputs (dates, numbers, text) inside a row save on change.
  tbody.addEventListener("change", function (event) {
    const control = event.target.closest("[data-field]");
    if (!control || control.tagName === "DIV") return;
    const row = control.closest("[data-row]");
    if (!row) return;
    save(row, control.dataset.field, control.value);
  });
 
  // --------------------------------------------------- edit and expand
 
  tbody.addEventListener("click", function (event) {
    const toggle = event.target.closest("[data-edit-toggle]");
    if (toggle) {
      const row = toggle.closest("[data-row]");
      const editing = row.classList.toggle("is-editing");
      toggle.textContent = editing ? "Done" : "Edit";
      toggle.setAttribute("aria-label", editing ? "Finish editing" : "Edit this item");
      toggle.classList.toggle("is-active", editing);
      return;
    }
 
    const expand = event.target.closest("[data-expand-toggle]");
    if (expand) {
      const row = expand.closest("[data-row]");
      const detail = row.nextElementSibling;
      if (detail && detail.hasAttribute("data-detail-row")) {
        const opening = detail.hidden;
        detail.hidden = !opening;
        expand.setAttribute("aria-expanded", String(opening));
        expand.classList.toggle("is-open", opening);
        row.classList.toggle("is-expanded", opening);
      }
    }
  });
 
  renderTokens();
  apply();
})();