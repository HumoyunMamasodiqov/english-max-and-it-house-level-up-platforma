import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone


FONT_DIR = os.path.join(settings.BASE_DIR, 'static', 'fonts')
WINDIR = os.environ.get('WINDIR', 'C:\\Windows')


def _get_font(name, size):
    paths = [
        os.path.join(FONT_DIR, name),
        os.path.join(FONT_DIR, name.lower()),
        os.path.join(WINDIR, 'Fonts', name),
        os.path.join(WINDIR, 'Fonts', name.lower()),
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_certificate_image(student_name, group_name, teacher_name, level, score, background_path):
    try:
        bg = Image.open(background_path).convert("RGBA")
    except Exception:
        return None

    img_w, img_h = bg.size
    draw = ImageDraw.Draw(bg)

    student_name = student_name.title()

    name_font = _get_font('Parisienne-Regular.ttf', int(img_w * 0.065))
    level_font = _get_font('arial.ttf', int(img_w * 0.021))
    teacher_font = _get_font('arial.ttf', int(img_w * 0.018))

    draw.text(
        (img_w / 2, img_h * 0.52),
        student_name,
        fill="#000000",
        font=name_font,
        anchor="mm",
        align="center"
    )

    level_text = level if level else "English Proficiency Level"
    draw.text(
        (img_w / 2, img_h * 0.71),
        level_text,
        fill="#000000",
        font=level_font,
        anchor="mm",
        align="center"
    )

    if teacher_name:
        teacher_x = img_w * 0.91
        teacher_y = img_h * 0.94
        draw.text(
            (teacher_x, teacher_y),
            teacher_name,
            fill="#ffffff",
            font=teacher_font,
            anchor="mm",
            align="center"
        )   

    output = BytesIO()
    bg = bg.convert("RGB")
    bg.save(output, format="PNG", quality=95)
    output.seek(0)

    return output


def save_certificate_pdf(student_name, group_name, teacher_name, level, score, background_path):
    img_data = generate_certificate_image(student_name, group_name, teacher_name, level, score, background_path)
    if img_data is None:
        return None

    safe_name = student_name.replace(' ', '_').replace('/', '_')
    filename = f"certificate_{safe_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
    return ContentFile(img_data.read(), name=filename)
