// Relative path base (works locally and via https://lohasmedical.synology.me)
const API = "";

const SERVICE_LABELS = {
  spinal_correction: "脊柱矯正",
  pain_rehabilitation: "疼痛康復",
  postpartum_recovery: "產後康復",
  posture_adjustment: "體態調整",
  foot_treatment: "足科治療",
  chinese_orthopedics: "中醫骨科",
  psychological_consultation: "心理諮詢",
  nutrition: "營養食療",
  online_consultation: "網上診症",
};

const DOCTOR_LABELS = {
  wong_yat_tak: "王溢德 醫師",
  wong_yat_ki: "王溢琪 醫師",
};

function getPatientId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

function setTodayDefaults() {
  const today = new Date().toISOString().substring(0, 10);
  const followupDate = document.getElementById("followup-date");
  const treatmentDate = document.getElementById("treatment-date");
  if (followupDate && !followupDate.value) followupDate.value = today;
  if (treatmentDate && !treatmentDate.value) treatmentDate.value = today;
}

// 1. Load Profile Details & Appointments History
async function loadProfile() {
  const id = getPatientId();
  if (!id) return;

  try {
    const response = await fetch(`${API}/patient/${id}`, { cache: "no-store" });
    if (!response.ok) throw new Error("Failed to load patient data");

    const data = await response.json();

    const badge = document.getElementById("member-code-badge");
    if (badge) {
      badge.textContent = data.member_code ? `(${data.member_code})` : "";
    }

    document.getElementById("profile-name").value = data.name || "";
    document.getElementById("profile-phone").value = data.phone || "";
    document.getElementById("profile-email").value = data.email || "";
    document.getElementById("profile-birthday").value = data.birthday || "";
    document.getElementById("profile-gender").value = data.gender || "";
    document.getElementById("profile-address").value = data.address || "";

    const medHistoryEl = document.getElementById("profile-medical-history");
    if (medHistoryEl) medHistoryEl.value = data.medical_history || "";

    document.getElementById("profile-notes").value = data.notes || "";

    const history = document.getElementById("history");
    history.innerHTML = "";

    if (data.appointments && data.appointments.length > 0) {
      let historyHTML = "";
      data.appointments.forEach((item) => {
        const serviceText = SERVICE_LABELS[item.service] || item.service || "-";
        const doctorText = DOCTOR_LABELS[item.doctor] || item.doctor || "-";
        const payText = item.payment_status ? ` | 付款: ${item.payment_status}` : "";
        historyHTML += `
          <div>
            <p><strong>日期:</strong> ${item.date || "-"} ${item.time || ""}</p>
            <p><strong>服務:</strong> ${serviceText}</p>
            <p><strong>醫師:</strong> ${doctorText}</p>
            <p><strong>狀態:</strong> ${item.status || "-"}${payText}</p>
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
    const response = await fetch(`${API}/patient-packages/${id}`, { cache: "no-store" });
    const data = await response.json();

    const box = document.getElementById("packages");
    box.innerHTML = "";

    if (data && data.length > 0) {
      let packagesHTML = "";
      data.forEach((p) => {
        const expiryText = p.expiry_date ? `<p>到期日: ${p.expiry_date}</p>` : "";
        packagesHTML += `
          <div class="member-card">
            <h3>${p.name}</h3>
            <p>已使用: ${p.used} / ${p.total ?? p.used + p.remaining}</p>
            <p>剩餘: ${p.remaining}</p>
            ${expiryText}
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
    const response = await fetch(`${API}/packages`, { cache: "no-store" });
    const data = await response.json();

    const select = document.getElementById("package-select");
    select.innerHTML = '<option value="">請選擇套餐</option>';

    data.forEach((p) => {
      const priceText = p.price != null ? ` ($${p.price})` : "";
      select.innerHTML += `<option value="${p.id}">${p.name} (${p.sessions}次)${priceText}</option>`;
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
    const response = await fetch(`${API}/treatment/${id}`, { cache: "no-store" });
    const data = await response.json();

    const box = document.getElementById("treatments");
    box.innerHTML = "";

    if (data && data.length > 0) {
      let treatmentsHTML = "";
      data.forEach((item) => {
        const serviceText = SERVICE_LABELS[item.service] || item.service || "";
        const doctorText = DOCTOR_LABELS[item.doctor] || item.doctor || "";
        const painText =
          item.pain_score !== null && item.pain_score !== undefined && item.pain_score !== ""
            ? `<p><strong>痛楚指數:</strong> ${item.pain_score} / 10</p>`
            : "";

        treatmentsHTML += `
          <div class="treatment-card">
            <p><strong>日期:</strong> ${item.date || "-"}</p>
            ${serviceText ? `<p><strong>服務:</strong> ${serviceText}</p>` : ""}
            ${doctorText ? `<p><strong>醫師:</strong> ${doctorText}</p>` : ""}
            ${painText}
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
    const response = await fetch(`${API}/followup/${id}`, { cache: "no-store" });
    const data = await response.json();

    const box = document.getElementById("followups");
    box.innerHTML = "";

    if (data && data.length > 0) {
      let followupsHTML = "";
      data.forEach((item) => {
        const progressText = item.progress_rating ? `<p><strong>進度評級:</strong> ${item.progress_rating}</p>` : "";
        const nextDateText = item.next_followup_date ? `<p><strong>下次跟進:</strong> ${item.next_followup_date}</p>` : "";
        followupsHTML += `
          <div>
            <p><strong>日期:</strong> ${item.date || "-"}</p>
            <p><strong>狀態:</strong> ${item.status || "-"}</p>
            ${progressText}
            ${nextDateText}
            <p>${item.notes || ""}</p>
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

    const medHistoryEl = document.getElementById("profile-medical-history");

    try {
      const res = await fetch(`${API}/patient/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: document.getElementById("profile-name").value,
          phone: document.getElementById("profile-phone").value,
          email: document.getElementById("profile-email").value,
          birthday: document.getElementById("profile-birthday").value,
          gender: document.getElementById("profile-gender").value,
          address: document.getElementById("profile-address").value,
          medical_history: medHistoryEl ? medHistoryEl.value : "",
          notes: document.getElementById("profile-notes").value,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      alert("會員資料已更新");
    } catch (error) {
      alert("更新失敗：" + error.message);
    }
  };
}

// Add Treatment Record & Consume Package (if active package exists)
const addTreatmentBtn = document.getElementById("add-treatment");
if (addTreatmentBtn) {
  addTreatmentBtn.onclick = async function () {
    const id = getPatientId();
    if (!id) return alert("無效的會員 ID");

    const serviceVal = document.getElementById("treatment-service").value;
    const doctorEl = document.getElementById("treatment-doctor");
    const painEl = document.getElementById("treatment-pain-score");

    const formData = new FormData();
    formData.append("patient_id", id);
    formData.append("date", document.getElementById("treatment-date").value);
    formData.append("notes", document.getElementById("treatment-notes").value);
    formData.append("service", serviceVal);

    if (doctorEl && doctorEl.value) {
      formData.append("doctor", doctorEl.value);
    }
    if (painEl && painEl.value !== "") {
      formData.append("pain_score", painEl.value);
    }

    const file = document.getElementById("treatment-image").files[0];
    if (file) {
      formData.append("image", file);
    }

    try {
      const uploadRes = await fetch(`${API}/treatment/upload`, {
        method: "POST",
        body: formData,
      });
      if (!uploadRes.ok) throw new Error(`Upload failed (${uploadRes.status})`);

      // Attempt to deduct 1 package session if patient has an active package for this service
      const consumeRes = await fetch(`${API}/consume-package`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: Number(id),
          service: serviceVal,
        }),
      });

      const msg = consumeRes.ok
        ? "新增記錄成功（已自動扣減 1 次套餐）"
        : "新增記錄成功";

      alert(msg);
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
    const expiryEl = document.getElementById("package-expiry");
    if (!id || !packageId) return alert("請選擇有效套餐");

    try {
      const res = await fetch(`${API}/patient-package`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: Number(id),
          package_id: Number(packageId),
          purchase_date: new Date().toISOString().substring(0, 10),
          expiry_date: expiryEl && expiryEl.value ? expiryEl.value : null,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
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

    const nextDateEl = document.getElementById("followup-next-date");
    const progressEl = document.getElementById("followup-progress");

    try {
      const res = await fetch(`${API}/followup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: Number(id),
          date: document.getElementById("followup-date").value,
          next_followup_date: nextDateEl && nextDateEl.value ? nextDateEl.value : null,
          status: document.getElementById("followup-status").value,
          progress_rating: progressEl && progressEl.value ? progressEl.value : null,
          notes: document.getElementById("followup-notes").value,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      alert("新增回訪記錄成功");
      location.reload();
    } catch (error) {
      alert("新增回訪失敗：" + error.message);
    }
  };
}

// --- Initial Page Load Executions ---
setTodayDefaults();
loadProfile();
loadPatientPackages();
loadPackageOptions();
loadTreatments();
loadFollowups();