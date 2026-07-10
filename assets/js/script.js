let currentLanguage = "en";


async function changeLanguage(language) {

    currentLanguage = language;


    const path = window.location.pathname.includes("/pages/")
        ? "../languages/"
        : "languages/";


    const response = await fetch(
        `${path}${language}.json`
    );


    const translations = await response.json();


    document.querySelectorAll("[data-key]")
    .forEach(element => {

        const key = element.getAttribute("data-key");


        if (translations[key]) {

            element.textContent = translations[key];

        }

    });

}