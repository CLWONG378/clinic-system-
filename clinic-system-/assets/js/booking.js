document
.getElementById("booking-form")
.addEventListener("submit", async function(event){


    event.preventDefault();



    const booking = {


        name: document.querySelector(
            'input[type="text"]'
        ).value,


        phone: document.querySelector(
            'input[type="tel"]'
        ).value,


        email: document.querySelector(
            'input[type="email"]'
        ).value,


        service: document.querySelector(
            "select"
        ).value,


        appointment_date: document.querySelector(
            'input[type="date"]'
        ).value,


        appointment_time: document.querySelector(
            'input[type="time"]'
        ).value


    };



    const response = await fetch(
        "http://127.0.0.1:8000/booking",
        {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify(booking)

        }

    );



    const result = await response.json();



    alert(result.message);



});