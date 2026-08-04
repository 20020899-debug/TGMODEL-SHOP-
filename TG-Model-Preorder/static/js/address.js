console.log("address.js đã chạy");

const provinceSelect = document.getElementById("province");

fetch("https://provinces.open-api.vn/api/p/")
    .then(response => response.json())
    .then(data => {

        console.log(data);

        data.forEach(province => {

            const option = document.createElement("option");

            option.value = province.code;
            option.textContent = province.name;

            provinceSelect.appendChild(option);

        });

    })
    .catch(error => {

        console.error(error);

    });
