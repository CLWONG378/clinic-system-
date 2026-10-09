async function loadCalendar() {
  try {
    // Relative path works both locally and on DDNS domain
    const response = await fetch("/appointments");
    const appointments = await response.json();

    const events = appointments.map((item) => ({
      id: item.id,
      title: item.service,
      start: item.appointment_date + "T" + item.appointment_time,
    }));

    const calendarEl = document.getElementById("calendar");

    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: "dayGridMonth",
      events: events,
      height: "auto",

      eventClick: async function (info) {
        const id = info.event.id;

        // Relative path for fetching single appointment details
        const response = await fetch("/appointment/" + id);
        const data = await response.json();

        document.getElementById("patient-name").textContent = "Name: " + data.name;
        document.getElementById("patient-phone").textContent = "Phone: " + data.phone;
        document.getElementById("patient-email").textContent = "Email: " + data.email;
        document.getElementById("appointment-service").textContent = "Service: " + data.service;
        document.getElementById("appointment-date").textContent = "Date: " + data.date;
        document.getElementById("appointment-time").textContent = "Time: " + data.time;

        document.getElementById("appointment-status").value = data.status;

        document.getElementById("appointment-modal").style.display = "block";

        document.getElementById("save-status").onclick = async function () {
          const newStatus = document.getElementById("appointment-status").value;

          // Relative path for PUT request
          await fetch("/appointment/" + id, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(newStatus),
          });

          alert("Updated successfully!");
          location.reload();
        };
      },
    });

    calendar.render();
  } catch (error) {
    console.error("Failed to load calendar events:", error);
  }
}

loadCalendar();

// Close Modal Button Handler
document.getElementById("close-modal").onclick = function () {
  document.getElementById("appointment-modal").style.display = "none";
};
