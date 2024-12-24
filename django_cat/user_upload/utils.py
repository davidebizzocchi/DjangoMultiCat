from pathlib import Path
from typing import BinaryIO, TextIO, Union, List
import mimetypes
from PIL import Image
import pytesseract
import re
from pdf2image import convert_from_path
from icecream import ic

def open_file_by_type(file_path: Path) -> Union[BinaryIO, TextIO, Image.Image]:
    """
    Opens a file with the appropriate mode based on its extension.
    Uses Pillow for images.
    
    Args:
        file_path (Path): Path object pointing to the file
        
    Returns:
        Union[BinaryIO, TextIO, Image.Image]: Opened file object or Image
        
    Raises:
        ValueError: If file type is not supported
    """
    # Get file extension
    file_type = file_path.suffix.lower()
    
    # Define image types handled by Pillow
    image_types = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    # Define other binary files
    binary_types = {'.pdf'}
    # Define text types
    text_types = {'.txt', '.csv', '.md', '.json'}
    
    try:
        if file_type in image_types:
            return Image.open(file_path)
        elif file_type in binary_types:
            return open(file_path, 'rb')
        elif file_type in text_types:
            return open(file_path, 'r', encoding='utf-8')
        else:
            # Try to guess the type using mimetypes
            mime_type = mimetypes.guess_type(str(file_path))[0]
            if mime_type and mime_type.startswith('image/'):
                return Image.open(file_path)
            elif mime_type and mime_type.startswith('text/'):
                return open(file_path, 'r', encoding='utf-8')
            elif mime_type:
                return open(file_path, 'rb')
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
    except Exception as e:
        raise ValueError(f"Error opening file: {str(e)}")

def get_image_from_file(file_path: Path) -> Union[Image.Image, List[Image.Image]]:
    """
    Converte un file in una o più immagini PIL.
    Supporta PDF e immagini comuni.
    
    Args:
        file_path: Percorso del file
        
    Returns:
        Una singola immagine o lista di immagini
        
    Raises:
        ValueError: Se il file non può essere convertito in immagine
    """
    suffix = file_path.suffix.lower()

    ic("get_image_from_file", file_path, suffix)
    
    try:
        if (suffix == '.pdf'):
            return convert_from_path(file_path)
        elif suffix in {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}:
            return Image.open(file_path)
        else:
            raise ValueError(f"Formato file non supportato: {suffix}")
    except Exception as e:
        raise ValueError(f"Errore nella conversione del file: {str(e)}")

def process_image_ocr(img: Image.Image, is_double_page: bool = False) -> str:
    """
    Processa un'immagine con OCR
    
    Args:
        img (Image.Image): Immagine da processare
        is_double_page (bool): Se True, processa l'immagine come doppia pagina
        
    Returns:
        str: Testo estratto dall'immagine
    """
    def clean_text(text: str) -> str:
        """Pulisce il testo OCR"""
        return re.sub(r'\s+', ' ', text).strip()
    
    if is_double_page:
        width = img.size[0]
        left_text = pytesseract.image_to_string(img.crop((0, 0, width//2, img.size[1])))
        right_text = pytesseract.image_to_string(img.crop((width//2, 0, width, img.size[1])))
        return f"{clean_text(left_text)}\n\n{'='*50}\n\n{clean_text(right_text)}"
    else:
        return clean_text(pytesseract.image_to_string(img))

def save_processed_text(text: str, original_path: Path) -> Path:
    """
    Salva il testo processato come file txt nella stessa directory del file originale
    """
    output_path = original_path.with_suffix('.txt')
    
    # Se il file esiste già, aggiungi un contatore
    counter = 1
    while output_path.exists():
        output_path = original_path.with_name(f"{original_path.stem}_{counter}.txt")
        counter += 1
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
        
    return output_path
