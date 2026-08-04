async function timQuat() {

    const D =
    parseFloat(
        document.getElementById("diameter").value
    );

    const V =
    parseFloat(
        document.getElementById("velocity").value
    );

    const P =
    parseFloat(
        document.getElementById("pressure").value
    ) || 0;

    const loai =
        document.getElementById("loaiQuat").value;

    if (!D || !V) {

        alert("Nhập đường kính và vận tốc");

        return;
    }

    // mm -> m
    const d = D / 1000;

    // m3/h
    const Q =
        Math.PI *
        d *
        d /
        4 *
        V *
        3600;

    const res =
        await fetch(
            `/tim_quat?q=${Q}&p=${P}&loai=${encodeURIComponent(loai)}`
        );

    const fans =
        await res.json();

    let html = `
        <h3>
            Lưu lượng tính toán:
            ${Math.round(Q).toLocaleString()}
            m³/h
        </h3>
    `;

    if (fans.length === 0) {

        html += `
            <p>
                Không tìm thấy quạt phù hợp
            </p>
        `;

    } else {

        fans.forEach(fan => {

            html += `
<div class="fan-card">

    <h3>${fan.Model}</h3>

    <p>Loại: ${fan.Loai}</p>

    <p>
        Lưu lượng:
        ${fan.Qmin.toLocaleString()}
        -
        ${fan.Qmax.toLocaleString()}
        m³/h
    </p>

    <p>
        Áp suất:
        ${fan.Pmin.toLocaleString()}
        -
        ${fan.Pmax.toLocaleString()}
        Pa
    </p>

    <p>
        Công suất:
        ${fan.Kw} kW
    </p>

    <div class="btn-group">

        <button onclick="
            goiY(
                this,
                'thap',
                ${fan.Qmin},
                ${fan.Qmax}
            )
        ">
            Tháp lọc
        </button>

        <button onclick="
            goiY(
                this,
                'cyclone',
                ${fan.Qmin},
                ${fan.Qmax}
            )
        ">
            Cyclone
        </button>

        <button onclick="
            goiY(
                this,
                'than',
                ${fan.Qmin},
                ${fan.Qmax}
            )
        ">
            Thùng than
        </button>
        
        <button onclick="
    goiY(
        this,
        'tuivai',
        ${fan.Qmin},
        ${fan.Qmax}
    )
">
    Túi vải
</button>

    </div>

    <div class="device-result"></div>

</div>
`;
        });
    }

    document.getElementById("result").innerHTML =
        html;
}



async function goiY(btn, loai, qmin, qmax){

    const res = await fetch(
        `/goi_y?loai=${loai}&qmin=${qmin}&qmax=${qmax}`
    );

    const data = await res.json();

    let html = "";

    if(loai === "thap"){
        html += "<h4>Tháp lọc phù hợp</h4>";
    }

    if(loai === "cyclone"){
        html += "<h4>Cyclone phù hợp</h4>";
    }

    if(loai === "than"){
        html += "<h4>Thùng than phù hợp</h4>";
    }
    if(loai === "tuivai"){
    html += "<h4>HT lọc bụi túi vải phù hợp</h4>";
    }

    if(data.length === 0){

        html += `
        <p>
            Không tìm thấy thiết bị phù hợp
        </p>
        `;

    }else{

        data.forEach(item => {

            html += `
            <div class="device-card">

                <b>${item.Model}</b>

                <br>

                Q =
                ${Number(item.Q).toLocaleString()}
                m³/h

            </div>
            `;
        });

    }

    const fanCard =
        btn.closest(".fan-card");

    fanCard.querySelector(
        ".device-result"
    ).innerHTML = html;
}
