export default {
  async fetch(request, env, ctx) {
    // 1. Hanya terima metode POST
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    // 2. Verifikasi API Key (Lapisan keamanan dasar)
    const apiKey = request.headers.get("X-API-KEY");
    if (apiKey !== env.API_SECRET) {
      return new Response(JSON.stringify({ error: "Unauthorized: Invalid API Key" }), { status: 401 });
    }

    try {
      // 3. Ambil file ZIP dan nama file dari FormData
      const formData = await request.formData();
      const file = formData.get("file");
      const filename = formData.get("filename");

      if (!file || !filename) {
        return new Response(JSON.stringify({ error: "Missing file or filename" }), { status: 400 });
      }

      // 4. Siapkan endpoint GitHub API
      const repo = "Muhram07/Salinan-Eksperimen-Arsip-Dakwah";
      const path = `_uploads/${filename}`;
      const url = `https://api.github.com/repos/${repo}/contents/${path}`;

      // 5. Ubah file menjadi Base64 untuk dikirim ke GitHub
      const contentArrayBuffer = await file.arrayBuffer();
      const base64Content = btoa(String.fromCharCode(...new Uint8Array(contentArrayBuffer)));

      // 6. Kirim request PUT ke GitHub API
      const response = await fetch(url, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: `📤 Add ${filename} via API`,
          content: base64Content
        })
      });

      const responseData = await response.json();

      if (!response.ok) {
        console.error("GitHub API Error:", responseData);
        return new Response(JSON.stringify({ error: responseData.message || "GitHub API Error" }), { status: response.status });
      }

      // 7. Kirim balasan sukses ke Panel Admin
      return new Response(JSON.stringify({ success: true, message: "ZIP berhasil dikirim ke GitHub!" }), { status: 200 });

    } catch (error) {
      console.error("Worker Internal Error:", error);
      return new Response(JSON.stringify({ error: "Internal Server Error" }), { status: 500 });
    }
  }
};
