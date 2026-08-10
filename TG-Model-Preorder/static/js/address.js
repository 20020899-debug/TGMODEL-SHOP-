let vietnamAddressData = [];


// =========================================================
// ELEMENT
// =========================================================

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
// RESET QUẬN / HUYỆN
// =========================================================

function resetDistricts() {

    districtSelect.innerHTML =
        `
        <option value="">
            -- Chọn quận / huyện --
        </option>
        `;

    districtSelect.disabled =
        true;
}


// =========================================================
// RESET PHƯỜNG / XÃ
// =========================================================

function resetWards() {

    wardSelect.innerHTML =
        `
        <option value="">
            -- Chọn phường / xã --
        </option>
        `;

    wardSelect.disabled =
        true;
}


// =========================================================
// TẠO OPTION
// =========================================================

function createOption(
    name,
    code
) {

    const option =
        document.createElement(
            "option"
        );

    option.value =
        name;

    option.textContent =
        name;

    option.dataset.code =
        String(code);

    return option;
}


// =========================================================
// TẢI DỮ LIỆU ĐỊA CHỈ
// =========================================================

async function loadVietnamAddressData() {

    try {

        const response =
            await fetch(
                "/static/data/vietnam_address_63.json",
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                "HTTP " + response.status
            );
        }


        const data =
            await response.json();


        // File v2.2.0 phải là mảng trực tiếp
        if (!Array.isArray(data)) {

            throw new Error(
                "File JSON không phải dạng mảng"
            );
        }


        vietnamAddressData =
            data;


        // XÓA OPTION CŨ
        provinceSelect.innerHTML =
            `
            <option value="">
                -- Chọn tỉnh / thành phố --
            </option>
            `;


        // ĐỔ DANH SÁCH TỈNH
        vietnamAddressData.forEach(
            province => {

                if (
                    !province.FullName
                    ||
                    !province.Code
                ) {

                    return;
                }


                const option =
                    createOption(
                        province.FullName,
                        province.Code
                    );


                provinceSelect.appendChild(
                    option
                );

            }
        );


        provinceSelect.disabled =
            false;


        console.log(
            "Đã tải số tỉnh:",
            vietnamAddressData.length
        );

    }

    catch (error) {

        console.error(
            "Lỗi tải dữ liệu địa chỉ:",
            error
        );


        provinceSelect.innerHTML =
            `
            <option value="">
                Không tải được danh sách tỉnh
            </option>
            `;


        provinceSelect.disabled =
            true;

        resetDistricts();
        resetWards();
    }
}


// =========================================================
// CHỌN TỈNH → QUẬN / HUYỆN
// =========================================================

provinceSelect.addEventListener(
    "change",
    function() {

        resetDistricts();
        resetWards();


        const provinceCode =
            this.options[
                this.selectedIndex
            ].dataset.code;


        if (!provinceCode) {

            return;
        }


        const province =
            vietnamAddressData.find(
                item =>
                    String(item.Code)
                    ===
                    String(provinceCode)
            );


        if (!province) {

            return;
        }


        const districts =
            province.District;


        if (
            !Array.isArray(
                districts
            )
        ) {

            return;
        }


        districts.forEach(
            district => {

                if (
                    !district.FullName
                    ||
                    !district.Code
                ) {

                    return;
                }


                const option =
                    createOption(
                        district.FullName,
                        district.Code
                    );


                districtSelect.appendChild(
                    option
                );

            }
        );


        districtSelect.disabled =
            false;
    }
);


// =========================================================
// CHỌN QUẬN / HUYỆN → PHƯỜNG / XÃ
// =========================================================

districtSelect.addEventListener(
    "change",
    function() {

        resetWards();


        const provinceCode =
            provinceSelect.options[
                provinceSelect.selectedIndex
            ].dataset.code;


        const districtCode =
            this.options[
                this.selectedIndex
            ].dataset.code;


        if (
            !provinceCode
            ||
            !districtCode
        ) {

            return;
        }


        const province =
            vietnamAddressData.find(
                item =>
                    String(item.Code)
                    ===
                    String(provinceCode)
            );


        if (!province) {

            return;
        }


        const districts =
            province.District;


        if (
            !Array.isArray(
                districts
            )
        ) {

            return;
        }


        const district =
            districts.find(
                item =>
                    String(item.Code)
                    ===
                    String(districtCode)
            );


        if (!district) {

            return;
        }


        const wards =
            district.Ward;


        if (
            !Array.isArray(
                wards
            )
        ) {

            return;
        }


        wards.forEach(
            ward => {

                if (
                    !ward.FullName
                    ||
                    !ward.Code
                ) {

                    return;
                }


                const option =
                    createOption(
                        ward.FullName,
                        ward.Code
                    );


                wardSelect.appendChild(
                    option
                );

            }
        );


        wardSelect.disabled =
            false;
    }
);


// =========================================================
// KHỞI ĐỘNG
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        resetDistricts();
        resetWards();

        loadVietnamAddressData();
    }
);
