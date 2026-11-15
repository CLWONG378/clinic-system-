document.addEventListener("DOMContentLoaded", () => {
    // 1. Set minimum selectable date to today
    const dateInput = document.getElementById("appointment-date");
    if (dateInput) {
        const today = new Date().toISOString().split("T")[0];
        dateInput.min = today;
    }

    // 2. Generate 30-minute interval time slot buttons (09:00 - 18:00)
    generateTimeSlots("09:00", "18:00", 30);

    // 3. Attach form submission listener
    const form = document.getElementById("booking-form");
    if (form) {
        form.addEventListener("submit", handleBookingSubmit);
    }
});

/**
 * Doctor Selection Handler
 * Triggered when a doctor button card is clicked
 */
function selectDoctor(doctorId, element) {
    // Remove 'selected' state from all doctor buttons
    document.querySelectorAll(".doctor-card-btn").forEach(btn => {
        btn.classList.remove("selected");
    });

    // Highlight the clicked button
    element.classList.add("selected");

    // Store doctor ID in hidden input field
    document.getElementById("selected-doctor").value = doctorId;
}

/**
 * Dynamically generates 30-minute time slot buttons
 */
function generateTimeSlots(startStr, endStr, intervalMinutes) {
    const container = document.getElementById("time-slots-container");
    if (!container) return;

    container.innerHTML = ""; // Clear existing slots

    const [startHour, startMin] = startStr.split(":").map(Number);
    const [endHour, endMin] = endStr.split(":").map(Number);

    let current = new Date();
    current.setHours(startHour, startMin, 0, 0);

    const end = new Date();
    end.setHours(endHour, endMin, 0, 0);

    while (current < end) {
        const timeString = current.toTimeString().substring(0, 5); // Format "HH:MM"

        const button = document.createElement("button");
        button.type = "button";
        button.className = "time-slot-btn";
        button.innerText = timeString;

        // Click event for selecting a time slot
        button.onclick = function () {
            document.querySelectorAll(".time-slot-btn").forEach(btn => btn.classList.remove("selected"));
            button.classList.add("selected");
            document.getElementById("appointment-time").value = timeString;
        };

        container.appendChild(button);

        // Advance time by 30 minutes
        current.setMinutes(current.getMinutes() + intervalMinutes);
    }
}

/**
 * Form Submit Handler with Fetch API
 */
async function handleBookingSubmit(event) {
    event.preventDefault();

    const selectedDoctor = document.getElementById("selected-doctor").value;
    const selectedTime = document.getElementById("appointment-time").value;

    // Validation checks
    if (!selectedDoctor) {
        alert("請選擇醫生 (Please select a doctor)");
        return;
    }

    if (!selectedTime) {
        alert("請選擇預約時段 (Please select a time slot)");
        return;
    }

    // Build payload matching backend requirements
    const booking = {
        name: document.getElementById("name").value,
        phone: document.getElementById("phone").value,
        email: document.getElementById("email").value,
        service: document.getElementById("service").value,
        doctor: selectedDoctor,
        appointment_date: document.getElementById("appointment-date").value,
        appointment_time: selectedTime
    };

    try {
        const response = await fetch("http://127.0.0.1:8000/booking", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(booking)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const result = await response.json();
        alert(result.message || "預約成功！ (Booking Successful!)");

        // Reset form state on success
        document.getElementById("booking-form").reset();
        document.querySelectorAll(".selected").forEach(el => el.classList.remove("selected"));
        document.getElementById("selected-doctor").value = "";
        document.getElementById("appointment-time").value = "";

    } catch (error) {
        console.error("Booking error:", error);
        alert("預約提交失敗，請稍後再試。 (Booking submission failed. Please try again.)");
    }
}