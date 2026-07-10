async function loadPackages(){


const response =
await fetch(
"http://127.0.0.1:8000/packages"
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
服務:
${p.service}
</p>


<p>
次數:
${p.sessions}
</p>


<p>
價格:
${p.price}
</p>


</div>


`;


});


}


loadPackages();