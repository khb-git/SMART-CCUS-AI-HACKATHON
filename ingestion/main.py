import os
import json
import uuid
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


from dotenv import load_dotenv

load_dotenv()

# Environment variables
source_dir = os.getenv("PATH_TO_RAW_DATA_DIR")
ingestion_folder = os.getenv("PATH_TO_CHUNKED_DATA_DIR")

# Constant for EPA source
EPA_LINK = "https://www.epa.gov/uic/final-class-vi-guidance-documents"

def chunk_with_langchain(source_dir, output_root):
    # Initialize the splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100,
        add_start_index=True
    )

    if not os.path.exists(output_root):
        os.makedirs(output_root)

    # Validate source directory exists
    if not os.path.exists(source_dir):
        print(f"Source directory not found: {source_dir}")
        return

    for filename in os.listdir(source_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(source_dir, filename)
            
            try:
                # 1. Load and Split the specific PDF
                loader = PyPDFLoader(file_path)
                pages = loader.load()
                chunks = splitter.split_documents(pages)

                # 2. Setup the directory for this specific PDF
                file_folder_name = os.path.splitext(filename)[0]
                file_output_dir = os.path.join(output_root, file_folder_name)
                os.makedirs(file_output_dir, exist_ok=True)

                # Generate a unique ID for the document
                doc_uuid = str(uuid.uuid4())

                # 3. Create top-level attribute.json for the document
                sample_metadata = pages[0].metadata if pages else {}
                datasource_attr = {
                    "document_id": doc_uuid,
                    "datasource_name": filename,
                    "file_type": "PDF",
                    "online_link": EPA_LINK,
                    "author_name": sample_metadata.get("author", "Environmental Protection Agency")
                }
                with open(os.path.join(file_output_dir, "attribute.json"), "w") as f:
                    json.dump(datasource_attr, f, indent=4)

                # 4. Save each chunk into the 0/, 1/, 2/ structure
                for i, chunk in enumerate(chunks):
                    chunk_folder = os.path.join(file_output_dir, str(i))
                    os.makedirs(chunk_folder, exist_ok=True)

                    # Generate a unique ID for the specific chunk
                    chunk_uuid = str(uuid.uuid4())

                    # Save the text content
                    with open(os.path.join(chunk_folder, "content.txt"), "w", encoding="utf-8") as f:
                        f.write(chunk.page_content)

                    # Save chunk attributes
                    chunk_attr = {
                        "chunk_id": chunk_uuid,
                        "parent_document_id": doc_uuid,
                        "page": chunk.metadata.get("page", 0) + 1,
                        "chunk_index": i,
                        "datasource_name": filename
                    }
                    with open(os.path.join(chunk_folder, "attribute.json"), "w") as f:
                        json.dump(chunk_attr, f, indent=4)

                print(f"Successfully processed {len(chunks)} chunks for: {filename}")

            except Exception as e:
                print(f"Failed to process {filename}: {str(e)}")

if __name__ == "__main__":
    chunk_with_langchain(source_dir, ingestion_folder)

