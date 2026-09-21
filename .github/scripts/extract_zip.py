import os
import shutil
import zipfile
import yaml
import re
import sys
import json

# ==========================================
# PEMETAAN NAMA KATEGORI OTOMATIS (12 BULAN HIJRIAH & KATEGORI UMUM)
# ==========================================
CATEGORY_MAP = {
    # 1. Muharram
    "muharram": "Muharram (1)",
    "muharram (1)": "Muharram (1)",
    
    # 2. Safar
    "safar": "Safar (2)",
    "safar (2)": "Safar (2)",
    
    # 3. Rabi'ul Awal
    "rabiul awal": "Rabi'ul Awal (3)",
    "rabi'ul awal": "Rabi'ul Awal (3)",
    "rabi'ul awal (3)": "Rabi'ul Awal (3)",
    
    # 4. Rabi'ul Akhir
    "rabiul akhir": "Rabi'ul Akhir (4)",
    "rabi'ul akhir": "Rabi'ul Akhir (4)",
    "rabi'ul akhir (4)": "Rabi'ul Akhir (4)",
    
    # 5. Jumadil Awal
    "jumadil awal": "Jumadil Awal (5)",
    "jumadal ula": "Jumadil Awal (5)",
    "jumadil awal (5)": "Jumadil Awal (5)",
    
    # 6. Jumadil Akhir
    "jumadil akhir": "Jumadil Akhir (6)",
    "jumadal akhirah": "Jumadil Akhir (6)",
    "jumadil akhir (6)": "Jumadil Akhir (6)",
    
    # 7. Rajab
    "rajab": "Rajab (7)",
    "rajab (7)": "Rajab (7)",
    
    # 8. Sya'ban
    "sya'ban": "Sya'ban (8)",
    "syaban": "Sya'ban (8)",
    "sya'ban (8)": "Sya'ban (8)",
    
    # 9. Ramadhan
    "ramadhan": "Ramadhan (9)",
    "ramadan": "Ramadhan (9)",
    "ramadhan (9)": "Ramadhan (9)",
    
    # 10. Syawwal
    "syawwal": "Syawwal (10)",
    "syawal": "Syawwal (10)",
    "syawwal (10)": "Syawwal (10)",
    
    # 11. Dzulqa'dah
    "dzulqa'dah": "Dzulqa'dah (11)",
    "dzulqadah": "Dzulqa'dah (11)",
    "dzulqa'dah (11)": "Dzulqa'dah (11)",
    
    # 12. Dzulhijjah
    "dzulhijjah": "Dzulhijjah (12)",
    "dzulhijjah (12)": "Dzulhijjah (12)",
}

HIJRIAH_ORDER = [
    "Muharram (1)",
    "Safar (2)",
    "Rabi'ul Awal (3)",
    "Rabi'ul Akhir (4)",
    "Jumadil Awal (5)",
    "Jumadil Akhir (6)",
    "Rajab (7)",
    "Sya'ban (8)",
    "Ramadhan (9)",
    "Syawwal (10)",
    "Dzulqa'dah (11)",
    "Dzulhijjah (12)"
]

HIJRIAH_MONTHS_SET = set(HIJRIAH_ORDER)

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

def normalize_category_name(kat_str):
    if not kat_str:
        return "Unknown"
    clean_key = kat_str.strip().lower()
    return CATEGORY_MAP.get(clean_key, kat_str.strip())

def consolidate_folders():
    """Memindahkan isi seluruh folder fisik lama/tidak standar ke folder resmi standar"""
    base_poster_path = "posters"
    if not os.path.exists(base_poster_path):
        return

    for folder_name in os.listdir(base_poster_path):
        folder_path = os.path.join(base_poster_path, folder_name)
        if not os.path.isdir(folder_path):
            continue

        normalized_cat = normalize_category_name(folder_name)
        target_folder_name = re.sub(r'[^a-z0-9]+', '-', normalized_cat.lower()).strip('-')

        # Jika nama folder fisik tidak sesuai standar (misal: 'ramadhan' != 'ramadhan-9' atau 'syawal' != 'syawwal-10')
        if folder_name != target_folder_name:
            target_folder_path = os.path.join(base_poster_path, target_folder_name)
            os.makedirs(target_folder_path, exist_ok=True)

            print(f"Mengonsolidasi folder: {folder_path} -> {target_folder_path}")

            for subfolder in os.listdir(folder_path):
                src_sub = os.path.join(folder_path, subfolder)
                if os.path.isdir(src_sub):
                    dst_sub = os.path.join(target_folder_path, subfolder)

                    # Jika ada nama poster yang sama di folder target, perbarui penomorannya
                    if os.path.exists(dst_sub):
                        next_num = get_next_sequence(target_folder_path)
                        num_str = get_padded_number(next_num)
                        slug_base = re.sub(r'-\d+$', '', subfolder)
                        dst_sub = os.path.join(target_folder_path, f"{slug_base}-{num_str}")

                    shutil.move(src_sub, dst_sub)

                    # Perbarui atribut kategori di poster.md
                    md_path = os.path.join(dst_sub, 'poster.md')
                    if os.path.exists(md_path):
                        try:
                            with open(md_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            yaml_match = re.search(r'---(.*?)---', content, re.DOTALL)
                            if yaml_match:
                                data = yaml.safe_load(yaml_match.group(1))
                                data['kategori'] = normalized_cat
                                new_yaml = yaml.dump(data, allow_unicode=True, sort_keys=False)
                                new_content = f"---\n{new_yaml}---" + content[yaml_match.end():]
                                with open(md_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                        except Exception as e:
                            print(f"Gagal memperbarui MD di {md_path}: {e}")

            # Hapus folder lama setelah semua isinya dipindahkan
            if os.path.exists(folder_path) and not os.listdir(folder_path):
                os.rmdir(folder_path)

def main():
    zip_dir = '_uploads'
    temp_dir = '_temp_extract'

    if not os.path.exists(zip_dir):
        print("Folder '_uploads' tidak ditemukan. Menjalankan pemindaian manifest...")
        scan_and_repair()
        return

    zip_files = [f for f in os.listdir(zip_dir) if f.endswith('.zip')]
    
    if not zip_files:
        print("Tidak ada file ZIP ditemukan di _uploads. Memperbarui manifest...")
        scan_and_repair()
        return

    for zip_filename in zip_files:
        zip_file_path = os.path.join(zip_dir, zip_filename)
        print(f"Memproses ZIP: {zip_file_path}")

        os.makedirs(temp_dir, exist_ok=True)
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        target_folder = None

        md_path = os.path.join(temp_dir, 'poster.md')
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                yaml_match = re.search(r'---(.*?)---', content, re.DOTALL)
                if yaml_match:
                    try:
                        data = yaml.safe_load(yaml_match.group(1))
                        kategori = data.get('kategori', 'Unknown')
                        judul = data.get('judul', 'Unknown')

                        slug_base = re.sub(r'[^a-z0-9]+', '-', judul.lower()).strip('-')
                        if not slug_base: 
                            slug_base = 'poster'

                        display_kategori = normalize_category_name(kategori)
                        kategori_folder_name = re.sub(r'[^a-z0-9]+', '-', display_kategori.lower()).strip('-')
                        kategori_path = os.path.join('posters', kategori_folder_name)
                        
                        next_num = get_next_sequence(kategori_path)
                        num_str = get_padded_number(next_num)
                        final_slug = f"{slug_base}-{num_str}"
                        
                        target_folder = os.path.join('posters', kategori_folder_name, final_slug)
                        print(f"Target folder: {target_folder}")

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

    scan_and_repair()

def scan_and_repair():
    # Perbaiki dan gabungkan seluruh folder tidak teratur terlebih dahulu
    consolidate_folders()

    print("Memindai & memperbarui struktur kategori...")
    
    manifest_path = "manifest.json"
    existing_emoji_map = {}

    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                old_manifest = json.load(f)
                existing_emoji_map = old_manifest.get('kategori_emoji', {})
        except Exception as e:
            print(f"Gagal membaca manifest.json lama: {e}")

    categories_set = set(HIJRIAH_ORDER)

    manifest_data = {
        "kategori_list": [],
        "kategori_emoji": existing_emoji_map,
        "total_poster": 0,
        "posters": []
    }
    
    for month in HIJRIAH_ORDER:
        if month not in manifest_data['kategori_emoji']:
            manifest_data['kategori_emoji'][month] = "🌙"

    base_poster_path = "posters"
    
    if os.path.exists(base_poster_path):
        for kategori in os.listdir(base_poster_path):
            kategori_path = os.path.join(base_poster_path, kategori)
            if os.path.isdir(kategori_path):
                for poster_folder in os.listdir(kategori_path):
                    poster_path = os.path.join(kategori_path, poster_folder)
                    if os.path.isdir(poster_path):
                        md_file_path = os.path.join(poster_path, 'poster.md')
                        if os.path.exists(md_file_path):
                            try:
                                with open(md_file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    yaml_match = re.search(r'---(.*?)---', content, re.DOTALL)
                                    if yaml_match:
                                        data = yaml.safe_load(yaml_match.group(1))
                                        raw_kategori = data.get('kategori', kategori)
                                        
                                        display_kategori = normalize_category_name(raw_kategori)
                                        categories_set.add(display_kategori)
                                        
                                        real_folder_name = os.path.basename(poster_path)
                                        real_kategori = os.path.basename(os.path.dirname(poster_path))
                                        
                                        data['kategori'] = display_kategori
                                        data['path'] = f"{real_kategori.lower()}/{real_folder_name}"
                                        
                                        new_emoji = data.get('kategori_emoji')
                                        if new_emoji and new_emoji != '📂':
                                            manifest_data['kategori_emoji'][display_kategori] = new_emoji
                                        
                                        manifest_data['posters'].append(data)
                                        manifest_data['total_poster'] += 1

                            except Exception as e:
                                print(f"Gagal membaca {md_file_path}: {e}")

    other_categories = sorted([c for c in categories_set if c not in HIJRIAH_MONTHS_SET])
    manifest_data['kategori_list'] = HIJRIAH_ORDER + other_categories

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    
    print("Selesai! Seluruh folder fisik berhasil diselaraskan dan manifest.json telah diperbarui.")

if __name__ == "__main__":
    main()
