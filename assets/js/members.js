let allPatients = [];



async function loadMembers(){


    const response =
    await fetch(
        "http://127.0.0.1:8000/patients"
    );


    allPatients =
    await response.json();



    displayMembers(
        allPatients
    );


}



function displayMembers(
    patients
){


    const container =
    document.getElementById(
        "members"
    );


    container.innerHTML="";



    patients.forEach(patient=>{


        const card =
        document.createElement(
            "div"
        );



        card.innerHTML = `


        <div class="member-card">


        <h3>
        ${patient.name}
        </h3>


        <p>
        電話:
        ${patient.phone}
        </p>


        <p>
        電郵:
        ${patient.email || ""}
        </p>


        <button
        onclick="viewMember(${patient.id})">

        查看資料

        </button>


        </div>


        `;



        container.appendChild(card);


    });


}





document
.getElementById(
"search-member"
)
.addEventListener(
"input",
function(){



    const keyword =
    this.value
    .toLowerCase();



    const filtered =
    allPatients.filter(
        p =>


        p.name
        .toLowerCase()
        .includes(keyword)

        ||

        (p.phone || "")
        .includes(keyword)


    );



    displayMembers(
        filtered
    );


});





function viewMember(id){


    window.location.href =
    "member-profile.html?id="
    + id;


}




loadMembers();