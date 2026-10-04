document.addEventListener("DOMContentLoaded", () => {
  const minScoreSlider = document.getElementById("min-score-slider");
  const minScoreDisplay = document.getElementById("min-score-val");
  const filterForm = document.getElementById("jobs-filter-form");
  const searchInput = document.getElementById("search-keyword");
  const clearSearchBtn = document.getElementById("clear-search-btn");

  if (minScoreSlider && minScoreDisplay) {
    minScoreSlider.addEventListener("input", (e) => {
      minScoreDisplay.textContent = e.target.value + "%";
    });
    minScoreSlider.addEventListener("change", () => {
      if (filterForm) filterForm.submit();
    });
  }

  if (clearSearchBtn && searchInput && filterForm) {
    clearSearchBtn.addEventListener("click", () => {
      searchInput.value = "";
      filterForm.submit();
    });
  }

  const skillChips = document.querySelectorAll(".quick-skill-chip");
  skillChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const skill = chip.dataset.skill || "";
      if (searchInput && filterForm) {
        searchInput.value = skill;
        filterForm.submit();
      }
    });
  });

  const quickFilterSelects = document.querySelectorAll(".auto-submit-filter");
  quickFilterSelects.forEach((select) => {
    select.addEventListener("change", () => {
      if (filterForm) filterForm.submit();
    });
  });

  const matchTriggerButtons = document.querySelectorAll(".trigger-job-match-btn");
  matchTriggerButtons.forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const jobId = btn.dataset.jobId;
      if (!jobId) return;

      setButtonLoading(btn, true, "matching...");

      try {
        const response = await fetch("/api/match", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ job_id: jobId })
        });
        const data = await response.json();
        if (response.ok && data.success) {
          showToast("match analysis completed successfully.", "success");
          setTimeout(() => {
            window.location.href = data.redirect_url;
          }, 450);
        } else {
          setButtonLoading(btn, false);
          showToast(data.error || "failed to calculate match.", "error");
        }
      } catch (err) {
        setButtonLoading(btn, false);
        showToast("network error calculating match.", "error");
      }
    });
  });
});
