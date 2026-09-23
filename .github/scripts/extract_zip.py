import os
import shutil
import zipfile
import yaml
import re
import sys
import json

# === DAFTAR URUTAN RESMI 12 BULAN HIJRIAH (TAMPILAN ESTETIK BERPETIK) ===
HIJRIAH_ORDER = [
    "Muharram",
    "Safar",
    "Rabi'ul Awwal",
    "Rabi'ul Akhir",
    "Jumadil Awwal",
    "Jumadil Akhir",
    "Rajab",
    "Sya'ban",
    "Ramadhan",
    "Syawwal",
    "Dzulqa'dah",
    "Dzulhijjah"
]

HIJRIAH_NORMALIZE_MAP = {}
for i, m in enumerate(HIJRIAH_ORDER, 1):
    base_name = m.lower()
    num = str(i)
    
    HIJRIAH_NORMALIZE_MAP[base_name] = m
    HIJRIAH_NORMALIZE_MAP[f"{base_name} ({num})"] = m
    HIJRIAH_NORMALIZE_MAP[f"{base_name}-{num}"] = m
    HIJRIAH_NORMALIZE_MAP[f"{base_name} {num}"] = m
    
    # Variasi ejaan tanpa tanda petik / variasi penulisan
    base_no_quote = base_name.replace("'", "").replace("’", "").replace("`", "")
    HIJRIAH_NORMALIZE_MAP[base_no_quote] = m
    HIJRIAH_NORMALIZE_MAP[f"{base_no_quote} ({num})"] = m
    
    base_single_w = base_name.replace('awwal', 'awal').replace('syawwal', 'syawal')
    HIJRIAH_NORMALIZE_MAP[base_single_w] = m
    HIJRIAH_NORMALIZE_MAP[f"{base_single_w} ({num})"] = m

# KAMUS BAKU KATEGORI
KATEGORI_REPLACE_MAP = {
    "aqidah": "Akidah",
    "akidah": "Akidah",
    "bidah": "Bid'ah",
    "bid'ah": "Bid'ah",
    "bid’ah": "Bid'ah",
    "fiqih": "Fikih",
    "fikih": "Fikih",
    "shalat": "Sholat",
    "sholat": "Sholat",
    "hadits": "Hadits",
    "dzikir": "Dzikir",
    "zikir": "Zikir",
    "doa": "Do'a",
    "do'a": "Do'a",
    "do’a": "Do'a",
}

def get_canonical_kategori(kat_str):
    """Mengembalikan nama kategori resmi dengan tanda petik untuk tampilan public/manifest."""
    if not kat_str:
        return "Umum"
    clean_str = kat_str.strip().lower().replace("’", "'").replace("‘", "'")
    if clean_str in HIJRIAH_NORMALIZE_MAP:
        return HIJRIAH_NORMALIZE_MAP[clean_str]
    if clean_str in KATEGORI_REPLACE_MAP:
        return KATEGORI_REPLACE_MAP[clean_str]
    return kat_str.strip().title()

def get_folder_slug(kat_str):
    """Menghasilkan nama folder fisik yang bersih 100% dari tanda petik & simbol."""
    canonical = get_canonical_kategori(kat_str)
    
    # 1. Konversi ke huruf kecil
    slug = canonical.lower()
    
    # 2. Hapus nomor urut dalam kurung jika ada
    slug = re.sub(r'\s*\(\d+\)', '', slug)
    
    # 3. BERSIHKAN TOTAL SEMUA JENIS TANDA PETIK
    slug = slug.replace("’", "").replace("'", "").replace("`", "").replace("‘", "")
    
    # 4. Ganti spasi/karakter non-alfanumerik dengan strip (-)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'[^a-z0-9\-]+', '', slug)
    
    # 5. Rapikan pemisah strip ganda
    slug = re.sub(r'-+', '-', slug).strip('-')
    
    return slug

def get_padded_number(num):
    return f"{num:0{max(3, len(str(num)))}d}"

def get_next_sequence(kategori_path):
    if not os.path.exists(kategori_path):
        return 1
    max_num = 0
    for folder in os.listdir(kategori_path):
        if os.path.isdir(os.path.join(kategori_path, folder)):
            parts = folder.split('-')
            if len(parts) > 1 and parts[-1].isdigit():
                try:
                    num = int(parts[-1])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
    return max_num + 1

def main():
    zip_dir = '_uploads'
    temp_dir = '_temp_extract'

    os.makedirs(zip_dir, exist_ok=True)
    zip_files = [f for f in os.listdir(zip_dir) if f.endswith('.zip')]

    if zip_files:
        for zip_filename in zip_files:
            zip_file_path = os.path.join(zip_dir, zip_filename)
            print(f"Memproses ZIP baru: {zip_file_path}")

            os.makedirs(temp_dir, exist_ok=True)
            try:
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            except Exception as e:
                print(f"Gagal mengekstrak {zip_filename}: {e}")
                continue

            target_folder = None
            md_path = os.path.join(temp_dir, 'poster.md')
            if os.path.exists(md_path):
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    yaml_match = re.search(r'---(.*?)---', content, re.DOTALL)
                    if yaml_match:
                        try:
                            data = yaml.safe_load(yaml_match.group(1))
                            raw_kategori = data.get('kategori', 'Unknown')
                            judul = data.get('judul', 'Unknown')

                            canonical_kategori = get_canonical_kategori(raw_kategori)
                            kat_folder_slug = get_folder_slug(canonical_kategori)

                            slug_base = re.sub(r'[^a-z0-9]+', '-', judul.lower()).strip('-')
                            if not slug_base: 
                                slug_base = 'poster'

                            kategori_path = os.path.join('posters', kat_folder_slug)
                            next_num = get_next_sequence(kategori_path)
                            num_str = get_padded_number(next_num)
                            final_slug = f"{slug_base}-{num_str}"
                            
                            target_folder = os.path.join('posters', kat_folder_slug, final_slug)
                        except Exception as e:
                            print(f"Gagal parsing YAML di poster.md: {e}")
                    
            if not target_folder:
                fallback_name = os.path.splitext(zip_filename)[0]
                target_folder = os.path.join('posters', 'unknown', fallback_name)

            os.makedirs(target_folder, exist_ok=True)
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(target_folder, file)
                    shutil.move(src_path, dst_path)

            shutil.rmtree(temp_dir)
            os.remove(zip_file_path)
            print("ZIP berhasil diekstrak dan dipindahkan.")

    scan_and_reconstruct_posters()

def scan_and_reconstruct_posters():
    print("Memindai & merekonstruksi seluruh struktur folder dan file poster.md...")
    manifest_path = "manifest.json"
    existing_emoji_map = {}

    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                old_manifest = json.load(f)
                existing_emoji_map = old_manifest.get('kategori_emoji', {})
        except Exception as e:
            print(f"Gagal membaca manifest.json lama: {e}")

    for month in HIJRIAH_ORDER:
        if month not in existing_emoji_map:
            existing_emoji_map[month] = "🌙"

    base_poster_path = "posters"
    if not os.path.exists(base_poster_path):
        print("Folder posters belum ada.")
        return

    all_posters_temp = []
    
    for kat_folder in os.listdir(base_poster_path):
        kat_folder_path = os.path.join(base_poster_path, kat_folder)
        if os.path.isdir(kat_folder_path):
            for poster_folder in os.listdir(kat_folder_path):
                poster_path = os.path.join(kat_folder_path, poster_folder)
                if os.path.isdir(poster_path):
                    md_file_path = os.path.join(poster_path, 'poster.md')
                    if os.path.exists(md_file_path):
                        all_posters_temp.append((poster_path, md_file_path))

    manifest_data = {
        "kategori_list": [],
        "kategori_emoji": existing_emoji_map,
        "total_poster": 0,
        "posters": []
    }
    
    kategori_terpakai_set = set()

    for poster_path, md_file_path in all_posters_temp:
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            yaml_match = re.search(r'---(.*?)---', content, re.DOTALL)
            if yaml_match:
                yaml_raw = yaml_match.group(1)
                data = yaml.safe_load(yaml_raw) or {}
                
                raw_kategori = data.get('kategori', 'Umum')
                canonical_kat = get_canonical_kategori(raw_kategori)
                
                # Pertahankan nama estetik di frontmatter
                data['kategori'] = canonical_kat
                kategori_terpakai_set.add(canonical_kat)

                new_emoji = data.get('kategori_emoji')
                if new_emoji and new_emoji != '📂':
                    manifest_data['kategori_emoji'][canonical_kat] = new_emoji

                new_yaml_content = yaml.dump(data, allow_unicode=True, sort_keys=False)
                new_full_content = f"---\n{new_yaml_content}---\n" + content[yaml_match.end():]
                
                with open(md_file_path, 'w', encoding='utf-8') as f:
                    f.write(new_full_content)

                # Gunakan slug tanpa petik untuk penataan folder fisik
                target_kat_slug = get_folder_slug(canonical_kat)
                current_parent_slug = os.path.basename(os.path.dirname(poster_path))
                
                correct_poster_dir = poster_path
                if current_parent_slug != target_kat_slug:
                    target_kat_path = os.path.join(base_poster_path, target_kat_slug)
                    os.makedirs(target_kat_path, exist_ok=True)
                    
                    folder_name = os.path.basename(poster_path)
                    new_destination = os.path.join(target_kat_path, folder_name)
                    
                    if not os.path.exists(new_destination):
                        shutil.move(poster_path, new_destination)
                        correct_poster_dir = new_destination
                        print(f"🔀 Memindahkan poster ke folder bersih: {target_kat_slug} ({folder_name})")
                    else:
                        for item in os.listdir(poster_path):
                            s_item = os.path.join(poster_path, item)
                            d_item = os.path.join(new_destination, item)
                            if not os.path.exists(d_item):
                                shutil.move(s_item, d_item)
                        shutil.rmtree(poster_path)
                        correct_poster_dir = new_destination

                real_folder_name = os.path.basename(correct_poster_dir)
                real_kategori_folder = os.path.basename(os.path.dirname(correct_poster_dir))
                data['path'] = f"{real_kategori_folder}/{real_folder_name}"
                
                manifest_data['posters'].append(data)
                manifest_data['total_poster'] += 1

        except Exception as e:
            print(f"Gagal merekonstruksi {md_file_path}: {e}")

    # Menghapus folder kategori lama yang kosong / berpetik
    for kat_folder in os.listdir(base_poster_path):
        kat_folder_path = os.path.join(base_poster_path, kat_folder)
        if os.path.isdir(kat_folder_path) and not os.listdir(kat_folder_path):
            shutil.rmtree(kat_folder_path)
            print(f"🧹 Menghapus folder kategori kosong: {kat_folder}")

    hijriah_terpakai = [m for m in HIJRIAH_ORDER if m in kategori_terpakai_set]
    non_hijriah = sorted(list(kategori_terpakai_set - set(HIJRIAH_ORDER)))

    manifest_data['kategori_list'] = hijriah_terpakai + non_hijriah

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Rekonstruksi Selesai! Total Poster Aktif: {manifest_data['total_poster']}")

if __name__ == "__main__":
    main()
