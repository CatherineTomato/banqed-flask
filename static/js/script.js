document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("wardrobeSearch");
  const table = document.getElementById("wardrobeTable");

  if (!searchInput || !table) return;

  const rows = table.querySelectorAll("tbody tr");

  searchInput.addEventListener("input", function () {
    const query = searchInput.value.toLowerCase();

    rows.forEach(function (row) {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(query) ? "" : "none";
    });
  });
});