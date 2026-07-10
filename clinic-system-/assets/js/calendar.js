async function loadCalendar(){


    const response = await fetch(
        "http://127.0.0.1:8000/appointments"
    );


    const appointments =
        await response.json();



    const events =
    appointments.map(item => ({


        id: item.id,


        title: item.service,


        start:
        item.appointment_date
        + "T"
        + item.appointment_time,


    }));



    const calendarEl =
        document.getElementById("calendar");



    const calendar =
    new FullCalendar.Calendar(

        calendarEl,

        {

            initialView: "dayGridMonth",

            events: events,

            height: "auto",


            eventClick: async function(info){


    const id = info.event.id;



    const response =
    await fetch(
        "http://127.0.0.1:8000/appointment/"
        + id
    );


    const data =
    await response.json();



    document.getElementById(
        "patient-name"
    ).innerHTML =
    "Name: " + data.name;



    document.getElementById(
        "patient-phone"
    ).innerHTML =
    "Phone: " + data.phone;



    document.getElementById(
        "patient-email"
    ).innerHTML =
    "Email: " + data.email;



    document.getElementById(
        "appointment-service"
    ).innerHTML =
    "Service: " + data.service;



    document.getElementById(
        "appointment-date"
    ).innerHTML =
    "Date: " + data.date;



    document.getElementById(
        "appointment-time"
    ).innerHTML =
    "Time: " + data.time;



    document.getElementById(
        "appointment-status"
    ).value =
    data.status;



    document
    .getElementById("appointment-modal")
    .style.display="block";



    document
    .getElementById("save-status")
    .onclick = async function(){



        await fetch(

            "http://127.0.0.1:8000/appointment/"
            + id,

            {

                method:"PUT",

                headers:{
                    "Content-Type":"application/json"
                },

                body:
                JSON.stringify(
                    document.getElementById(
                        "appointment-status"
                    ).value
                )

            }

        );



        alert("Updated");


        location.reload();


    };



}

        }

    );


    calendar.render();


}



loadCalendar();

document
.getElementById("close-modal")
.onclick=function(){

    document
    .getElementById("appointment-modal")
    .style.display="none";

};