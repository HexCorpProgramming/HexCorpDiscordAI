#install venv and requirements
sudo apt install python3.11 python3.11-venv
python3.11 -m venv env
source env/bin/activate
pip install -r requirements.txt

#help text
echo "just run 'env/bin/activate' whenever you enter the directory now!"
