Setup Commands:

# Create venv
python3 -m venv env

source env/bin/activate

# Install dependencies
pip install -r requirments.txt

or 

pip install pillow hachoir mutagen pikepdf fastapi uvicorn python-multipart numpy matplotlib scipy steganography-tools sqlalchemy aiofiles


# to activate when starting after the installation 
// for windows
> .\env\Scripts\activate
// for linux
> source ./env/bin/activate



# dependencies 

requirments.txt


# for windows 

pip install httpie


# set up enviroment variabls
export PROXY_API_KEY="a-strong-random-key"
export MAX_FILE_BYTES=26214400   # 25MB
export ALLOWED_EXTENSIONS="jpg,jpeg,png,pdf,txt"
export SCRUB_TIMEOUT=20
export SCRUB_MEMORY_LIMIT_MB=300
export OUTBOX_DIR="./outbox"
export DB_PATH="./proxy_logs.db"



# to start 
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
