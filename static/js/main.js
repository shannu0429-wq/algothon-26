function showToast(message, type = "info", duration = 4000) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  
  const textSpan = document.createElement("span");
  textSpan.textContent = String(message).toLowerCase();
  
  const closeBtn = document.createElement("button");
  closeBtn.className = "toast-close";
  closeBtn.innerHTML = "&times;";
  closeBtn.onclick = () => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 250);
  };

  toast.appendChild(textSpan);
  toast.appendChild(closeBtn);
  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.add("show");
  });

  setTimeout(() => {
    if (toast.parentElement) {
      toast.classList.remove("show");
      setTimeout(() => toast.remove(), 250);
    }
  }, duration);
}

function setButtonLoading(button, isLoading, loadingText = "processing...") {
  if (!button) return;
  if (isLoading) {
    button.dataset.originalHtml = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `<span class="stage-spinner"></span> ${loadingText.toLowerCase()}`;
  } else {
    button.disabled = false;
    if (button.dataset.originalHtml) {
      button.innerHTML = button.dataset.originalHtml;
    }
  }
}

function syncThemeUI(theme) {
  const isDark = theme === "dark";
  const navBtn = document.getElementById("nav-theme-toggle");
  if (navBtn) {
    const icon = navBtn.querySelector(".theme-nav-icon") || navBtn;
    icon.textContent = isDark ? "☀️" : "🌙";
  }

  const sidebarBtn = document.getElementById("sidebar-theme-toggle");
  if (sidebarBtn) {
    const icon = sidebarBtn.querySelector(".theme-icon");
    const label = sidebarBtn.querySelector(".theme-label");
    if (icon) icon.textContent = isDark ? "☀️" : "🌙";
    if (label) label.textContent = isDark ? "light mode" : "dark mode";
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("jobalign_theme", next);
  syncThemeUI(next);
  showToast(`switched to ${next} mode`, "info", 2000);
}

document.addEventListener("DOMContentLoaded", () => {
  const initialTheme = document.documentElement.getAttribute("data-theme") || localStorage.getItem("jobalign_theme") || "dark";
  syncThemeUI(initialTheme);

  const navThemeBtn = document.getElementById("nav-theme-toggle");
  if (navThemeBtn) {
    navThemeBtn.addEventListener("click", toggleTheme);
  }

  const sidebarThemeBtn = document.getElementById("sidebar-theme-toggle");
  if (sidebarThemeBtn) {
    sidebarThemeBtn.addEventListener("click", toggleTheme);
  }

  const sidebar = document.getElementById("dashboard-sidebar");
  const collapseBtn = document.getElementById("sidebar-collapse-btn");

  if (sidebar) {
    const isCollapsed = localStorage.getItem("jobalign_sidebar_collapsed") === "true";
    if (isCollapsed) {
      sidebar.classList.add("collapsed");
    }

    if (collapseBtn) {
      collapseBtn.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed");
        const collapsedNow = sidebar.classList.contains("collapsed");
        localStorage.setItem("jobalign_sidebar_collapsed", collapsedNow ? "true" : "false");
      });
    }
  }

  const menuBtn = document.querySelector(".mobile-menu-btn");
  const navLinks = document.querySelector(".nav-links");
  if (menuBtn && navLinks) {
    menuBtn.addEventListener("click", () => {
      navLinks.classList.toggle("show");
    });
  }

  const flashMessages = document.querySelectorAll(".flash-msg-data");
  flashMessages.forEach((msg) => {
    const text = msg.dataset.message;
    const cat = msg.dataset.category || "info";
    if (text) {
      showToast(text, cat);
    }
  });
});
