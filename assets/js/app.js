let posterData = [];

async function loadPosters() {
    try {
        const res = await fetch("/data/posters.json");
        if (!res.ok) throw new Error();
        posterData = await res.json();
        renderPoster(posterData);
        if (typeof updateCategoryCount === "function") {
            updateCategoryCount();
        }
    } catch (e) {
        document.getElementById("post-list").innerHTML = `<div class="loading">❌ Gagal memuat poster.</div>`;
    }
}

function renderPoster(data) {
    const container = document.getElementById("post-list");
    container.innerHTML = "";
    if (!data || data.length === 0) {
        container.innerHTML = `<div class="loading">Tidak ada hasil.</div>`;
        return;
    }
    data.forEach(item => {
        container.innerHTML += `
        <div class="poster">
            <img src="${item.image}" alt="${item.title}" onclick="bukaPoster('${item.id}')">
            <h3 onclick="bukaPoster('${item.id}')">${item.title}</h3>
            <p>${item.caption}</p>
            <small>📂 ${item.category}</small>
            <button onclick="event.stopPropagation();toggleCaption('${item.id}')">📖 Baca Caption</button>
            <button onclick="event.stopPropagation();copyCaption('${item.id}')">📋 Copy Caption</button>
            <div id="caption-${item.id}" class="caption-box">${item.content}</div>
        </div>`;
    });
}

function bukaPoster(id) {
    location.href = "/poster.html?id=" + encodeURIComponent(id);
}

function toggleCaption(id) {
    const box = document.getElementById("caption-" + id);
    if (!box) return;
    if (box.style.display === "block") {
        box.style.display = "none";
    } else {
        box.style.display = "block";
        box.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

function copyCaption(id) {
    const poster = posterData.find(p => p.id === id);
    if (!poster) return;
    navigator.clipboard.writeText(poster.content);
    alert("✅ Caption berhasil disalin");
}

const search = document.getElementById("search");
const resultBox = document.createElement("div");
resultBox.id = "search-result";
search.after(resultBox);

search.addEventListener("input", function() {
    const key = this.value.trim().toLowerCase();
    if (key === "") {
        resultBox.innerHTML = "";
        renderPoster(posterData);
        return;
    }
    const hasil = posterData.filter(item => {
        const tags = (item.tags || []).join(" ").toLowerCase();
        return (item.title.toLowerCase().includes(key) || item.category.toLowerCase().includes(key) || item.caption.toLowerCase().includes(key) || tags.includes(key));
    });
    renderPoster(hasil);
    resultBox.innerHTML = "";
    if (hasil.length === 0) {
        resultBox.innerHTML = `<div class="search-item">Tidak ada hasil.</div>`;
        return;
    }
    hasil.forEach(item => {
        resultBox.innerHTML += `<div class="search-item" onclick="pilihPoster('${item.id}')"><b>📚 ${item.title}</b> <small>📂 ${item.category}</small></div>`;
    });
});

function pilihPoster(id) {
    resultBox.innerHTML = "";
    search.value = "";
    const hasil = posterData.filter(item => item.id === id);
    renderPoster(hasil);
    setTimeout(() => {
        document.getElementById("post-list").scrollIntoView({ behavior: "smooth" });
    }, 150);
}

function filterCategory(category) {
    resultBox.innerHTML = "";
    search.value = "";
    const hasil = posterData.filter(item => item.category === category);
    renderPoster(hasil);
    document.getElementById("post-list").scrollIntoView({ behavior: "smooth" });
}

loadPosters();
