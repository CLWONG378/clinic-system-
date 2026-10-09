// Retrieve saved language from LocalStorage, default to "zh-hk" or "en"
let currentLanguage = localStorage.getItem("app_lang") || "zh-hk";

async function changeLanguage(language) {
  currentLanguage = language;
  localStorage.setItem("app_lang", language);

  try {
    // Root-absolute path guarantees correct fetching across any subroute (/pages, /admin, etc.)
    const response = await fetch(`/languages/${language}.json`);

    if (!response.ok) {
      throw new Error(`Failed to load translation file: ${language}.json`);
    }

    const translations = await response.json();

    document.querySelectorAll("[data-key]").forEach((element) => {
      const key = element.getAttribute("data-key");

      if (translations[key]) {
        // Handle input placeholders vs standard text content
        if (element.tagName === "INPUT" || element.tagName === "TEXTAREA") {
          if (element.hasAttribute("placeholder")) {
            element.setAttribute("placeholder", translations[key]);
          } else {
            element.value = translations[key];
          }
        } else {
          element.textContent = translations[key];
        }
      }
    });

    // Update html lang attribute
    document.documentElement.lang = language;
  } catch (error) {
    console.error("Language switching error:", error);
  }
}

// Automatically apply the saved language when the page loads
document.addEventListener("DOMContentLoaded", () => {
  changeLanguage(currentLanguage);
});
