document.addEventListener("DOMContentLoaded", () => {
  const progressBars = document.querySelectorAll(".progress-bar-fill");
  progressBars.forEach((bar) => {
    const width = bar.dataset.targetWidth || "0%";
    requestAnimationFrame(() => {
      bar.style.width = width;
    });
  });

  const editProfileForm = document.getElementById("profile-edit-form");
  if (editProfileForm) {
    editProfileForm.addEventListener("submit", () => {
      const btn = editProfileForm.querySelector("button[type='submit']");
      if (btn) setButtonLoading(btn, true, "saving changes...");
    });
  }

  const editResumeForm = document.getElementById("resume-edit-form");
  if (editResumeForm) {
    editResumeForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const saveBtn = document.getElementById("save-resume-changes-btn");
      if (saveBtn) setButtonLoading(saveBtn, true, "updating profile...");

      const name = document.getElementById("edit-name") ? document.getElementById("edit-name").value : "";
      const email = document.getElementById("edit-email") ? document.getElementById("edit-email").value : "";
      const phone = document.getElementById("edit-phone") ? document.getElementById("edit-phone").value : "";
      const location = document.getElementById("edit-location") ? document.getElementById("edit-location").value : "";
      const summary = document.getElementById("edit-summary") ? document.getElementById("edit-summary").value : "";
      const skillsRaw = document.getElementById("edit-skills") ? document.getElementById("edit-skills").value : "";
      const skills = skillsRaw.split(",").map(s => s.trim().toLowerCase()).filter(s => s.length > 0);

      try {
        const response = await fetch("/api/resume/update", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, phone, location, summary, skills })
        });
        const data = await response.json();
        if (response.ok && data.success) {
          showToast("candidate profile updated successfully.", "success");
          setTimeout(() => window.location.reload(), 500);
        } else {
          if (saveBtn) setButtonLoading(saveBtn, false);
          showToast(data.error || "failed to update candidate profile.", "error");
        }
      } catch (err) {
        if (saveBtn) setButtonLoading(saveBtn, false);
        showToast("network error updating profile.", "error");
      }
    });
  }
});
