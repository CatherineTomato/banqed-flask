document.addEventListener("DOMContentLoaded", function () {
  const searchInputs = document.querySelectorAll(".table-search");

  searchInputs.forEach(function (input) {
    const tableId = input.getAttribute("data-table");
    const table = document.getElementById(tableId);
    if (!table) return;

    const rows = table.querySelectorAll("tbody tr");

    input.addEventListener("input", function () {
      const query = input.value.toLowerCase();

      rows.forEach(function (row) {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
      });
    });
  });
});