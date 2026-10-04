document.addEventListener("DOMContentLoaded", () => {
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

  if (!dropzone || !fileInput) return;

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

  function advanceStage(index) {
    stages.forEach((st, i) => {
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

      advanceStage(0);
      const stageTimer1 = setTimeout(() => advanceStage(1), 600);
      const stageTimer2 = setTimeout(() => advanceStage(2), 1400);
      const stageTimer3 = setTimeout(() => advanceStage(3), 2200);
      const stageTimer4 = setTimeout(() => advanceStage(4), 3000);
      const stageTimer5 = setTimeout(() => advanceStage(5), 3800);

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
            window.location.href = data.redirect_url || "/resume";
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
});
