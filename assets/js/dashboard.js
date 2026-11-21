const SERVICE_NAMES = {
  spinal_correction: "脊柱矯正 (Spinal Correction)",
  pain_rehabilitation: "疼痛康復 (Pain Rehabilitation)",
  postpartum_recovery: "產後康復 (Postpartum Recovery)",
  posture_adjustment: "體態調整 (Posture Adjustment)",
  foot_treatment: "足科治療 (Foot Treatment)",
  chinese_orthopedics: "中醫骨科 (Chinese Orthopedics)",
  psychological_consultation: "心理諮詢 (Psychological Consultation)",
  nutrition: "營養食療 (Nutrition)",
  online_consultation: "網上診症 (Online Consultation)",
};

async function loadDashboard() {
  const serviceBox = document.getElementById("services");

  try {
    // Relative path works both locally and on https://lohasmedical.synology.me
    const response = await fetch("/dashboard", { cache: "no-store" });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();

    const patientsEl = document.getElementById("total-patients");
    const bookingsEl = document.getElementById("total-bookings");
    const treatmentsEl = document.getElementById("total-treatments");
    const followupsEl = document.getElementById("total-followups");
    const paidEl = document.getElementById("total-paid-hkd");

    if (patientsEl) patientsEl.textContent = data.patients ?? 0;
    if (bookingsEl) bookingsEl.textContent = data.bookings ?? 0;
    if (treatmentsEl) treatmentsEl.textContent = data.treatments ?? 0;
    if (followupsEl && data.followups !== undefined) {
      followupsEl.textContent = data.followups;
    }
    if (paidEl && data.paid_amount_hkd !== undefined) {
      paidEl.textContent = `HK$${Number(data.paid_amount_hkd).toLocaleString("en-HK", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      })}`;
    }

    if (!serviceBox) return;
    serviceBox.innerHTML = "";

    if (Array.isArray(data.services) && data.services.length > 0) {
      const list = document.createElement("div");
      list.className = "popular-services-list";

      data.services.forEach((item) => {
        const displayName = SERVICE_NAMES[item.name] || item.name || "未分類 (Unspecified)";
        const count = Number(item.count) || 0;

        const row = document.createElement("p");
        const strong = document.createElement("strong");
        strong.textContent = displayName;
        row.appendChild(strong);
        row.appendChild(document.createTextNode(`: ${count}`));
        list.appendChild(row);
      });

      serviceBox.appendChild(list);
    } else {
      serviceBox.innerHTML = "<p>暫無熱門服務數據</p>";
    }
  } catch (error) {
    console.error("Failed to load dashboard data:", error);
    if (serviceBox) {
      serviceBox.innerHTML = "<p style='color:red;'>無法載入數據，請檢查伺服器連線。</p>";
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();

  const refreshBtn = document.getElementById("refresh-dashboard");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", loadDashboard);
  }
});