const province = document.getElementById("province");
const district = document.getElementById("district");
const ward = document.getElementById("ward");

// =========================
// Load danh sách tỉnh
// =========================
fetch("https://provinces.open-api.vn/api/v1/p/")
    .then(res => res.json())
    .then(data => {

        data.forEach(p => {

            const option = document.createElement("option");

            // Dùng tên để gửi về Flask
            option.value = p.name;

            // Hiển thị tên
            option.textContent = p.name;

            // Lưu mã tỉnh để gọi API
            option.dataset.code = p.code;

            province.appendChild(option);

        });

    });


// =========================
// Khi chọn tỉnh
// =========================
province.addEventListener("change", function () {

    district.innerHTML =
        '<option value="">-- Chọn quận / huyện --</option>';

    ward.innerHTML =
        '<option value="">-- Chọn phường / xã --</option>';

    district.disabled = true;
    ward.disabled = true;

    if (this.selectedIndex === 0) return;

    const provinceCode =
        this.options[this.selectedIndex].dataset.code;

    fetch(`https://provinces.open-api.vn/api/v1/p/${provinceCode}?depth=2`)
        .then(res => res.json())
        .then(data => {

            data.districts.forEach(d => {

                const option = document.createElement("option");

                option.value = d.name;
                option.textContent = d.name;
                option.dataset.code = d.code;

                district.appendChild(option);

            });

            district.disabled = false;

        });

});


// =========================
// Khi chọn huyện
// =========================
district.addEventListener("change", function () {

    ward.innerHTML =
        '<option value="">-- Chọn phường / xã --</option>';

    ward.disabled = true;

    if (this.selectedIndex === 0) return;

    const districtCode =
        this.options[this.selectedIndex].dataset.code;

    fetch(`https://provinces.open-api.vn/api/v1/d/${districtCode}?depth=2`)
        .then(res => res.json())
        .then(data => {

            data.wards.forEach(w => {

                const option = document.createElement("option");

                option.value = w.name;
                option.textContent = w.name;

                ward.appendChild(option);

            });

            ward.disabled = false;

        });

});
