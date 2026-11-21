const DOCTOR_LABELS = {
  wong_yat_tak: "王溢德 醫師 (Dr. Wong Yat Tak)",
  wong_yat_ki: "王溢琪 醫師 (Dr. Wong Yat Ki)",
};

const DOCTOR_SHORT = {
  wong_yat_tak: "王溢德",
  wong_yat_ki: "王溢琪",
};

const SERVICE_LABELS = {
  pain_rehabilitation: "疼痛康復",
  spinal_correction: "脊柱矯正",
  postpartum_recovery: "產後康復",
  posture_adjustment: "體態調整",
  foot_treatment: "足科治療",
  chinese_orthopedics: "中醫骨科",
  psychological_consultation: "心理諮詢",
  nutrition: "營養食療",
  online_consultation: "網上診症",
};

function getStatusColor(status) {
  switch ((status || "").toLowerCase()) {
    case "confirmed":
      return "#10b981"; // Green
    case "completed":
      return "#3b82f6"; // Blue
    case "cancelled":
      return "#9ca3af"; // Gray
    case "pending":
    default:
      return "#f59e0b"; // Amber
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const calendarEl = document.getElementById("calendar");
  const doctorFilter = document.getElementById("doctor-filter");
  const modal = document.getElementById("appointment-modal");

  if (!calendarEl) return;

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
    },
    slotMinTime: "09:00:00",
    slotMaxTime: "19:30:00",
    slotDuration: "00:30:00",
    allDaySlot: false,
    height: "auto",

    // Dynamically fetch events for the visible date range & selected doctor
    events: async function (fetchInfo, successCallback, failureCallback) {
      try {
        const startDate = fetchInfo.startStr.split("T")[0];
        const endDate = fetchInfo.endStr.split("T")[0];
        const selectedDoctor = doctorFilter ? doctorFilter.value : "";

        const params = new URLSearchParams({
          start_date: startDate,
          end_date: endDate,
        });
        if (selectedDoctor) {
          params.append("doctor", selectedDoctor);
        }

        const response = await fetch("/calendar?" + params.toString(), {
          cache: "no-store",
        });
        if (!response.ok) {
          throw new Error("Failed to fetch calendar events");
        }

        const appointments = await response.json();

        const events = appointments.map((item) => {
          const serviceText = SERVICE_LABELS[item.service] || item.service;
          const docText = DOCTOR_SHORT[item.doctor] || item.doctor || "";
          const paidTag = item.payment_status === "Paid" ? " [Paid]" : "";
          const color = getStatusColor(item.status);

          return {
            id: String(item.id),
            title: `${item.patient_name || "Patient"} - ${serviceText}${docText ? ` (${docText})` : ""}${paidTag}`,
            start: `${item.appointment_date}T${item.appointment_time}`,
            backgroundColor: color,
            borderColor: color,
          };
        });

        successCallback(events);
      } catch (error) {
        console.error("Failed to load calendar events:", error);
        failureCallback(error);
      }
    },

    // Open modal with full patient & appointment details on click
    eventClick: async function (info) {
      const id = info.event.id;

      try {
        const response = await fetch("/appointment/" + id, {
          cache: "no-store",
        });
        if (!response.ok) {
          throw new Error("Failed to fetch appointment details");
        }

        const data = await response.json();

        const memberEl = document.getElementById("member-code");
        if (memberEl) memberEl.textContent = "Member ID: " + (data.member_code || "-");

        document.getElementById("patient-name").textContent = "Name: " + (data.name || "-");
        document.getElementById("patient-phone").textContent = "Phone: " + (data.phone || "-");
        document.getElementById("patient-email").textContent = "Email: " + (data.email || "-");

        const doctorEl = document.getElementById("appointment-doctor");
        if (doctorEl) {
          doctorEl.textContent = "Doctor: " + (DOCTOR_LABELS[data.doctor] || data.doctor || "-");
        }

        document.getElementById("appointment-service").textContent =
          "Service: " + (SERVICE_LABELS[data.service] || data.service || "-");
        document.getElementById("appointment-date").textContent = "Date: " + (data.date || "-");
        document.getElementById("appointment-time").textContent = "Time: " + (data.time || "-");

        const paymentEl = document.getElementById("appointment-payment");
        if (paymentEl) {
          paymentEl.textContent = "Payment: " + (data.payment_status || "Unpaid");
        }

        const notesEl = document.getElementById("appointment-notes");
        if (notesEl) {
          notesEl.textContent = "Notes: " + (data.notes || "-");
        }

        document.getElementById("appointment-status").value = data.status || "Pending";

        // Link directly to the patient's digital profile
        const profileLink = document.getElementById("open-member-profile");
        if (profileLink && data.patient_id) {
          profileLink.href = "/admin/member-profile.html?id=" + data.patient_id;
        }

        modal.style.display = "block";

        document.getElementById("save-status").onclick = async function () {
          const newStatus = document.getElementById("appointment-status").value;

          const putRes = await fetch("/appointment/" + id, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(newStatus),
          });

          if (!putRes.ok) {
            alert("Failed to update status.");
            return;
          }

          alert("Updated successfully!");
          modal.style.display = "none";
          calendar.refetchEvents();
        };
      } catch (error) {
        console.error("Failed to load appointment details:", error);
        alert("Could not load appointment details.");
      }
    },
  });

  calendar.render();

  // Re-fetch events when switching doctor filter
  if (doctorFilter) {
    doctorFilter.addEventListener("change", () => {
      calendar.refetchEvents();
    });
  }

  // Close Modal Button Handler
  const closeBtn = document.getElementById("close-modal");
  if (closeBtn) {
    closeBtn.onclick = function () {
      modal.style.display = "none";
    };
  }
});