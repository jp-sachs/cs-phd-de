## Analysis of computer Science PhD regulations at German universities

### Structure of the repository
- All data (processed or not) in `data` folder
- All scripts processing data and analyzing it in `processing` folder
- All analyses with visualizations / tables / reports in `analysis` folder
- Further files and folders:
    - `devcontainer` for reproduction of dev environment (local Docker installation required)
    - `Dockerfile` required for the devcontainer
    - `README.md`: This README file

### TODOs
- Write data extraction scripts:
    - Retrieve PDFs: Save them to `data/pdf`, one file per university (use GitLFS for storage); code in `processing/preprocessing/save_pdfs.py`
    - Extract text from PDFs: Store it in `data/text`, one file per university; code in `processing/preprocessing/extract_from_pdf.py`
- Further analysis ...