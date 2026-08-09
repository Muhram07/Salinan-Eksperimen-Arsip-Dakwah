import { Octokit } from "https://esm.sh/octokit";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method Not Allowed" });
  }

  const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
  const GITHUB_OWNER = "Muhram07";
  const GITHUB_REPO = "ArsipDakwah";

  if (!GITHUB_TOKEN) {
    return res.status(500).json({ error: "GITHUB_TOKEN tidak ditemukan" });
  }

  try {
    const { title, category, tags, caption, content, imageBase64, filename, pdfBase64, pdfName } = req.body;
    const octokit = new Octokit({ auth: GITHUB_TOKEN });
    
    // 1. Simpan Gambar ke FOLDER TES: test-output/img/
    const imagePath = `test-output/img/${filename}`;
    await octokit.rest.repos.createOrUpdateFileContents({
      owner: GITHUB_OWNER, repo: GITHUB_REPO, path: imagePath,
      message: `[TES] Upload gambar: ${title}`, content: imageBase64, branch: "main",
    });

    // 2. Jika ada PDF, simpan ke FOLDER TES: test-output/pdf/
    let pdfPath = null;
    if (pdfBase64 && pdfName) {
      pdfPath = `test-output/pdf/${pdfName}`;
      await octokit.rest.repos.createOrUpdateFileContents({
        owner: GITHUB_OWNER, repo: GITHUB_REPO, path: pdfPath,
        message: `[TES] Upload PDF: ${pdfName}`, content: pdfBase64, branch: "main",
      });
    }

    // 3. Simpan JSON ke FOLDER TES: test-output/posters.json
    const testData = [{
      id: `test-${Date.now()}`,
      title, category, tags: tags.split(',').map(t => t.trim()),
      image: `/${imagePath}`,
      pdf: pdfPath ? `/${pdfPath}` : null,
      caption, content,
      date: new Date().toISOString().split('T')[0]
    }];

    // Tulis file JSON baru di folder tes (TIDAK akan menimpa data asli)
    await octokit.rest.repos.createOrUpdateFileContents({
      owner: GITHUB_OWNER, repo: GITHUB_REPO, path: "test-output/posters.json",
      message: `[TES] Membuat file JSON output`,
      content: Buffer.from(JSON.stringify(testData, null, 2)).toString('base64'),
      branch: "main",
    });

    return res.status(200).json({ 
      success: true, 
      message: "✅ [TES BERHASIL] Output tersimpan di folder 'test-output'! Silakan cek GitHub Anda." 
    });
  } catch (error) {
    return res.status(500).json({ success: false, message: error.message });
  }
      }
