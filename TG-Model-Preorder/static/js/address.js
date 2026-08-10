let vietnamAddressData = null;


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
    value,
    text,
    code
) {

    const option =
        document.createElement(
            "option"
        );


    option.value =
        value;


    option.textContent =
        text;


    if (code) {

        option.dataset.code =
            code;

    }


    return option;

}


// =========================================================
// TẢI DỮ LIỆU ĐỊA CHỈ LOCAL
// =========================================================

async function loadVietnamAddressData() {

    try {

        const response =
            await fetch(
                "/static/data/vietnam_address_63.json",
                {
                    cache: "force-cache"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Không tải được dữ liệu địa chỉ"
            );

        }


        vietnamAddressData =
            await response.json();


        const provinces =
            vietnamAddressData.provinces;


        if (
            !Array.isArray(provinces)
        ) {

            throw new Error(
                "Dữ liệu tỉnh/thành không hợp lệ"
            );

        }


        provinces.forEach(
            province => {

                const option =
                    createOption(
                        province.name,
                        province.name,
                        province.code
                    );


                provinceSelect.appendChild(
                    option
                );

            }
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


        if (!vietnamAddressData) {

            return;

        }


        const provinceCode =
            this.options[
                this.selectedIndex
            ].dataset.code;


        if (!provinceCode) {

            return;

        }


        const province =
            vietnamAddressData.provinces.find(
                item =>
                    item.code === provinceCode
            );


        if (
            !province
            ||
            !Array.isArray(
                province.districts
            )
        ) {

            return;

        }


        province.districts.forEach(
            district => {

                const option =
                    createOption(
                        district.name,
                        district.name,
                        district.code
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


        if (!vietnamAddressData) {

            return;

        }


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
            vietnamAddressData.provinces.find(
                item =>
                    item.code === provinceCode
            );


        if (!province) {

            return;

        }


        const district =
            province.districts.find(
                item =>
                    item.code === districtCode
            );


        if (
            !district
            ||
            !Array.isArray(
                district.wards
            )
        ) {

            return;

        }


        district.wards.forEach(
            ward => {

                const option =
                    createOption(
                        ward.name,
                        ward.name,
                        ward.code
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