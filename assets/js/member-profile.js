// Relative path base (works locally and via DDNS domain)
const API = "";

// Helper to get patient ID from URL query parameters (?id=...)
function getPatientId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

// 1. Load Profile Details & Appointments History
async function loadProfile() {
  const id = getPatientId();
  if (!id) return;

  try {
    const response = await fetch(`${API}/patient/${id}`);
    if (!response.ok) throw new Error("Failed to load patient data");
    
    const data = await response.json();

    document.getElementById("profile-name").value = data.name || "";
    document.getElementById("profile-phone").value = data.phone || "";
    document.getElementById("profile-email").value = data.email || "";
    document.getElementById("profile-birthday").value = data.birthday || "";
    document.getElementById("profile-gender").value = data.gender || "";
    document.getElementById("profile-address").value = data.address || "";
    document.getElementById("profile-notes").value = data.notes || "";

    const history = document.getElementById("history");
    history.innerHTML = "";

    if (data.appointments && data.appointments.length > 0) {
      let historyHTML = "";
      data.appointments.forEach((item) => {
        historyHTML += `
          <div>
            <p><strong>日期:</strong> ${item.date}</p>
            <p><strong>服務:</strong> ${item.service}</p>
            <p><strong>狀態:</strong> ${item.status}</p>
            <hr>
          </div>
        `;
      });
      history.innerHTML = historyHTML;
    } else {
      history.innerHTML = "<p>暫無預約紀錄</p>";
    }
  } catch (error) {
    console.error("Error in loadProfile:", error);
  }
}

// 2. Load Patient Purchased Packages
async function loadPatientPackages() {
  const id = getPatientId();
  if (!id) return;

  try {
    const response = await fetch(`${API}/patient-packages/${id}`);
    const data = await response.json();

    const box = document.getElementById("packages");
    box.innerHTML = "";

    if (data && data.length > 0) {
      let packagesHTML = "";
      data.forEach((p) => {
        packagesHTML += `
          <div class="member-card">
            <h3>${p.name}</h3>
            <p>已使用: ${p.used}</p>
            <p>剩餘: ${p.remaining}</p>
            <p>狀態: ${p.status}</p>
          </div>
        `;
      });
      box.innerHTML = packagesHTML;
    } else {
      box.innerHTML = "<p>暫無套餐資料</p>";
    }
  } catch (error) {
    console.error("Error in loadPatientPackages:", error);
  }
}

// 3. Load Available Package Options for Selection
async function loadPackageOptions() {
  try {
    const response = await fetch(`${API}/packages`);
    const data = await response.json();

    const select = document.getElementById("package-select");
    select.innerHTML = '<option value="">請選擇套餐</option>';

    data.forEach((p) => {
      select.innerHTML += `<option value="${p.id}">${p.name}</option>`;
    });
  } catch (error) {
    console.error("Error in loadPackageOptions:", error);
  }
}

// 4. Load Treatment Records
async function loadTreatments() {
  const id = getPatientId();
  if (!id) return;

  try {
    const response = await fetch(`${API}/treatment/${id}`);
    const data = await response.json();

    const box = document.getElementById("treatments");
    box.innerHTML = "";

    if (data && data.length > 0) {
      let treatmentsHTML = "";
      data.forEach((item) => {
        treatmentsHTML += `
          <div class="treatment-card">
            <p><strong>日期:</strong> ${item.date}</p>
            ${
              item.image
                ? `<img src="/uploads/${item.image}" width="250" style="max-width:100%; border-radius:4px;">`
                : ""
            }
            <p>${item.notes || ""}</p>
            <hr>
          </div>
        `;
      });
      box.innerHTML = treatmentsHTML;
    } else {
      box.innerHTML = "<p>暫無服務記錄</p>";
    }
  } catch (error) {
    console.error("Error in loadTreatments:", error);
  }
}

// 5. Load Follow-up History
async function loadFollowups() {
  const id = getPatientId();
  if (!id) return;

  try {
    const response = await fetch(`${API}/followup/${id}`);
    const data = await response.json();

    const box = document.getElementById("followups");
    box.innerHTML = "";

    if (data && data.length > 0) {
      let followupsHTML = "";
      data.forEach((item) => {
        followupsHTML += `
          <div>
            <p><strong>日期:</strong> ${item.date}</p>
            <p><strong>狀態:</strong> ${item.status}</p>
            <p>${item.notes}</p>
            <hr>
          </div>
        `;
      });
      box.innerHTML = followupsHTML;
    } else {
      box.innerHTML = "<p>暫無回訪紀錄</p>";
    }
  } catch (error) {
    console.error("Error in loadFollowups:", error);
  }
}

// --- Event Handlers ---

// Save Profile Info
const saveProfileBtn = document.getElementById("save-profile");
if (saveProfileBtn) {
  saveProfileBtn.onclick = async function () {
    const id = getPatientId();
    if (!id) return alert("無效的會員 ID");

    try {
      await fetch(`${API}/patient/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: document.getElementById("profile-name").value,
          phone: document.getElementById("profile-phone").value,
          email: document.getElementById("profile-email").value,
          birthday: document.getElementById("profile-birthday").value,
          gender: document.getElementById("profile-gender").value,
          address: document.getElementById("profile-address").value,
          notes: document.getElementById("profile-notes").value,
        }),
      });

      alert("會員資料已更新");
    } catch (error) {
      alert("更新失敗：" + error.message);
    }
  };
}

// Add Treatment Record & Consume Package
const addTreatmentBtn = document.getElementById("add-treatment");
if (addTreatmentBtn) {
  addTreatmentBtn.onclick = async function () {
    const id = getPatientId();
    if (!id) return alert("無效的會員 ID");

    const formData = new FormData();
    formData.append("patient_id", id);
    formData.append("date", document.getElementById("treatment-date").value);
    formData.append("notes", document.getElementById("treatment-notes").value);
    formData.append("service", document.getElementById("treatment-service").value);

    const file = document.getElementById("treatment-image").files[0];
    if (file) {
      formData.append("image", file);
    }

    try {
      // Upload treatment record
      await fetch(`${API}/treatment/upload`, {
        method: "POST",
        body: formData,
      });

      // Deduct package usage
      await fetch(`${API}/consume-package`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: id,
          service: document.getElementById("treatment-service").value,
        }),
      });

      alert("新增記錄成功");
      location.reload();
    } catch (error) {
      alert("新增記錄失敗：" + error.message);
    }
  };
}

// Buy Package
const buyPackageBtn = document.getElementById("buy-package");
if (buyPackageBtn) {
  buyPackageBtn.onclick = async function () {
    const id = getPatientId();
    const packageId = document.getElementById("package-select").value;
    if (!id || !packageId) return alert("請選擇有效套餐");

    try {
      await fetch(`${API}/patient-package`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: id,
          package_id: packageId,
          purchase_date: new Date().toISOString().substring(0, 10),
        }),
      });

      alert("套餐已加入");
      location.reload();
    } catch (error) {
      alert("購買套餐失敗：" + error.message);
    }
  };
}

// Add Followup Record
const addFollowupBtn = document.getElementById("add-followup");
if (addFollowupBtn) {
  addFollowupBtn.onclick = async function () {
    const id = getPatientId();
    if (!id) return alert("無效的會員 ID");

    try {
      await fetch(`${API}/followup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: id,
          date: document.getElementById("followup-date").value,
          status: document.getElementById("followup-status").value,
          notes: document.getElementById("followup-notes").value,
        }),
      });

      alert("新增回訪記錄成功");
      location.reload();
    } catch (error) {
      alert("新增回訪失敗：" + error.message);
    }
  };
}

// --- Initial Page Load Executions ---
loadProfile();
loadPatientPackages();
loadPackageOptions();
loadTreatments();
loadFollowups();
