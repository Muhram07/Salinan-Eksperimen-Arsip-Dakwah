let categoryData = [];

/* =========================
   LOAD KATEGORI
========================= */

async function loadCategories() {

    try {

        const res = await fetch("/data/categories.json");

        if (!res.ok) throw new Error();

        categoryData = await res.json();

        renderCategories();

    } catch (e) {

        document.getElementById("category-list").innerHTML = `
        <div class="loading">
            ❌ Gagal memuat kategori.
        </div>
        `;

    }

}

/* =========================
   RENDER KATEGORI
========================= */

function renderCategories() {

    const container =
    document.getElementById("category-list");

    container.innerHTML = "";

    categoryData.forEach(cat => {

        // Pastikan nama kategori bersih dari spasi
        const kategoriName = cat.name.trim();

        const jumlah = posterData.filter(p =>
            p.category.trim() === kategoriName
        ).length;

        container.innerHTML += `

        <div
        class="card"
        id="cat-${cat.id}"
        onclick="pilihKategori('${kategoriName}', '${cat.id}')">

            <div style="font-size:42px;">
                ${cat.icon}
            </div>

            <h3 style="
                margin-top:12px;
                color:white;
                font-size:24px;
            ">
                ${kategoriName}
            </h3>

            <p style="
                margin-top:10px;
                color:#bdbdbd;
                line-height:1.6;
                font-size:15px;
            ">
                ${cat.description}
            </p>

            <div style="
                margin-top:18px;
                color:#FFD700;
                font-weight:bold;
            ">
                📄 ${jumlah} Poster
            </div>

        </div>

        `;

    });

}

/* =========================
   UPDATE JUMLAH POSTER
========================= */

function updateCategoryCount() {

    if (categoryData.length === 0) return;

    renderCategories();

}

/* =========================
   PILIH KATEGORI - PERBAIKAN PALING PENTING
========================= */

function pilihKategori(category, id) {

    document.querySelectorAll(".card").forEach(card => {

        card.style.borderColor = "#222";
        card.style.boxShadow = "none";

    });

    const aktif =
    document.getElementById("cat-" + id);

    if (aktif) {

        aktif.style.borderColor = "#FFD700";
        aktif.style.boxShadow =
        "0 0 20px rgba(255,215,0,.35)";

    }

    // Panggil fungsi filterCategory yang ada di app.js
    // Pastikan category dikirim dengan nama yang sudah dipastikan benar
    if (typeof filterCategory === "function") {
        filterCategory(category);
    } else {
        console.error("Fungsi filterCategory tidak ditemukan di app.js!");
    }

}

/* ========================= */

loadCategories();
