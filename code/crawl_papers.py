"""
Crawl Papers Utility

This script cleans local markdown copies of arXiv paper abstract pages structurally.
It converts the raw markdown content to an HTML DOM structure using markdown-it-py,
then uses BeautifulSoup (BS4) to extract only key paper information (Title, Authors, 
Abstract). 

By decomposing navigation bars, boilerplate elements, sidebars, search containers, 
and social links programmatically without relying on regex strings, it prepares a clean, 
minimum-context summary file for indexing or direct LLM reasoning.

Input:  sandbox/papers/*.md (abstract pages with arXiv wrapper boilerplate)
Output: sandbox/crawled_papers/*.md (clean Title and Abstract details only)
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup
import markdown_it

PAPERS_DIR = Path(__file__).parent / "sandbox" / "papers"
CRAWLED_DIR = Path(__file__).parent / "sandbox" / "crawled_papers"

def clean_paper(file_path: Path):
    print(f"Cleaning {file_path.name} structurally using BeautifulSoup...")
    content = file_path.read_text(encoding="utf-8")
    
    # 1. Parse markdown to HTML DOM
    md = markdown_it.MarkdownIt()
    html_content = md.render(content)
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 2. Locate core paper elements structurally
    title_el = None
    authors_el = None
    abstract_el = None
    
    # Find title and author elements based on text content structural indicators
    for h in soup.find_all(["h1", "h2", "h3"]):
        text = h.get_text().strip()
        if "title:" in text.lower():
            title_el = h
        elif "authors:" in text.lower():
            authors_el = h
            
    # Find Abstract paragraph block
    for p in soup.find_all(["p", "blockquote"]):
        text = p.get_text().strip()
        if text.lower().startswith("abstract:") or text.lower().startswith("> abstract:"):
            abstract_el = p
            break
            
    # Reassemble a clean document containing only core structural details
    output_lines = []
    if title_el:
        output_lines.append(f"# {title_el.get_text().strip()}")
    if authors_el:
        output_lines.append(f"\n{authors_el.get_text().strip()}\n")
    if abstract_el:
        abs_text = abstract_el.get_text().strip().replace("Abstract:", "").replace("> Abstract:", "").strip()
        output_lines.append(f"Abstract: {abs_text}")
        
    cleaned_content = "\n".join(output_lines)
    
    # If structural matching failed to extract, fall back to structural tags decomposing
    if not cleaned_content.strip():
        for element in soup.find_all(["nav", "header", "footer", "form", "input", "button"]):
            element.decompose()
        cleaned_content = soup.get_text().strip()

    CRAWLED_DIR.mkdir(parents=True, exist_ok=True)
    output_file = CRAWLED_DIR / file_path.name
    output_file.write_text(cleaned_content.strip(), encoding="utf-8")
    print(f"Saved clean structural content to {output_file}")

def main():
    if not PAPERS_DIR.exists():
        print(f"Source directory {PAPERS_DIR} does not exist!")
        return

    # Clean destination folder first
    if CRAWLED_DIR.exists():
        print(f"Cleaning existing files in {CRAWLED_DIR}...")
        for f in CRAWLED_DIR.glob("*"):
            if f.is_file():
                f.unlink()

    md_files = list(PAPERS_DIR.glob("*.md"))
    for file_path in md_files:
        clean_paper(file_path)

if __name__ == "__main__":
    main()
