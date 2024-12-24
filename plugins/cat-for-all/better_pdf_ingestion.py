import pytesseract
from pdf2image import convert_from_path
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import OrderedDict
import signal
import sys

# Dizionario thread-safe per i risultati parziali
partial_results = OrderedDict()
results_lock = threading.Lock()
start_time = time.time()

def signal_handler(signum, frame):
    elapsed_time = time.time() - start_time
    print(f"\nInterruzione rilevata dopo {elapsed_time:.2f} secondi.")
    print("Salvataggio risultati parziali...")
    save_partial_results(elapsed_time)
    sys.exit(0)

def save_partial_results(elapsed_time=None):
    with results_lock:
        if elapsed_time is None:
            elapsed_time = time.time() - start_time
            
        header = f"Tempo di elaborazione: {elapsed_time:.2f} secondi\n"
        header += f"Pagine elaborate: {len(partial_results)}\n"
        header += "-" * 100 + "\n\n"
        
        ordered_text = "".join([partial_results[k] for k in sorted(partial_results.keys())])
        with open("result_partial.txt", "w") as f:
            f.write(header + ordered_text)
    print(f"Risultati parziali salvati in 'result_partial.txt' - Tempo: {elapsed_time:.2f}s")

def split_image_vertically(image):
    width, height = image.size
    mid_point = width // 2
    left_half = image.crop((0, 0, mid_point, height))
    right_half = image.crop((mid_point, 0, width, height))
    return left_half, right_half

def process_page(page_data):
    page_number, page = page_data
    start = time.time()
    result = ""
    
    try:
        left_half, right_half = split_image_vertically(page)
        
        # Process left half
        result += pytesseract.image_to_string(left_half)
        result += "\n"*3 + "-" * 100 + "\n" * 3
        
        # Process right half
        result += pytesseract.image_to_string(right_half)
        result += "\n"*3 + "-" * 100 + "\n" * 3
        
        # Salva il risultato parziale nel dizionario
        with results_lock:
            partial_results[page_number] = result
            
        print(f"Pagina {page_number} processata, time: {time.time() - start}")
        return result
    except Exception as e:
        print(f"Errore nel processare la pagina {page_number}: {str(e)}")
        return ""

# Registra il gestore dei segnali
signal.signal(signal.SIGINT, signal_handler)

pages = convert_from_path("scanned.pdf", 300)
print(f"Numero di pagine: {len(pages)}")
all_text = ""

print("start")
start_time = time.time()  # Reset start time just before processing
try:
    # Crea una lista di tuple (numero_pagina, pagina)
    pages_with_numbers = list(enumerate(pages))
    
    # Usa ThreadPoolExecutor per processare le pagine in parallelo
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process_page, pages_with_numbers))
        
    # Combina tutti i risultati
    all_text = "".join(results)

finally:
    elapsed_time = time.time() - start_time
    print(f"\nTempo totale di elaborazione: {elapsed_time:.2f} secondi")
    if all_text:
        header = f"Tempo totale di elaborazione: {elapsed_time:.2f} secondi\n"
        header += f"Pagine totali elaborate: {len(pages)}\n"
        header += "-" * 100 + "\n\n"
        with open("result.txt", "w") as f:
            f.write(header + all_text)
    save_partial_results(elapsed_time)

