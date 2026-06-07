SMART CCUS AI Hackathon
Repository for the Penn State NittCarbAI SEG Hackathon team.
This project is a prototype Class VI permit review assistant for CCUS workflows. It scrapes and ingests EPA Class VI reference documents and permit application materials, indexes them into a local vector database, and exposes a chatbot-style review assistant through a CLI, FastAPI backend, and Streamlit demo UI.
---
Current System Overview
The current pipeline is:
```text
scrape/download
→ manifest with local paths
→ PDF/DOCX/XLSX ingestion
→ text/table extraction
→ section-aware chunking
→ schema metadata tagging
→ Chroma vector indexing
→ auto-route reference vs permits
→ query intent routing
→ query expansion
→ diversified retrieval
→ local reranking
→ evidence packaging
→ evidence-grounded answer synthesis
→ FastAPI /ask endpoint
→ Streamlit chatbot UI
```
The system supports questions such as:
```text
How do applicants monitor injection pressure and flow rate?
What does Class VI require for testing and monitoring?
Compare applicant injection pressure monitoring against EPA expectations.
How do applicants handle groundwater monitoring?
What evidence supports continuous monitoring requirements?
```
---
Repository Structure
```text
api/
  main.py                     FastAPI backend with /health and /ask

ingestion/
  main.py                     PDF/DOCX/XLSX ingestion and chunking

rag/
  ask.py                      End-to-end CLI ask workflow
  evidence.py                 Evidence packaging
  index_chunks.py             Chroma indexing workflow
  query_chroma.py             Retrieval smoke-test CLI
  query_expansion.py          Class VI query expansion
  query_intent.py             Query intent routing
  reranker.py                 Lightweight local reranking
  retriever.py                Schema-aware retrieval
  review_answer.py            Structured review answer builder
  answer_synthesis.py         Evidence-grounded answer synthesis
  vectorstore.py              Chroma wrapper
  embeddings.py               Embedding wrapper
  types.py                    Shared dataclasses/types

scraper.py                    Scraper entry point
tests/                        Unit and integration tests
ui/
  app.py                      Streamlit chatbot UI
  api_client.py               Streamlit API client helpers
```
---
Setup
1. Create and activate a virtual environment
Windows PowerShell:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
2. Install dependencies
```powershell
pip install -r requirements.txt
```
3. Confirm tests pass
```powershell
python -m pytest tests/
```
---
Environment Variables
The ingestion script can use `.env` values, but CLI flags can also be used directly.
Example `.env`:
```env
PATH_TO_RAW_DATA_DIR=data/raw_docs
PATH_TO_CHUNKED_DATA_DIR=data/chunked
PATH_TO_MANIFEST=data/manifest.json
```
Local/generated data folders are intentionally not committed.
---
End-to-End Demo Workflow
The full workflow is:
```text
download documents
→ ingest/chunk documents
→ index chunks into Chroma
→ run API
→ run Streamlit UI
```
---
Step 1: Scrape and Download Documents
Run the scraper/downloader workflow used by the project.
Depending on the current scraper entry point, this may be:
```powershell
python scraper.py
```
The expected result is a manifest at:
```text
data/manifest.json
```
and downloaded files under:
```text
data/raw_docs/
```
The manifest should include a `local_path` field for each downloaded file so ingestion can reuse local files directly.
---
Step 2: Ingest Documents
Run ingestion from the manifest:
```powershell
python -m ingestion.main --manifest data/manifest.json --output data/chunked
```
Expected successful output:
```json
{
  "processed": 112,
  "skipped_missing_local_path": 0,
  "skipped_missing_file": 0,
  "skipped_unsupported_type": 0,
  "failed": 0
}
```
The ingestion step handles:
```text
PDF text
PDF tables
DOCX text
DOCX tables
XLSX tables
section-aware chunk context
schema-aware metadata
```
---
Step 3: Index Chunks into Chroma
Index the chunked data into the local Chroma vector database:
```powershell
python -m rag.index_chunks --chunked-dir data/chunked --collection auto --persist-directory chroma_data --batch-size 32
```
The `--collection auto` option routes chunks into:
```text
reference
permits
```
based on document metadata.
---
Step 4: Test Retrieval from the CLI
Run a direct retrieval smoke test:
```powershell
python -m rag.query_chroma --query "How do applicants monitor injection pressure and flow rate?" --collection permits --persist-directory chroma_data --k 5 --section-id 8 --diversified --fetch-k 30 --max-per-source 1
```
Useful comparison flags:
```powershell
--no-query-expansion
--no-reranking
```
Example:
```powershell
python -m rag.query_chroma --query "How do applicants monitor injection pressure and flow rate?" --collection permits --persist-directory chroma_data --k 5 --section-id 8 --diversified --fetch-k 30 --max-per-source 1 --no-query-expansion
```
Query expansion has produced strong retrieval improvements during testing. For the pressure/flow monitoring query, the top score improved from about `0.6751` without expansion to about `0.7851` with expansion.
---
Step 5: Run the Ask CLI
The ask CLI runs the full backend assistant workflow:
```powershell
python -m rag.ask --query "How do applicants monitor injection pressure and flow rate?" --persist-directory chroma_data --section-id 8
```
This performs:
```text
intent routing
query expansion
retrieval
reranking
evidence packaging
answer synthesis
formatted answer output
```
Useful flags:
```powershell
--intent auto
--intent regulatory_requirement
--intent permit_precedent
--intent cross_check
--intent general_review
--no-query-expansion
--no-reranking
```
Example cross-check:
```powershell
python -m rag.ask --query "Compare applicant injection pressure monitoring against EPA expectations." --persist-directory chroma_data --section-id 8 --intent cross_check
```
---
Step 6: Run the FastAPI Backend
Start the API server:
```powershell
python -m uvicorn api.main:app --reload
```
The API should be available at:
```text
http://127.0.0.1:8000
```
Swagger docs:
```text
http://127.0.0.1:8000/docs
```
Health check:
```text
GET /health
```
Ask endpoint:
```text
POST /ask
```
Example `/ask` request body:
```json
{
  "query": "How do applicants monitor injection pressure and flow rate?",
  "persist_directory": "chroma_data",
  "section_id": "8",
  "intent": "auto",
  "k_reference": 3,
  "k_permits": 5,
  "fetch_k": 30,
  "max_per_source": 1,
  "expand_retrieval_query": true,
  "use_reranking": true
}
```
---
Step 7: Run the Streamlit UI
Keep the FastAPI server running in one terminal.
Open a second terminal and run:
```powershell
python -m streamlit run ui/app.py
```
Streamlit should open at:
```text
http://localhost:8501
```
In the UI, use:
```text
FastAPI URL: http://127.0.0.1:8000
Chroma persist directory: chroma_data
Section ID: 8
Intent: auto
Reference evidence count: 3
Permit evidence count: 5
Raw candidates before diversification: 30
Max evidence items per source: 1
Use query expansion: checked
Use local reranking: checked
```
Example question:
```text
How do applicants monitor injection pressure and flow rate?
```
Expected UI sections:
```text
Answer
Reviewer interpretation
Potential follow-up
Evidence summary
Evidence items
Source document links
Similarity scores
Excerpts
```
---
Current Retrieval Features
Query Intent Routing
The system classifies questions into:
```text
regulatory_requirement
permit_precedent
cross_check
general_review
```
Examples:
```text
What does Class VI require for testing and monitoring?
→ reference collection

How do applicants monitor injection pressure and flow rate?
→ permits collection

Compare applicant injection pressure monitoring against EPA expectations.
→ reference + permits
```
Query Expansion
Natural-language questions are expanded with Class VI vocabulary.
Example:
```text
flow rate
→ injection rate, mass flow rate, mass flowmeter, Coriolis meter, orifice meter

pressure
→ wellhead pressure, annulus pressure, downhole pressure, pressure transducer

monitoring
→ continuous recording devices, SCADA, operational parameters
```
The original user question is still displayed. The expanded query is only used for retrieval.
Diversified Retrieval
Results are diversified by source document to avoid returning too many chunks from the same PDF.
Recommended demo setting:
```text
max_per_source = 1
```
Local Reranking
A lightweight local reranker compares retrieved candidates against the original user question using lexical overlap and Class VI technical term boosts.
Reranking may not always increase the displayed similarity score, because displayed scores remain Chroma similarity scores. Reranking is meant to improve result ordering and answer relevance.
Similarity Scores
Similarity scores are retrieval similarity values, not correctness probabilities.
Example:
```text
Similarity score: 0.7851
```
This means the chunk was highly similar to the retrieval query. It does not mean the answer is 78.51% correct.
---
Recommended Demo Questions
Permit precedent
```text
How do applicants monitor injection pressure and flow rate?
```
```text
How do applicants monitor groundwater during injection?
```
```text
How do applicants track plume and pressure front movement?
```
Regulatory/reference
```text
What does Class VI require for testing and monitoring?
```
```text
What does EPA guidance say about mechanical integrity testing?
```
Cross-check
```text
Compare applicant injection pressure monitoring against EPA expectations.
```
```text
Evaluate whether the applicant testing and monitoring plan is adequate.
```
```text
What gaps should a reviewer look for in a Testing and Monitoring Plan?
```
---
Development Workflow
Use feature branches:
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/<branch-name>
```
Run tests before committing:
```powershell
python -m pytest tests/
```
Commit and push:
```powershell
git status
git add <changed-files>
git commit -m "Short descriptive message"
git push origin feature/<branch-name>
```
Open a PR with:
```text
base: develop
compare: feature/<branch-name>
```
---
Common Troubleshooting
FastAPI is not running
If Streamlit shows a backend request error, make sure this command is running in another terminal:
```powershell
python -m uvicorn api.main:app --reload
```
Check:
```text
http://127.0.0.1:8000/docs
```
Streamlit cannot find the API
Confirm the UI sidebar has:
```text
FastAPI URL: http://127.0.0.1:8000
```
Chroma directory not found or no results
Make sure chunks were indexed:
```powershell
python -m rag.index_chunks --chunked-dir data/chunked --collection auto --persist-directory chroma_data --batch-size 32
```
Then use:
```text
persist_directory: chroma_data
```
Generated folders showing in Git
Do not commit local data/vector stores.
Common local folders:
```text
data/raw_docs/
data/chunked/
data/chunked_section_test/
chroma_data/
chroma_data_section_test/
.pytest_cache/
.venv/
```
Hugging Face warning on Windows
You may see:
```text
Warning: You are sending unauthenticated requests to the HF Hub.
```
or symlink/cache warnings. These are not blockers for local development. A Hugging Face token can improve download limits, but the system can run without one.
---
Current Status
The project currently has:
```text
working ingestion
working vector indexing
working retrieval
working ask CLI
working FastAPI backend
working Streamlit demo UI
passing tests
```
The next likely improvements are:
```text
1. Better table serialization
2. More review-mode presets
3. Cleaner answer prose
4. Optional LLM polish layer
5. Deployment configuration
6. Expanded regression query suite
```