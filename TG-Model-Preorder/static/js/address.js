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
// TẢI FILE JSON LOCAL
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


        const rawData =
            await response.json();


        // =================================================
        // FILE V2.2.0 CÓ THỂ LÀ MẢNG TRỰC TIẾP
        // =================================================

        if (
            Array.isArray(rawData)
        ) {

            vietnamAddressData =
                rawData;

        }

        else if (
            Array.isArray(
                rawData.data
            )
        ) {

            vietnamAddressData =
                rawData.data;

        }

        else {

            throw new Error(
                "Cấu trúc JSON không hợp lệ"
            );

        }


        // =================================================
        // ĐỔ TỈNH / THÀNH
        // =================================================

        vietnamAddressData.forEach(
            province => {

                const provinceName =
                    province.FullName
                    || province.Name
                    || "";


                const provinceCode =
                    province.Code
                    || "";


                if (!provinceName) {

                    return;

                }


                const option =
                    createOption(
                        provinceName,
                        provinceName,
                        provinceCode
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


        if (
            !Array.isArray(
                vietnamAddressData
            )
        ) {

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
            vietnamAddressData.find(
                item =>
                    String(
                        item.Code
                    )
                    ===
                    String(
                        provinceCode
                    )
            );


        if (!province) {

            return;

        }


        const districts =
            province.District
            || province.Districts
            || [];


        if (
            !Array.isArray(
                districts
            )
        ) {

            return;

        }


        districts.forEach(
            district => {

                const districtName =
                    district.FullName
                    || district.Name
                    || "";


                const districtCode =
                    district.Code
                    || "";


                if (!districtName) {

                    return;

                }


                const option =
                    createOption(
                        districtName,
                        districtName,
                        districtCode
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


        if (
            !Array.isArray(
                vietnamAddressData
            )
        ) {

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
            vietnamAddressData.find(
                item =>
                    String(
                        item.Code
                    )
                    ===
                    String(
                        provinceCode
                    )
            );


        if (!province) {

            return;

        }


        const districts =
            province.District
            || province.Districts
            || [];


        const district =
            districts.find(
                item =>
                    String(
                        item.Code
                    )
                    ===
                    String(
                        districtCode
                    )
            );


        if (!district) {

            return;

        }


        const wards =
            district.Ward
            || district.Wards
            || [];


        if (
            !Array.isArray(
                wards
            )
        ) {

            return;

        }


        wards.forEach(
            ward => {

                const wardName =
                    ward.FullName
                    || ward.Name
                    || "";


                const wardCode =
                    ward.Code
                    || "";


                if (!wardName) {

                    return;

                }


                const option =
                    createOption(
                        wardName,
                        wardName,
                        wardCode
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
