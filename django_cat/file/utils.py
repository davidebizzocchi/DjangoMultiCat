from pathlib import Path
from typing import BinaryIO, TextIO, Union, List
import mimetypes
from PIL import Image
import pytesseract
import re
from pdf2image import convert_from_path
from icecream import ic
import json

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
    Converts a file into one or more PIL images.
    Supports PDF and common images.

    Args:
        file_path: Path to the file
    
    Returns:
        Single image or list of images
    
    Raises:
        ValueError: If file cannot be converted to image
    """
    suffix = file_path.suffix.lower()

    ic("get_image_from_file", file_path, suffix)

    try:
        if (suffix == '.pdf'):
            return convert_from_path(file_path)
        elif suffix in {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}:
            return Image.open(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    except Exception as e:
        raise ValueError(f"Error converting file: {str(e)}")

def process_image_ocr(img: Image.Image, is_double_page: bool = False) -> List[str]:
    """
    Processes an image with OCR and returns a list of extracted texts

    Args:
        img (Image.Image): Image to process
        is_double_page (bool): If True, splits the image into two pages
    
    Returns:
        List[str]: List of extracted texts (one per page)
    """
    def clean_text(text: str) -> str:
        """Cleans the OCR text"""
        return re.sub(r'\s+', ' ', text).strip()

    if is_double_page:
        width = img.size[0]
        left_text = clean_text(pytesseract.image_to_string(img.crop((0, 0, width//2, img.size[1]))))
        right_text = clean_text(pytesseract.image_to_string(img.crop((width//2, 0, width, img.size[1]))))
        return [left_text, right_text]
    else:
        return [clean_text(pytesseract.image_to_string(img))]

def save_processed_text(text: str, original_path: Path) -> Path:
    """
    Saves the processed text as a txt file in the same directory as the original file
    """
    output_path = original_path.with_suffix('.txt')

    # If the file already exists, add a counter
    counter = 1
    while output_path.exists():
        output_path = original_path.with_name(f"{original_path.stem}_{counter}.txt")
        counter += 1
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    return output_path

def next_file_path(file_path: Path) -> Path:
    """
    Generates a unique path for a file in a directory.
    If the file already exists, adds a counter.

    Args:
        file_path: Path to the original file
    
    Returns:
        Path: new file path
    """

    counter = 1
    output_path = Path(file_path)
    while output_path.exists():
        output_path = file_path.with_name(f"{file_path.stem}_{counter}")
        counter += 1

    return output_path

def update_processed_text(text: str, original_path: Path) -> None:
    """
    Updates the processed text file with the new text.
    If the file does not exist, creates it.

    Args:
        text: Text to write
        original_path: Path to the original file
    
    Returns:
        None
    """

    with open(original_path, 'w', encoding='utf-8') as f:
        f.write(text + "\n")

def extract_and_validate_json(text: str, retries=3) -> dict:
    """
    Extracts and validates JSON from text, handling multiple attempts if necessary.

    Args:
        text: Text containing JSON
        retries: Number of parsing attempts
    
    Returns:
        dict: Validated JSON
    """
    # Try to find JSON between braces
    json_pattern = r'\{[^{}]*\}'
    matches = re.finditer(json_pattern, text)

    for match in matches:
        try:
            json_str = match.group()
            data = json.loads(json_str)
            if "new_text" in data:
                return data
        except json.JSONDecodeError:
            continue
        
    # If no valid JSON is found, return dictionary with all text
    return {"new_text": text}
