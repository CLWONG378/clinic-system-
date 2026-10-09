let allPatients = [];

async function loadMembers() {
  const container = document.getElementById("members");

  try {
    // Relative path for API request
    const response = await fetch("/patients");

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    allPatients = await response.json();
    displayMembers(allPatients);
  } catch (error) {
    console.error("Failed to load members:", error);
    if (container) {
      container.innerHTML = "<p style='color:red;'>無法載入會員資料，請檢查伺服器連線。</p>";
    }
  }
}

function displayMembers(patients) {
  const container = document.getElementById("members");
  if (!container) return;

  container.innerHTML = "";

  if (!patients || patients.length === 0) {
    container.innerHTML = "<p>找不到相關會員紀錄</p>";
    return;
  }

  patients.forEach((patient) => {
    const card = document.createElement("div");

    card.innerHTML = `
      <div class="member-card">
        <h3>${patient.name || "未提供姓名"}</h3>
        <p><strong>電話:</strong> ${patient.phone || "未提供"}</p>
        <p><strong>電郵:</strong> ${patient.email || "未提供"}</p>
        <button type="button" onclick="viewMember(${patient.id})">
          查看資料
        </button>
      </div>
    `;

    container.appendChild(card);
  });
}

// Live Search Event Listener
const searchInput = document.getElementById("search-member");
if (searchInput) {
  searchInput.addEventListener("input", function () {
    const keyword = this.value.trim().toLowerCase();

    const filtered = allPatients.filter((p) => {
      const nameMatch = (p.name || "").toLowerCase().includes(keyword);
      const phoneMatch = (p.phone || "").includes(keyword);
      return nameMatch || phoneMatch;
    });

    displayMembers(filtered);
  });
}

// Redirect to Member Profile
function viewMember(id) {
  window.location.href = `member-profile.html?id=${id}`;
}

// Initial Load Execution
loadMembers();
