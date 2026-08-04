const provinceSelect = document.getElementById("province");
const wardSelect = document.getElementById("ward");

// Tải danh sách tỉnh
fetch("https://provinces.open-api.vn/api/p/")
    .then(res => res.json())
    .then(data => {
        data.forEach(province => {
            const option = document.createElement("option");
            option.value = province.code;
            option.textContent = province.name;
            provinceSelect.appendChild(option);
        });
    });

// Khi chọn tỉnh
provinceSelect.addEventListener("change", function () {

    wardSelect.innerHTML =
        '<option value="">-- Chọn phường / xã --</option>';

    wardSelect.disabled = true;

    if (!this.value) return;

    fetch(`https://provinces.open-api.vn/api/p/${this.value}?depth=2`)
        .then(res => res.json())
        .then(data => {

            // API có thể trả về wards hoặc districts tùy phiên bản
            let wards = [];

            if (data.wards) {
                wards = data.wards;
            } else if (data.districts) {
                data.districts.forEach(d => {
                    if (d.wards) {
                        wards.push(...d.wards);
                    }
                });
            }

            wards.forEach(ward => {
                const option = document.createElement("option");
                option.value = ward.code;
                option.textContent = ward.name;
                wardSelect.appendChild(option);
            });

            wardSelect.disabled = false;
        })
        .catch(err => console.error(err));
});
