import fitz  # PyMuPDF
from PIL import Image
import io
import os

SIGNATURE_KEYWORDS = [
    "signature", "imza", "sign here", "buraya imza",
    "authorized signature", "yetkili imza", "imzası"
]

def load_pdf(pdf_path: str) -> fitz.Document:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    return fitz.open(pdf_path)

def get_page_count(doc: fitz.Document) -> int:
    return len(doc)

def render_page(doc: fitz.Document, page_number: int, dpi: int = 150) -> Image.Image:
    page = doc[page_number]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    return Image.open(io.BytesIO(img_bytes))

def find_signature_areas(doc: fitz.Document, page_number: int) -> list:
    page = doc[page_number]
    found = []

    for keyword in SIGNATURE_KEYWORDS:
        instances = page.search_for(keyword)
        for rect in instances:
            area = {
                "x": rect.x0,
                "y": rect.y1 + 2,
                "w": max(rect.width * 3, 150),
                "h": 40,
                "reason": f"Keyword match: '{keyword}'"
            }
            found.append(area)

    paths = page.get_drawings()
    page_width = page.rect.width

    for path in paths:
        rect = path["rect"]
        width = rect.x1 - rect.x0
        height = rect.y1 - rect.y0

        if width > page_width * 0.2 and height < 5:
            area = {
                "x": rect.x0,
                "y": rect.y0 - 35,
                "w": width,
                "h": 35,
                "reason": "Horizontal line (signature line)"
            }
            found.append(area)

    return found

def place_signature(pdf_path, page_number, x, y, signature_img_path, width=150, height=60, output_path=None):
    doc = fitz.open(pdf_path)
    page = doc[page_number]

    if not os.path.exists(signature_img_path):
        raise FileNotFoundError(f"Signature image not found: {signature_img_path}")

    sig_img = Image.open(signature_img_path).convert("RGBA")
    sig_img = sig_img.resize((int(width * 2), int(height * 2)), Image.LANCZOS)

    img_bytes = io.BytesIO()
    sig_img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    rect = fitz.Rect(x, y, x + width, y + height)
    page.insert_image(rect, stream=img_bytes.read(), overlay=True)

    if output_path is None:
        base, ext = os.path.splitext(pdf_path)
        output_path = f"{base}_signed{ext}"

    doc.save(output_path)
    doc.close()
    return output_path

def pt_to_px(pt_value: float, dpi: int = 150) -> float:
    return pt_value * (dpi / 72)

def px_to_pt(px_value: float, dpi: int = 150) -> float:
    return px_value * (72 / dpi)


if __name__ == "__main__":
    # Create test PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Internship Application Form", fontsize=20)
    page.insert_text((100, 200), "Full Name: ____________________")
    page.insert_text((100, 300), "Signature: ____________________")
    doc.save("test.pdf")
    doc.close()
    print("test.pdf created!")

    # Create test signature image
    img = Image.new("RGBA", (300, 100), (255, 255, 255, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), "John Doe", fill=(0, 0, 200, 255))
    img.save("signature.png")
    print("signature.png created!")

    # Test load and page count
    doc = load_pdf("test.pdf")
    print(f"Page count: {get_page_count(doc)}")

    # Test signature area detection
    areas = find_signature_areas(doc, 0)
    print(f"Signature areas found: {len(areas)}")
    for a in areas:
        print(f"  {a['reason']} -> x={a['x']:.1f}, y={a['y']:.1f}")

    doc.close()

    # Test place signature
    output = place_signature("test.pdf", 0, 100, 290, "signature.png")
    print(f"Signed PDF saved: {output}")