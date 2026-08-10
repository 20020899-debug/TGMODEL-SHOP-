const provinceSelect =
    document.getElementById(
        "province"
    );


const districtSelect =
    document.getElementById(
        "district"
    );


const wardSelect =
    document.getElementById(
        "ward"
    );


// =========================================================
// TẢI TỈNH
// =========================================================

fetch(
    "https://provinces.open-api.vn/api/v2/p/"
)

.then(
    response => response.json()
)

.then(
    provinces => {

        provinces.forEach(
            province => {

                const option =
                    document.createElement(
                        "option"
                    );


                option.value =
                    province.name;


                option.textContent =
                    province.name;


                option.dataset.id =
                    province.code;


                provinceSelect.appendChild(
                    option
                );

            }
        );

    }
)

.catch(
    error => {

        console.error(
            "Không tải được tỉnh:",
            error
        );

    }
);


// =========================================================
// TỈNH → QUẬN
// =========================================================

provinceSelect.addEventListener(
    "change",
    function() {

        const selected =
            this.options[
                this.selectedIndex
            ];


        const provinceId =
            selected.dataset.id;


        districtSelect.innerHTML =
            `
            <option value="">
                -- Chọn quận / huyện --
            </option>
            `;


        wardSelect.innerHTML =
            `
            <option value="">
                -- Chọn phường / xã --
            </option>
            `;


        wardSelect.disabled =
            true;


        if (!provinceId) {

            districtSelect.disabled =
                true;

            return;
        }


        districtSelect.disabled =
            false;


        fetch(
            "https://provinces.open-api.vn/api/v2/p/"
            + provinceId
            + "?depth=2"
        )

        .then(
            response => response.json()
        )

        .then(
            data => {

                data.districts.forEach(
                    district => {

                        const option =
                            document.createElement(
                                "option"
                            );


                        option.value =
                            district.name;


                        option.textContent =
                            district.name;


                        option.dataset.id =
                            district.code;


                        districtSelect.appendChild(
                            option
                        );

                    }
                );

            }
        )

        .catch(
            error => {

                console.error(
                    "Không tải được quận/huyện:",
                    error
                );

            }
        );

    }
);


// =========================================================
// QUẬN → XÃ
// =========================================================

districtSelect.addEventListener(
    "change",
    function() {

        const selected =
            this.options[
                this.selectedIndex
            ];


        const districtId =
            selected.dataset.id;


        wardSelect.innerHTML =
            `
            <option value="">
                -- Chọn phường / xã --
            </option>
            `;


        if (!districtId) {

            wardSelect.disabled =
                true;

            return;
        }


        wardSelect.disabled =
            false;


        fetch(
            "https://provinces.open-api.vn/api/v2/d/"
            + districtId
            + "?depth=2"
        )

        .then(
            response => response.json()
        )

        .then(
            data => {

                data.wards.forEach(
                    ward => {

                        const option =
                            document.createElement(
                                "option"
                            );


                        option.value =
                            ward.name;


                        option.textContent =
                            ward.name;


                        wardSelect.appendChild(
                            option
                        );

                    }
                );

            }
        )

        .catch(
            error => {

                console.error(
                    "Không tải được phường/xã:",
                    error
                );

            }
        );

    }
);
