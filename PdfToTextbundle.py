
import os
import fitz  # PyMuPDF
from PyPDF2 import PdfReader
import re

FILTER_WORDS = "COMP -424: Artificial intelligence"

def sanitize_title(title):
    # Remove any characters that are not alphanumeric, spaces, or hyphens
    sanitized = re.sub('[^a-zA-Z0-9 \-]', '', title)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    return sanitized

def sanitize_title1(title):
    # Remove any characters that are not alphanumeric, spaces, or hyphens
    sanitized = re.sub('[^a-zA-Z \-]', '', title)
    # Replace spaces with underscores
    return sanitized

def get_sanitized_filename_from_pdf(pdf_path):
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    sanitized_filename = filename.replace('-', ' ').replace('_', ' ')
    
    # Introduce spaces between capitalized words
    sanitized_filename = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', sanitized_filename)
    
    return sanitized_filename

def pdf_to_textbundle(pdf_path):
    # Determine the output directory name
    output_dir_name = os.path.splitext(os.path.basename(pdf_path))[0] + ".textbundle"
    output_dir_path = os.path.join(os.path.dirname(pdf_path), output_dir_name)
    
    # Create directories for TextBundle and assets
    assets_dir = os.path.join(output_dir_path, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # Open the PDF file using PyPDF2 for text extraction
    pdf_file = open(pdf_path, "rb")
    pdf = PdfReader(pdf_file)
    
    # Extract title from the PDF for filename and format it as "L1 Title"
    pdf_title = get_sanitized_filename_from_pdf(pdf_path)
    markdown_filename = f"{pdf_title}.md"
    
    markdown_content = []
    
    # Open the PDF using PyMuPDF for image extraction
    pdf_doc = fitz.open(pdf_path)
    
    for page_num, page in enumerate(pdf.pages):
        page_text = page.extract_text().replace(FILTER_WORDS, "")
        
        # Convert bullet points and numbered lists to markdown format
        lines = page_text.split("\n")
        page_title = lines[0] if lines else "Page"  # Use the refined first line as the title if available
        sanitized_page_title = sanitize_title(page_title)
        
        # Remove the title line from the main content
        lines = lines[1:]
        
        for idx, line in enumerate(lines):
            if line.strip().startswith("•"):
                lines[idx] = "- " + line.strip()[1:].strip()  # Convert bullet points to markdown format
            elif line.strip().endswith("."):
                try:
                    int(line.strip().split(".")[0])  # Check if starts with a number
                    lines[idx] = line.strip()  # Numbered list is already in markdown format
                except:
                    pass
        page_text = "\n".join(lines)
        
        # Add page text to markdown content using the page title
        markdown_content.append(f"### {sanitize_title1(page_title)}\n")
        markdown_content.append(page_text)
        
        # Extract images directly from the PDF using PyMuPDF
        images = pdf_doc.load_page(page_num).get_images(full=True)
        for img_index, image in enumerate(images):
            xref = image[0]
            base_image = pdf_doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Use PIL to get image dimensions
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes))
            if img.width < 100 or img.height < 100:
                continue
            
            image_name = f"{sanitized_page_title}_image_{img_index + 1}.png"
            image_path = os.path.join(assets_dir, image_name)
            img.save(image_path)
            
            # Add image reference to the markdown content
            markdown_content.append(f"![{page_title} Image {img_index + 1}](assets/{image_name})\n\n")
    
    # Close the PDF file after processing
    pdf_file.close()
    
    # Save markdown content
    with open(os.path.join(output_dir_path, markdown_filename), "w") as f:
        f.write("\n".join(markdown_content))
    
    print(f"TextBundle created at {output_dir_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python pdf_to_textbundle_no_page_numbers.py [path_to_pdf]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    pdf_to_textbundle(pdf_path)
