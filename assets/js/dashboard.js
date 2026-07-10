async function loadDashboard(){


const response =
await fetch(
"http://127.0.0.1:8000/dashboard"
);



const data =
await response.json();



document.getElementById(
"total-patients"
).innerHTML =
data.patients;



document.getElementById(
"total-bookings"
).innerHTML =
data.bookings;



document.getElementById(
"total-treatments"
).innerHTML =
data.treatments;



const serviceBox =
document.getElementById(
"services"
);



serviceBox.innerHTML="";



const serviceNames = {


    spinal_correction:
    "脊柱矯正",


    pain_rehabilitation:
    "疼痛康復",


    postpartum_recovery:
    "產后康復",


    posture_adjustment:
    "體態調整",


    foot_treatment:
    "足科治療",


    chinese_orthopedics:
    "中醫骨科",


    psychological_consultation:
    "心理咨詢",


    nutrition:
    "營養食療"


};



data.services.forEach(item=>{


serviceBox.innerHTML += `


<p>

${serviceNames[item.name] || item.name}

:

${item.count}

</p>


`;


});


}





loadDashboard();

