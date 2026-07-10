const API =
"http://127.0.0.1:8000";



async function loadProfile(){


    const params =
    new URLSearchParams(
        window.location.search
    );


    const id =
    params.get("id");



    const response =
    await fetch(
        API + "/patient/" + id
    );

async function loadPatientPackages(){


const params =
new URLSearchParams(
window.location.search
);


const id =
params.get("id");



const response =
await fetch(

"http://127.0.0.1:8000/patient-packages/"
+id

);



const data =
await response.json();



const box =
document.getElementById(
"packages"
);



box.innerHTML="";



data.forEach(p=>{


box.innerHTML += `


<div class="member-card">


<h3>
${p.name}
</h3>


<p>
已使用:
${p.used}
</p>


<p>
剩餘:
${p.remaining}
</p>


<p>
狀態:
${p.status}
</p>


</div>


`;


});


}


loadPatientPackages();

async function loadPackageOptions(){


const response =
await fetch(

"http://127.0.0.1:8000/packages"

);



const data =
await response.json();



const select =
document.getElementById(
"package-select"
);



data.forEach(p=>{


select.innerHTML += `


<option value="${p.id}">

${p.name}

</option>


`;


});


}


loadPackageOptions();


    const data =
    await response.json();



    document.getElementById(
"profile-name"
).value =
data.name || "";


document.getElementById(
"profile-phone"
).value =
data.phone || "";


document.getElementById(
"profile-email"
).value =
data.email || "";


document.getElementById(
"profile-birthday"
).value =
data.birthday || "";


document.getElementById(
"profile-gender"
).value =
data.gender || "";


document.getElementById(
"profile-address"
).value =
data.address || "";


document.getElementById(
"profile-notes"
).value =
data.notes || "";



    const history =
    document.getElementById(
        "history"
    );


    history.innerHTML="";



    data.appointments.forEach(item=>{


        history.innerHTML += `

        <div>

        <p>
        日期:
        ${item.date}
        </p>


        <p>
        服務:
        ${item.service}
        </p>


        <p>
        狀態:
        ${item.status}
        </p>


        <hr>

        </div>

        `;


    });



}



async function loadTreatments(){


    const params =
    new URLSearchParams(
        window.location.search
    );


    const id =
    params.get("id");



    const response =
    await fetch(
        API + "/treatment/" + id
    );


    const data =
    await response.json();



    const box =
    document.getElementById(
        "treatments"
    );


    box.innerHTML="";



    data.forEach(item=>{


        box.innerHTML += `


        <div class="treatment-card">


        <p>
        日期:
        ${item.date}
        </p>



        ${
        item.image

        ?

        `<img 
        src="${API}/uploads/${item.image}"
        width="250">`

        :

        ""

        }



        <p>
        ${item.notes}
        </p>


        <hr>


        </div>


        `;


    });



}





document
.getElementById("add-treatment")
.onclick = async function(){



    const params =
    new URLSearchParams(
        window.location.search
    );


    const id =
    params.get("id");



    const formData =
    new FormData();



    formData.append(
        "patient_id",
        id
    );



    formData.append(
        "date",
        document.getElementById(
            "treatment-date"
        ).value
    );



    formData.append(
        "notes",
        document.getElementById(
            "treatment-notes"
        ).value
    );

    formData.append(

"service",

document.getElementById(
"treatment-service"
).value

);



    const file =
    document.getElementById(
        "treatment-image"
    ).files[0];



    if(file){

        formData.append(
            "image",
            file
        );

    }



    await fetch(

        API + "/treatment/upload",

        {

        method:"POST",

        body:formData

        }

    );

    await fetch(

"http://127.0.0.1:8000/consume-package",

{

method:"POST",

headers:{

"Content-Type":
"application/json"

},

body:JSON.stringify({

patient_id:id,

service:
document.getElementById(
"treatment-service"
).value

})

}

);



    alert(
        "新增成功"
    );


    location.reload();


};

document
.getElementById(
"buy-package"
)
.onclick = async function(){


const params =
new URLSearchParams(
window.location.search
);


const id =
params.get("id");



await fetch(

"http://127.0.0.1:8000/patient-package",

{

method:"POST",

headers:{

"Content-Type":
"application/json"

},


body:JSON.stringify({

patient_id:id,


package_id:
document.getElementById(
"package-select"
).value,


purchase_date:
new Date()
.toISOString()
.substring(0,10)

})


}

);



alert(
"套餐已加入"
);



location.reload();


};


async function loadFollowups(){


const params =
new URLSearchParams(
window.location.search
);


const id =
params.get("id");



const response =
await fetch(

"http://127.0.0.1:8000/followup/"
+ id

);



const data =
await response.json();



const box =
document.getElementById(
"followups"
);



box.innerHTML="";



data.forEach(item=>{


box.innerHTML += `


<div>

<p>
日期:
${item.date}
</p>


<p>
狀態:
${item.status}
</p>


<p>
${item.notes}
</p>


<hr>

</div>


`;

});


}



loadFollowups();




loadProfile();
document
.getElementById(
"save-profile"
)
.onclick = async function(){



const params =
new URLSearchParams(
window.location.search
);



const id =
params.get("id");



await fetch(

"http://127.0.0.1:8000/patient/"
+ id,


{

method:"PUT",


headers:{

"Content-Type":
"application/json"

},


body:JSON.stringify({

name:
document.getElementById(
"profile-name"
).value,


phone:
document.getElementById(
"profile-phone"
).value,


email:
document.getElementById(
"profile-email"
).value,


birthday:
document.getElementById(
"profile-birthday"
).value,


gender:
document.getElementById(
"profile-gender"
).value,


address:
document.getElementById(
"profile-address"
).value,


notes:
document.getElementById(
"profile-notes"
).value


})


}


);



alert(
"會員資料已更新"
);


};

loadTreatments();