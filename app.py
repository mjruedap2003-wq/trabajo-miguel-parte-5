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
    "Extrae texto de cualquier foto, tradúcelo y escúchalo con velocidades y"
    " acentos chistosos."
)

st.divider()

# Mapeos de idiomas y acentos
IDIOMAS = {
    "Español": {"ocr": "spa", "code": "es"},
    "Inglés": {"ocr": "eng", "code": "en"},
    "Francés": {"ocr": "fra", "code": "fr"},
    "Alemán": {"ocr": "deu", "code": "de"},
    "Italiano": {"ocr": "ita", "code": "it"},
    "Portugués": {"ocr": "por", "code": "pt"},
    "Japonés": {"ocr": "jpn", "code": "ja"},
    "Coreano": {"ocr": "kor", "code": "ko"},
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

    st.header("🎭 3. Modos de Velocidad")

    # Selección de velocidad (Tortuga vs Conejo)
    modo_velocidad = st.radio(
        "Velocidad de Lectura:",
        ("🐢 Modo Tortuga (Lento / Robot)", "🐇 Modo Conejo (Rápido)"),
        index=1,
    )

    accent_name = st.selectbox(
        "Acento Regional (TLD):", list(ACENTOS_TLD.keys())
    )
    display_output_text = st.checkbox("Mostrar texto traducido", value=True)

    st.divider()
    st.subheader("🐢 Mascota Guardiana")
    # Imagen de la tortuga
    try:
        tortuga_img = Image.open("tortuga.jpg")
        st.image(
            tortuga_img,
            caption="¡Mascota Lectora!",
            use_container_width=True,
        )
    except FileNotFoundError:
        st.image(
            "https://images.unsplash.com/photo-1437622368342-7a3d73a34c8f?q=80&w=400&auto=format&fit=crop",
            caption="📷 Coloca 'tortuga.jpg' en tu carpeta",
            use_container_width=True,
        )

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

        if st.button("🚀 Traducir y Generar Voz Divertida", type="primary"):
            with st.spinner("Traduciendo y modulando la voz..."):
                translated_text = text_clean

                # Proceso de traducción con protección anti-fallos
                if src_code != dest_code:
                    try:
                        translated_text = GoogleTranslator(
                            source=src_code, target=dest_code
                        ).translate(text_clean)
                    except Exception as e:
                        st.warning(
                            "No se pudo traducir el texto automáticamente."
                            " Se usará el texto original extraído."
                        )
                        translated_text = text_clean

                if display_output_text and src_code != dest_code:
                    st.markdown(
                        f"**Traducción ({out_lang_name}):** {translated_text}"
                    )

                # Definir velocidad según el modo seleccionado
                is_slow = "Tortuga" in modo_velocidad

                try:
                    # Generación de audio mediante gTTS
                    tts = gTTS(
                        text=translated_text,
                        lang=dest_code,
                        tld=tld_code,
                        slow=is_slow,
                    )

                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)

                    st.subheader(
                        "🔊 Audio Generado ("
                        + ("🐢 Modo Lento" if is_slow else "🐇 Modo Rápido")
                        + "):"
                    )
                    st.audio(fp, format="audio/mp3")

                except Exception as e:
                    st.error(f"Error al generar el audio: {e}")
    else:
        st.warning(
            "No se logró detectar texto legible en la imagen. Intenta enfocar mejor la foto o cambiar el filtro."
        )
    
    
