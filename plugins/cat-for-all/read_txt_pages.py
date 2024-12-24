from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import OrderedDict
import signal
import sys
import time

# Dizionario thread-safe per i risultati parziali
partial_results = OrderedDict()
results_lock = threading.Lock()
start_time = time.time()

llm = ChatGroq(
    api_key="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",
    streaming=False,
    max_tokens=6000,
    temperature=0.7,
    model="llama-3.1-8b-instant",
    top_p=1.0,
)

# Definizione del prompt
prompt = PromptTemplate.from_template(
    "Questa è una pagina di un libro estratta da un PDF. Riscrivila in modo più chiaro e conciso, rimuovi spazi e invio inutili, correggi gli errori che ci possono essere. rendila leggibile, simile ad una normale pagina di un libro. Non aggiungere commenti, scrivi solo la pgina!\n\nPagina: {page}"
)

# Creazione della sequenza runnable più strutturata
chain = (
    {"page": RunnablePassthrough()} 
    | prompt 
    | llm 
    | (lambda x: x.content)
)

def refactory_page(page: str):
    result = chain.invoke(page)
    time.sleep(10)  # Aggiunge 5 secondi di pausa dopo ogni chiamata LLM
    return result

def clean_page(page: str, min_length=50):
    page = page.strip()

    if len(page) < min_length:
        return None
    
    return refactory_page(page)

def file_content(filename):
    with open(filename, 'r') as f:
        return f.read()

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
        with open("refactory_partial.txt", "w") as f:
            f.write(header + ordered_text)
    print(f"Risultati parziali salvati in 'refactory_partial.txt' - Tempo: {elapsed_time:.2f}s")

def process_page(page_data):
    page_number, page = page_data
    start = time.time()
    
    try:
        if not page.strip() or len(page.strip()) < 50:
            return None
            
        result = refactory_page(page.strip())
        
        if result:
            # Salva il risultato parziale nel dizionario
            with results_lock:
                partial_results[page_number] = result + "\n" * 3 + "-" * 100 + "\n" * 3
            
            print(f"Pagina {page_number} processata, time: {time.time() - start:.2f}s")
            return result
        
    except Exception as e:
        print(f"Errore nel processare la pagina {page_number}: {str(e)}")
    return None

def read_pages(content: str, min_length=50):
    separator = "\n" * 3 + "-" * 100 + "\n" * 3
    
    if content.startswith(separator):
        content = content[len(separator):]
    
    pages = content.split(separator)
    pages_with_numbers = list(enumerate(pages))
    
    # Usa ThreadPoolExecutor per processare le pagine in parallelo
    cleaned_pages = ""
    with ThreadPoolExecutor(max_workers=1) as executor:
        results = list(executor.map(process_page, pages_with_numbers))
        
    # Filtra i None e unisci i risultati
    cleaned_pages = separator.join([r for r in results if r])
    return cleaned_pages

# Registra il gestore dei segnali
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    filename = "result.txt"
    start_time = time.time()  # Reset start time
    
    try:
        content = file_content(filename)
        processed_content = read_pages(content)
        
        elapsed_time = time.time() - start_time
        header = f"Tempo totale di elaborazione: {elapsed_time:.2f} secondi\n"
        header += f"Pagine totali elaborate: {len(partial_results)}\n"
        header += "-" * 100 + "\n\n"
        
        with open("refactory.txt", "w") as f:
            f.write(header + processed_content)
            
        print(f"\nElaborazione completata in {elapsed_time:.2f} secondi")
        print(f"Processate {len(partial_results)} pagine")
        
    except FileNotFoundError:
        print(f"File {filename} non trovato")
    except Exception as e:
        print(f"Errore durante la lettura: {str(e)}")
    finally:
        save_partial_results(time.time() - start_time)

