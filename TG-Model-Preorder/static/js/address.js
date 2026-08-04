const province = document.getElementById("province");
const district = document.getElementById("district");
const ward = document.getElementById("ward");

// Load tỉnh
fetch("https://provinces.open-api.vn/api/v1/p/")
    .then(res => res.json())
    .then(data => {
        data.forEach(p => {
            province.innerHTML +=
                `<option value="${p.code}">${p.name}</option>`;
        });
    });

// Chọn tỉnh
province.addEventListener("change", () => {

    district.innerHTML =
        '<option value="">-- Chọn quận / huyện --</option>';

    ward.innerHTML =
        '<option value="">-- Chọn phường / xã --</option>';

    district.disabled = true;
    ward.disabled = true;

    if (!province.value) return;

    fetch(`https://provinces.open-api.vn/api/v1/p/${province.value}?depth=2`)
        .then(res => res.json())
        .then(data => {

            data.districts.forEach(d => {

                district.innerHTML +=
                    `<option value="${d.code}">${d.name}</option>`;

            });

            district.disabled = false;

        });

});

// Chọn quận
district.addEventListener("change", () => {

    ward.innerHTML =
        '<option value="">-- Chọn phường / xã --</option>';

    ward.disabled = true;

    if (!district.value) return;

    fetch(`https://provinces.open-api.vn/api/v1/d/${district.value}?depth=2`)
        .then(res => res.json())
        .then(data => {

            data.wards.forEach(w => {

                ward.innerHTML +=
                    `<option value="${w.code}">${w.name}</option>`;

            });

            ward.disabled = false;

        });

});
