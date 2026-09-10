import glob
import io
import os
import time

import cv2
from deep_translator import GoogleTranslator
from gtts import gTTS
import numpy as np
from PIL import Image
import pytesseract
import streamlit as st

# Configuración básica
st.set_page_config(
    page_title="Lector Divertido - OCR y Voz", layout="centered"
)


# Limpieza de archivos de audio antiguos
def remove_old_files(days=1):
    os.makedirs("temp", exist_ok=True)
    mp3_files = glob.glob("temp/*.mp3")
    now = time.time()
    n_days = days * 86400
    for f in mp3_files:
        if os.stat(f).st_mtime < now - n_days:
            try:
                os.remove(f)
            except OSError:
                pass


remove_old_files(1)

# --- INTERFAZ PRINCIPAL ---
st.title("🎙️ Lectura Divertida de Imágenes (OCR + Voz)")
st.caption(
    "Extrae texto de cualquier foto y escúchalo traducido o con voces y"
    " acentos chistosos."
)

# Imagen decorativa previa
try:
    image_banner = Image.open("OIG7.jpg")
    st.image(
        image_banner,
        use_container_width=True,
        caption="¡Transforma tus fotos en audio con estilo!",
    )
except FileNotFoundError:
    pass

st.divider()

# Mapeos de idiomas y acentos
IDIOMAS = {
    "Español": {"ocr": "spa", "code": "es"},
    "Inglés": {"ocr": "eng", "code": "en"},
    "Francés": {"ocr": "fra", "code": "fr"},
    "Alemán": {"ocr": "deu", "code": "de"},
    "Italiano": {"ocr": "ita", "code": "it"},
    "Portugués": {"ocr": "por", "code": "pt"},
}

ACENTOS_TLD = {
    "Estándar": "com",
    "Reino Unido 🇬🇧": "co.uk",
    "Estados Unidos 🇺🇸": "com",
    "Australia 🇦🇺": "com.au",
    "India 🇮🇳": "co.in",
    "Irlanda 🇮🇪": "ie",
    "Sudáfrica 🇿🇦": "co.za",
}

# --- CONFIGURACIÓN EN LA BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ 1. Ajustes de Imagen")
    filtro = st.radio("Filtro de Contraste (Cámara)", ("No", "Sí"))

    st.header("🌐 2. Idioma y Traducción")
    in_lang_name = st.selectbox(
        "Idioma del texto en la foto:", list(IDIOMAS.keys()), index=0
    )
    out_lang_name = st.selectbox(
        "Idioma al que traducir la voz:", list(IDIOMAS.keys()), index=0
    )

    st.header("🎭 3. Efecto de Voz Divertido")
    accent_name = st.selectbox(
        "Acento Regional (TLD):", list(ACENTOS_TLD.keys())
    )
    voz_lenta = st.checkbox("🐢 Modo Voz Robot (Lectura Lenta)", value=False)
    display_output_text = st.checkbox("Mostrar texto traducido", value=True)

# --- CAPTURA O CARGA DE IMAGEN ---
st.subheader("📸 Captura o Sube tu Imagen")
cam_option = st.checkbox("Usar Cámara")

img_cv = None

if cam_option:
    img_file_buffer = st.camera_input("Toma una Foto")
    if img_file_buffer is not None:
        bytes_data = img_file_buffer.getvalue()
        img_cv = cv2.imdecode(
            np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR
        )
        if filtro == "Sí":
            img_cv = cv2.bitwise_not(img_cv)
else:
    bg_image = st.file_uploader(
        "Cargar Imagen desde archivo:", type=["png", "jpg", "jpeg"]
    )
    if bg_image is not None:
        file_bytes = np.asarray(bytearray(bg_image.read()), dtype=np.uint8)
        img_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        st.image(
            img_cv,
            channels="BGR",
            caption="Imagen cargada",
            use_container_width=True,
        )

# --- PROCESAMIENTO DE OCR Y VOZ ---
if img_cv is not None:
    ocr_code = IDIOMAS[in_lang_name]["ocr"]
    src_code = IDIOMAS[in_lang_name]["code"]
    dest_code = IDIOMAS[out_lang_name]["code"]
    tld_code = ACENTOS_TLD[accent_name]

    # Convertir BGR a RGB para PyTesseract
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)

    with st.spinner("Leyendo texto de la imagen..."):
        try:
            extracted_text = pytesseract.image_to_string(img_rgb, lang=ocr_code)
        except Exception:
            extracted_text = pytesseract.image_to_string(img_rgb)

    text_clean = extracted_text.strip()

    st.divider()
    st.subheader("📝 Texto Detectado:")

    if text_clean:
        st.info(text_clean)

        if st.button("🚀 Generar Voz Divertida", type="primary"):
            with st.spinner("Traduciendo y modulando la voz..."):
                try:
                    # Traducción si los idiomas difieren
                    if src_code != dest_code:
                        translated_text = GoogleTranslator(
                            source=src_code, target=dest_code
                        ).translate(text_clean)
                    else:
                        translated_text = text_clean

                    if display_output_text and src_code != dest_code:
                        st.markdown(
                            f"**Traducción ({out_lang_name}):** {translated_text}"
                        )

                    # Generación de audio con gTTS
                    tts = gTTS(
                        text=translated_text,
                        lang=dest_code,
                        tld=tld_code,
                        slow=voz_lenta,
                    )

                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)

                    st.subheader("🔊 Audio Generado:")
                    st.audio(fp, format="audio/mp3")

                except Exception as e:
                    st.error(f"Error al procesar la voz: {e}")
    else:
        st.warning(
            "No se logró detectar texto legible en la imagen. Intenta enfocar mejor la foto."
        )
 
    
    
