import os
import zipfile


def extract_zip(zip_path, dest_dir):
    extracted = []
    os.makedirs(dest_dir, exist_ok=True)
    base = os.path.realpath(dest_dir)
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            target = os.path.realpath(os.path.join(base, info.filename))
            if not target.startswith(base):
                raise ValueError("unsafe archive entry: " + info.filename)
            if info.is_dir():
                os.makedirs(target, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(zf.read(info))
            extracted.append(info.filename)
    return extracted
