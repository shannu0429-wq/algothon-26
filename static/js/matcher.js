document.addEventListener("DOMContentLoaded", () => {
  const tabPlatform = document.getElementById("tab-btn-platform");
  const tabCustom = document.getElementById("tab-btn-custom");
  const panelPlatform = document.getElementById("panel-platform");
  const panelCustom = document.getElementById("panel-custom");

  const platformSelect = document.getElementById("platform-job-select");
  const previewContainer = document.getElementById("job-preview-container");
  const noSelection = document.getElementById("platform-no-selection");
  const prevTitle = document.getElementById("prev-title");
  const prevCompany = document.getElementById("prev-company");
  const prevMeta = document.getElementById("prev-meta");
  const prevSkills = document.getElementById("prev-skills");
  const prevDesc = document.getElementById("prev-desc");
  const prevViewLink = document.getElementById("prev-view-link");
  const platformMatchBtn = document.getElementById("platform-match-btn");

  const matcherForm = document.getElementById("job-matcher-form");
  const jobTitleInput = document.getElementById("job-title-input");
  const jobCompanyInput = document.getElementById("job-company-input");
  const jobLocationInput = document.getElementById("job-location-input");
  const jobDescTextarea = document.getElementById("job-desc-textarea");
  const jobFileInput = document.getElementById("job-file-input");
  const clearBtn = document.getElementById("matcher-clear-btn");
  const sampleBtn = document.getElementById("matcher-sample-btn");
  const analyzeBtn = document.getElementById("matcher-submit-btn");
  const progressCard = document.getElementById("matching-progress-card");

  function switchTab(mode) {
    if (mode === "platform") {
      tabPlatform.classList.add("active");
      tabCustom.classList.remove("active");
      panelPlatform.style.display = "block";
      panelCustom.style.display = "none";
    } else {
      tabCustom.classList.add("active");
      tabPlatform.classList.remove("active");
      panelCustom.style.display = "block";
      panelPlatform.style.display = "none";
    }
  }

  if (tabPlatform && tabCustom) {
    tabPlatform.addEventListener("click", () => switchTab("platform"));
    tabCustom.addEventListener("click", () => switchTab("custom"));
  }

  async function loadJobPreview(jobId) {
    if (!jobId) {
      if (previewContainer) previewContainer.style.display = "none";
      if (noSelection) noSelection.style.display = "block";
      return;
    }

    try {
      const resp = await fetch(`/api/jobs/${jobId}`);
      const data = await resp.json();
      if (resp.ok && data.success && data.job) {
        const j = data.job;
        if (prevTitle) prevTitle.textContent = j.title;
        if (prevCompany) prevCompany.textContent = `${j.company} • ${j.location}`;
        if (prevMeta) {
          prevMeta.innerHTML = `
            <span class="meta-pill">📅 ${j.experience_required}</span>
            <span class="meta-pill">🎓 ${j.education_required}</span>
            <span class="meta-pill">💼 ${j.job_type}</span>
          `;
        }
        if (prevSkills) {
          const skills = j.required_skills || [];
          prevSkills.innerHTML = skills.map(s => `<span class="skill-tag" style="background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.3); color: #c7d2fe;">✦ ${s}</span>`).join("");
        }
        if (prevDesc) {
          const descSnippet = j.description.length > 280 ? j.description.slice(0, 280) + "..." : j.description;
          prevDesc.textContent = descSnippet;
        }
        if (prevViewLink) {
          prevViewLink.href = `/jobs/${j.id}`;
        }
        if (noSelection) noSelection.style.display = "none";
        if (previewContainer) previewContainer.style.display = "block";
      }
    } catch (err) {
      showToast("could not load job preview.", "error");
    }
  }

  if (platformSelect) {
    platformSelect.addEventListener("change", (e) => {
      loadJobPreview(e.target.value);
    });
    if (platformSelect.value) {
      loadJobPreview(platformSelect.value);
    }
  }

  function runProgressAnimation() {
    if (!progressCard) return;
    progressCard.style.display = "block";
    progressCard.scrollIntoView({ behavior: "smooth", block: "center" });

    const dot1 = document.getElementById("step-dot-1");
    const dot2 = document.getElementById("step-dot-2");
    const dot3 = document.getElementById("step-dot-3");
    const dot4 = document.getElementById("step-dot-4");

    setTimeout(() => {
      if (dot1) { dot1.classList.remove("active"); dot1.classList.add("done"); }
      if (dot2) { dot2.classList.add("active"); }
    }, 400);

    setTimeout(() => {
      if (dot2) { dot2.classList.remove("active"); dot2.classList.add("done"); }
      if (dot3) { dot3.classList.add("active"); }
    }, 900);

    setTimeout(() => {
      if (dot3) { dot3.classList.remove("active"); dot3.classList.add("done"); }
      if (dot4) { dot4.classList.add("active"); }
    }, 1400);
  }

  if (platformMatchBtn) {
    platformMatchBtn.addEventListener("click", async () => {
      const jobId = platformSelect ? platformSelect.value : null;
      if (!jobId) {
        showToast("please select a job opportunity first.", "warning");
        return;
      }

      setButtonLoading(platformMatchBtn, true, "matching...");
      runProgressAnimation();

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
          }, 600);
        } else {
          setButtonLoading(platformMatchBtn, false);
          if (progressCard) progressCard.style.display = "none";
          showToast(data.error || "failed to calculate match.", "error");
        }
      } catch (err) {
        setButtonLoading(platformMatchBtn, false);
        if (progressCard) progressCard.style.display = "none";
        showToast("network error during match calculation.", "error");
      }
    });
  }

  const sampleData = {
    title: "python backend engineer",
    company: "apex analytics",
    location: "remote",
    description: "we are looking for a python backend engineer to design, build, and maintain high-performance restful apis and data pipelines. the candidate will work with python, flask, mysql, redis, and docker in a fast-paced agile environment.\n\nrequirements:\n- 2+ years experience with python, flask or fastapi\n- strong understanding of mysql query optimization and database indexing\n- restful api design and authentication\n- familiarity with docker, git, and ci/cd workflows\n\npreferred:\n- experience with aws cloud services and redis"
  };

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (jobTitleInput) jobTitleInput.value = "";
      if (jobCompanyInput) jobCompanyInput.value = "";
      if (jobLocationInput) jobLocationInput.value = "";
      if (jobDescTextarea) jobDescTextarea.value = "";
      if (jobFileInput) jobFileInput.value = "";
      showToast("cleared job inputs.", "info");
    });
  }

  if (sampleBtn) {
    sampleBtn.addEventListener("click", () => {
      if (jobTitleInput) jobTitleInput.value = sampleData.title;
      if (jobCompanyInput) jobCompanyInput.value = sampleData.company;
      if (jobLocationInput) jobLocationInput.value = sampleData.location;
      if (jobDescTextarea) jobDescTextarea.value = sampleData.description;
      showToast("sample python role loaded.", "info");
    });
  }

  if (matcherForm) {
    matcherForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const formData = new FormData(matcherForm);
      const desc = formData.get("job_description") || "";
      const file = jobFileInput ? jobFileInput.files[0] : null;

      if (!desc.trim() && !file) {
        showToast("please paste a job description or upload a document.", "warning");
        return;
      }

      setButtonLoading(analyzeBtn, true, "analyzing custom match...");
      runProgressAnimation();

      try {
        const response = await fetch("/api/match", {
          method: "POST",
          body: formData
        });

        const data = await response.json();

        if (response.ok && data.success) {
          showToast("match analysis completed successfully.", "success");
          setTimeout(() => {
            window.location.href = data.redirect_url;
          }, 600);
        } else {
          setButtonLoading(analyzeBtn, false);
          if (progressCard) progressCard.style.display = "none";
          showToast(data.error || "could not complete match analysis.", "error");
        }
      } catch (err) {
        setButtonLoading(analyzeBtn, false);
        if (progressCard) progressCard.style.display = "none";
        showToast("network error occurred during matching.", "error");
      }
    });
  }

  const scoreElement = document.getElementById("animated-score-number");
  const scoreCircle = document.getElementById("score-circle-indicator");
  if (scoreElement && scoreCircle) {
    const targetScore = parseFloat(scoreElement.dataset.score || "0");
    let currentScore = 0;
    const duration = 1200;
    const startTime = performance.now();

    function updateScore(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      currentScore = eased * targetScore;
      scoreElement.textContent = Math.round(currentScore) + "%";
      scoreCircle.style.setProperty("--score-pct", Math.round(currentScore));

      if (progress < 1) {
        requestAnimationFrame(updateScore);
      } else {
        scoreElement.textContent = Math.round(targetScore) + "%";
        scoreCircle.style.setProperty("--score-pct", Math.round(targetScore));
      }
    }

    requestAnimationFrame(updateScore);
  }
});
