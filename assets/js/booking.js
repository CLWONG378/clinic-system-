// Automatically uses "https://lohasmedical.synology.me" when live,
// or falls back to your public URL if opened locally.
const API_BASE_URL = window.location.origin.startsWith("http")
    ? window.location.origin
    : "https://lohasmedical.synology.me";

document.addEventListener("DOMContentLoaded", () => {
    const dateInput = document.getElementById("appointment-date");
    if (dateInput) {
        const today = new Date().toISOString().split("T")[0];
        dateInput.min = today;

        // Refresh booked slots when user picks or types a date
        dateInput.addEventListener("change", updateAvailableSlots);
    }

    // Generate initial 30-minute interval time slot buttons (09:00 - 18:00)
    generateTimeSlots("09:00", "18:00", 30, []);

    // Attach form submission listener
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

    // Fetch booked slots for the newly selected doctor
    updateAvailableSlots();
}

/**
 * Fetches booked slots from the database via backend API and re-renders buttons
 */
async function updateAvailableSlots() {
    const doctorId = document.getElementById("selected-doctor").value;
    const appointmentDate = document.getElementById("appointment-date").value;

    // Clear any previously selected time whenever doctor or date changes
    document.getElementById("appointment-time").value = "";

    // Wait until both doctor and date are chosen before querying the database
    if (!doctorId || !appointmentDate) {
        generateTimeSlots("09:00", "18:00", 30, []);
        return;
    }

    try {
        const url = `${API_BASE_URL}/booked-slots?doctor=${encodeURIComponent(doctorId)}&appointment_date=${encodeURIComponent(appointmentDate)}`;
        const response = await fetch(url, { cache: "no-store" });

        if (!response.ok) {
            throw new Error(`Failed to fetch booked slots: ${response.status}`);
        }

        const data = await response.json();
        const bookedTimes = Array.isArray(data.booked_times) ? data.booked_times : [];

        generateTimeSlots("09:00", "18:00", 30, bookedTimes);
    } catch (error) {
        console.error("Error loading booked slots:", error);
        generateTimeSlots("09:00", "18:00", 30, []);
    }
}

/**
 * Dynamically generates 30-minute time slot buttons and grays out booked ones
 */
function generateTimeSlots(startStr, endStr, intervalMinutes, bookedTimes = []) {
    const container = document.getElementById("time-slots-container");
    if (!container) return;

    container.innerHTML = ""; // Clear existing slots
    const bookedSet = new Set(bookedTimes);

    const [startHour, startMin] = startStr.split(":").map(Number);
    const [endHour, endMin] = endStr.split(":").map(Number);

    let current = new Date();
    current.setHours(startHour, startMin, 0, 0);

    const end = new Date();
    end.setHours(endHour, endMin, 0, 0);

    while (current < end) {
        const timeString = current.toTimeString().substring(0, 5); // Format "HH:MM"
        const isBooked = bookedSet.has(timeString);

        const button = document.createElement("button");
        button.type = "button";
        button.className = "time-slot-btn";
        button.innerText = timeString;

        if (isBooked) {
            // Gray out and prevent clicking
            button.disabled = true;
            button.classList.add("booked");
            button.title = "此時段已被預約 (Already Booked)";
        } else {
            // Click event for selecting an available time slot
            button.onclick = function () {
                document.querySelectorAll(".time-slot-btn").forEach(btn => btn.classList.remove("selected"));
                button.classList.add("selected");
                document.getElementById("appointment-time").value = timeString;
            };
        }

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
    const selectedDate = document.getElementById("appointment-date").value;
    const selectedTime = document.getElementById("appointment-time").value;

    // Validation checks
    if (!selectedDoctor) {
        alert("請選擇醫生 (Please select a doctor)");
        return;
    }

    if (!selectedDate) {
        alert("請選擇預約日期 (Please select a date)");
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
        appointment_date: selectedDate,
        appointment_time: selectedTime
    };

    try {
        const response = await fetch(`${API_BASE_URL}/booking`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(booking)
        });

        // Handle duplicate booking if someone else booked the slot just before submit
        if (response.status === 409) {
            alert("此時段剛剛已被預約，請選擇其他時段。(This time slot was just booked. Please select another slot.)");
            await updateAvailableSlots(); // Refresh grayed-out buttons immediately
            return;
        }

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
        generateTimeSlots("09:00", "18:00", 30, []);

    } catch (error) {
        console.error("Booking error:", error);
        alert("預約提交失敗，請稍後再試。 (Booking submission failed. Please try again.)");
    }
}