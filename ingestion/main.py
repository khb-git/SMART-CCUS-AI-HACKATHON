import os
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


from dotenv import load_dotenv

load_dotenv()

source_dir = os.getenv("PATH_TORAW_DATA_DIR")
ingestion_folder = os.getenv("PATH_TO_CHUNKED_DATA_DIR")


def chunk_with_langchain(source_dir, output_root):
    # Initialize the splitter
    # chunk_size is characters; chunk_overlap keeps context between folders
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100,
        add_start_index=True
    )

    if not os.path.exists(output_root):
        os.makedirs(output_root)

    for filename in os.listdir(source_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(source_dir, filename)
            
            # 1. Load and Split the specific PDF
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            chunks = splitter.split_documents(pages)

            # 2. Setup the directory for this specific PDF
            file_folder_name = os.path.splitext(filename)[0]
            file_output_dir = os.path.join(output_root, file_folder_name)
            os.makedirs(file_output_dir, exist_ok=True)

            # 3. Create top-level attribute.json
            # LangChain loaders often extract metadata like author automatically
            sample_metadata = pages[0].metadata if pages else {}
            datasource_attr = {
                "datasource_name": filename,
                "file_type": "PDF",
                "online_link": sample_metadata.get("source", "N/A"),
                "author_name": sample_metadata.get("author", "Unknown")
            }
            with open(os.path.join(file_output_dir, "attribute.json"), "w") as f:
                json.dump(datasource_attr, f, indent=4)

            # 4. Save each chunk into the 0/, 1/, 2/ structure
            for i, chunk in enumerate(chunks):
                chunk_folder = os.path.join(file_output_dir, str(i))
                os.makedirs(chunk_folder, exist_ok=True)

                # Save the text content
                with open(os.path.join(chunk_folder, "content.txt"), "w", encoding="utf-8") as f:
                    f.write(chunk.page_content)

                # Save chunk attributes (includes original page number)
                chunk_attr = {
                    "page": chunk.metadata.get("page", 0) + 1,
                    "chunk_index": i,
                    "datasource_name": filename
                }
                with open(os.path.join(chunk_folder, "attribute.json"), "w") as f:
                    json.dump(chunk_attr, f, indent=4)

            print(f"Processed {len(chunks)} chunks for: {filename}")



chunk_with_langchain(source_dir, ingestion_folder)

