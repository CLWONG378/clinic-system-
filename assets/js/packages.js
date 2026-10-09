// Relative path works both locally and on DDNS domain
const API = "";

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

async function loadPackages() {
  const box = document.getElementById("packages");

  try {
    const response = await fetch(`${API}/packages`);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    box.innerHTML = "";

    if (!data || data.length === 0) {
      box.innerHTML = "<p>暫無套餐資料</p>";
      return;
    }

    let packagesHTML = "";
    data.forEach((p) => {
      const serviceDisplayName = serviceNames[p.service] || p.service || "一般服務";
      
      packagesHTML += `
        <div class="member-card">
          <h3>${p.name}</h3>
          <p><strong>服務:</strong> ${serviceDisplayName}</p>
          <p><strong>次數:</strong> ${p.sessions ?? "-"} 次</p>
          <p><strong>價格:</strong> $${p.price ?? "-"}</p>
        </div>
      `;
    });

    box.innerHTML = packagesHTML;
  } catch (error) {
    console.error("Failed to load packages:", error);
    if (box) {
      box.innerHTML = "<p style='color:red;'>無法載入套餐資料，請檢查伺服器連線。</p>";
    }
  }
}

// Optional: Handler for creating a new package
const createPackageBtn = document.getElementById("create-package");
if (createPackageBtn) {
  createPackageBtn.onclick = async function () {
    const name = document.getElementById("package-name")?.value;
    const sessions = document.getElementById("package-sessions")?.value;
    const price = document.getElementById("package-price")?.value;

    if (!name || !sessions || !price) {
      return alert("請填寫所有套餐資料");
    }

    try {
      const response = await fetch(`${API}/packages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name,
          sessions: parseInt(sessions, 10),
          price: parseFloat(price)
        })
      });

      if (!response.ok) throw new Error("新增套餐失敗");

      alert("新增套餐成功！");
      location.reload();
    } catch (error) {
      alert("新增套餐錯誤：" + error.message);
    }
  };
}

// Initial Load Execution
loadPackages();
