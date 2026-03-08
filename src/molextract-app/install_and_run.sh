git clone git@github.com:Aditya1001001/phrasematcher-annotate-companies-app.git
cd phrasematcher-*/app/
uv venv -p 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install pip
python -m spacy download en_core_web_sm
# python -m spacy download en_core_web_md
# python -m spacy download en_core_web_lg
streamlit run app.py

