from flask import Flask, request, send_file
from flask_cors import CORS   # ✅ import CORS
from PIL import Image
from io import BytesIO
import datetime
import os

app = Flask(__name__)
CORS(app)   # ✅ Enable CORS for all routes

DPI = 300               # DPI (dots per inch)
OUTPUT_FORMAT = "PNG"   # "JPEG" or "PNG"
JPEG_QUALITY = 95


def resize_to_width_in_inches(img: Image.Image, inches: float, dpi: int) -> Image.Image:
    target_width_px = int(round(inches * dpi))
    w, h = img.size
    scale = target_width_px / float(w)
    target_height_px = max(1, int(round(h * scale)))
    return img.resize((target_width_px, target_height_px), Image.LANCZOS)


@app.route("/", methods=["GET"])
def home():
    return {"message": "Welcome to the Image Resize API. Use POST /convert with an image."}


@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return {"error": "No file part"}, 400

    f = request.files["file"]
    if f.filename == "":
        return {"error": "No selected file"}, 400

    size_inch = request.form.get("size", type=float)  # Example: 7 or 10

    try:
        img = Image.open(f.stream)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        base = os.path.splitext(os.path.basename(f.filename))[0]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        converted = resize_to_width_in_inches(img, size_inch, DPI)
        out = BytesIO()
        save_kwargs = {}

        if OUTPUT_FORMAT.upper() == "PNG":
            if converted.mode == "RGBA":
                converted = converted.convert("RGB")
            save_kwargs.update(dict(quality=JPEG_QUALITY, dpi=(DPI, DPI)))
        else:
            save_kwargs.update(dict(dpi=(DPI, DPI)))

        ext = "jpg" if OUTPUT_FORMAT.upper() == "JPEG" else OUTPUT_FORMAT.lower()
        out_name = f"{base}_{size_inch:.0f}in_{DPI}dpi_{timestamp}.{ext}"

        converted.save(out, format=OUTPUT_FORMAT.upper(), **save_kwargs)
        out.seek(0)

        return send_file(
            out,
            mimetype=f"image/{ext}",
            as_attachment=True,
            download_name=out_name
        )

    except Exception as e:
        return {"error": f"Error processing image: {e}"}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
####