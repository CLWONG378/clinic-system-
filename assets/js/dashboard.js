async function loadDashboard() {
  try {
    // Relative path works both locally and via DDNS domain
    const response = await fetch("/dashboard");

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();

    document.getElementById("total-patients").textContent = data.patients ?? 0;
    document.getElementById("total-bookings").textContent = data.bookings ?? 0;
    document.getElementById("total-treatments").textContent = data.treatments ?? 0;

    const serviceBox = document.getElementById("services");
    serviceBox.innerHTML = "";

    const serviceNames = {
      spinal_correction: "脊柱矯正",
      pain_rehabilitation: "疼痛康復",
      postpartum_recovery: "產後康復",
      posture_adjustment: "體態調整",
      foot_treatment: "足科治療",
      chinese_orthopedics: "中醫骨科",
      psychological_consultation: "心理諮詢",
      nutrition: "營養食療"
    };

    if (data.services && data.services.length > 0) {
      let servicesHTML = "";
      data.services.forEach(item => {
        const displayName = serviceNames[item.name] || item.name;
        servicesHTML += `<p><strong>${displayName}</strong>: ${item.count}</p>`;
      });
      serviceBox.innerHTML = servicesHTML;
    } else {
      serviceBox.innerHTML = "<p>暫無熱門服務數據</p>";
    }

  } catch (error) {
    console.error("Failed to load dashboard data:", error);
    const serviceBox = document.getElementById("services");
    if (serviceBox) {
      serviceBox.innerHTML = "<p style='color:red;'>無法載入數據，請檢查伺服器連線。</p>";
    }
  }
}

loadDashboard();
