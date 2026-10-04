document.addEventListener("DOMContentLoaded", () => {
  const tabUpload = document.getElementById("tab-btn-upload");
  const tabText = document.getElementById("tab-btn-text");
  const secUpload = document.getElementById("section-file-upload");
  const secText = document.getElementById("section-text-create");

  if (tabUpload && tabText && secUpload && secText) {
    tabUpload.addEventListener("click", () => {
      tabUpload.className = "btn btn-sm btn-primary";
      tabText.className = "btn btn-sm btn-secondary";
      secUpload.style.display = "block";
      secText.style.display = "none";
    });

    tabText.addEventListener("click", () => {
      tabText.className = "btn btn-sm btn-primary";
      tabUpload.className = "btn btn-sm btn-secondary";
      secText.style.display = "block";
      secUpload.style.display = "none";
    });
  }

  const dropzone = document.getElementById("resume-dropzone");
  const fileInput = document.getElementById("resume-file-input");
  const fileInfoBox = document.getElementById("file-info-box");
  const fileNameDisplay = document.getElementById("file-name-display");
  const fileSizeDisplay = document.getElementById("file-size-display");
  const fileTypeDisplay = document.getElementById("file-type-display");
  const uploadForm = document.getElementById("resume-upload-form");
  const submitBtn = document.getElementById("resume-submit-btn");
  const stageBox = document.getElementById("processing-stages-box");
  const stages = [
    document.getElementById("stage-uploading"),
    document.getElementById("stage-extracting"),
    document.getElementById("stage-detecting"),
    document.getElementById("stage-skills"),
    document.getElementById("stage-experience"),
    document.getElementById("stage-profile")
  ];

  function formatBytes(bytes) {
    if (bytes === 0) return "0 bytes";
    const k = 1024;
    const sizes = ["bytes", "kb", "mb"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  function handleFileSelect(file) {
    if (!file) return;
    const ext = file.name.split(".").pop().toLowerCase();
    const validExts = ["pdf", "docx", "txt", "png", "jpg", "jpeg"];
    if (!validExts.includes(ext)) {
      showToast("unsupported file format. please upload pdf, docx, txt, png, jpg, or jpeg.", "error");
      return;
    }

    if (file.size > 16 * 1024 * 1024) {
      showToast("file exceeds the 16mb maximum upload size.", "error");
      return;
    }

    if (fileNameDisplay) fileNameDisplay.textContent = file.name.toLowerCase();
    if (fileSizeDisplay) fileSizeDisplay.textContent = formatBytes(file.size);
    if (fileTypeDisplay) fileTypeDisplay.textContent = ext;
    if (fileInfoBox) fileInfoBox.style.display = "block";
    if (submitBtn) submitBtn.disabled = false;
  }

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
      }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add("drag-over");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove("drag-over");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect(e.dataTransfer.files[0]);
      }
    });
  }

  function advanceStage(index, stageList) {
    stageList.forEach((st, i) => {
      if (!st) return;
      if (i < index) {
        st.className = "stage-item completed";
        const icon = st.querySelector(".stage-icon");
        if (icon) icon.innerHTML = "✓";
      } else if (i === index) {
        st.className = "stage-item active";
        const icon = st.querySelector(".stage-icon");
        if (icon) icon.innerHTML = '<span class="stage-spinner"></span>';
      } else {
        st.className = "stage-item";
        const icon = st.querySelector(".stage-icon");
        if (icon) icon.innerHTML = "○";
      }
    });
  }

  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const files = fileInput.files;
      if (!files || files.length === 0) {
        showToast("please select a resume file first.", "warning");
        return;
      }

      const formData = new FormData();
      formData.append("resume_file", files[0]);

      if (submitBtn) setButtonLoading(submitBtn, true, "uploading...");
      if (stageBox) stageBox.style.display = "flex";

      advanceStage(0, stages);
      const stageTimer1 = setTimeout(() => advanceStage(1, stages), 600);
      const stageTimer2 = setTimeout(() => advanceStage(2, stages), 1400);
      const stageTimer3 = setTimeout(() => advanceStage(3, stages), 2200);
      const stageTimer4 = setTimeout(() => advanceStage(4, stages), 3000);
      const stageTimer5 = setTimeout(() => advanceStage(5, stages), 3800);

      try {
        const response = await fetch("/api/resume/upload", {
          method: "POST",
          body: formData
        });

        clearTimeout(stageTimer1);
        clearTimeout(stageTimer2);
        clearTimeout(stageTimer3);
        clearTimeout(stageTimer4);
        clearTimeout(stageTimer5);

        const data = await response.json();

        if (response.ok && data.success) {
          stages.forEach((st) => {
            if (st) {
              st.className = "stage-item completed";
              const icon = st.querySelector(".stage-icon");
              if (icon) icon.innerHTML = "✓";
            }
          });
          showToast("resume uploaded and analyzed successfully.", "success");
          setTimeout(() => {
            window.location.href = data.redirect_url || "/profile";
          }, 600);
        } else {
          if (submitBtn) setButtonLoading(submitBtn, false);
          if (stageBox) stageBox.style.display = "none";
          showToast(data.error || "failed to parse resume. please check file content.", "error");
        }
      } catch (err) {
        clearTimeout(stageTimer1);
        clearTimeout(stageTimer2);
        clearTimeout(stageTimer3);
        clearTimeout(stageTimer4);
        clearTimeout(stageTimer5);
        if (submitBtn) setButtonLoading(submitBtn, false);
        if (stageBox) stageBox.style.display = "none";
        showToast("an unexpected network error occurred while uploading.", "error");
      }
    });
  }

  const textForm = document.getElementById("resume-text-form");
  const descInput = document.getElementById("resume-desc-input");
  const sampleBtn = document.getElementById("load-sample-desc-btn");
  const textSubmitBtn = document.getElementById("text-resume-submit-btn");
  const textStageBox = document.getElementById("text-processing-stages-box");
  const textStages = [
    document.getElementById("tstage-parsing"),
    document.getElementById("tstage-skills"),
    document.getElementById("tstage-structuring"),
    document.getElementById("tstage-profile")
  ];

  if (sampleBtn && descInput) {
    sampleBtn.addEventListener("click", () => {
      descInput.value = `alex rivera
alex.rivera@example.com | san francisco, ca

professional summary
results-driven software engineer with 3+ years of experience designing and deploying scalable backend systems, rest apis, and microservices. proficient in python, flask, mysql, docker, redis, and cloud environments.

technical skills: python, flask, fastapi, mysql, redis, docker, git, rest api, postgresql, aws, celery

experience:
software engineer at novatech solutions (2022 - present)
- designed and built high-performance microservices using python and flask handling 2m+ daily requests.
- optimized mysql database queries and indexing strategies, reducing response times by 38%.
- implemented restful api endpoints with jwt authentication and role-based permissions.
- containerized backend services using docker and established github actions ci/cd.

education:
bachelor of science in computer science, university of california berkeley, 2021

projects:
ai resume analyzer - nlp-powered document evaluation tool utilizing python, flask, and semantic text embeddings.
distributed task queue - asynchronous job execution framework using redis, python, and mysql for background processing.`;
      const nameInput = document.getElementById("text-candidate-name");
      const roleInput = document.getElementById("text-candidate-role");
      if (nameInput && !nameInput.value) nameInput.value = "alex rivera";
      if (roleInput && !roleInput.value) roleInput.value = "python developer";
      showToast("sample developer profile loaded.", "info");
    });
  }

  if (textForm) {
    textForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const descVal = descInput.value.trim();
      if (!descVal || descVal.length < 20) {
        showToast("please provide a description with at least 20 characters.", "warning");
        return;
      }

      const nameVal = document.getElementById("text-candidate-name") ? document.getElementById("text-candidate-name").value.trim() : "";
      const roleVal = document.getElementById("text-candidate-role") ? document.getElementById("text-candidate-role").value.trim() : "";

      if (textSubmitBtn) setButtonLoading(textSubmitBtn, true, "generating profile...");
      if (textStageBox) textStageBox.style.display = "flex";

      advanceStage(0, textStages);
      const tTimer1 = setTimeout(() => advanceStage(1, textStages), 500);
      const tTimer2 = setTimeout(() => advanceStage(2, textStages), 1100);
      const tTimer3 = setTimeout(() => advanceStage(3, textStages), 1700);

      try {
        const response = await fetch("/api/resume/create-from-text", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            description: descVal,
            name: nameVal,
            target_role: roleVal
          })
        });

        clearTimeout(tTimer1);
        clearTimeout(tTimer2);
        clearTimeout(tTimer3);

        const data = await response.json();

        if (response.ok && data.success) {
          textStages.forEach((st) => {
            if (st) {
              st.className = "stage-item completed";
              const icon = st.querySelector(".stage-icon");
              if (icon) icon.innerHTML = "✓";
            }
          });
          const skillCount = (data.skills || []).length;
          showToast(`resume generated with ${skillCount} skills identified.`, "success");
          setTimeout(() => {
            window.location.href = data.redirect_url || "/profile";
          }, 600);
        } else {
          if (textSubmitBtn) setButtonLoading(textSubmitBtn, false);
          if (textStageBox) textStageBox.style.display = "none";
          showToast(data.error || "failed to parse description.", "error");
        }
      } catch (err) {
        clearTimeout(tTimer1);
        clearTimeout(tTimer2);
        clearTimeout(tTimer3);
        if (textSubmitBtn) setButtonLoading(textSubmitBtn, false);
        if (textStageBox) textStageBox.style.display = "none";
        showToast("an unexpected network error occurred while generating profile.", "error");
      }
    });
  }
});
