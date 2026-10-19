import os
import zipfile


def extract_zip(zip_path, dest_dir):
    # VULNERABLE: each entry name is joined to dest_dir with no checks
    extracted = []
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            target = os.path.join(dest_dir, info.filename)
            if info.is_dir():
                os.makedirs(target, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(zf.read(info))
            extracted.append(info.filename)
    return extracted
