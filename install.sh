#add nice alias for sourcing
echo 'alias src="source env/bin/activate"' > ~/.profile 
source ~/.profile 

#install venv and requirements
sudo apt install python3.8 python3.8-venv
python3.8 -m venv env
source env/bin/activate
pip3.8 install -r requirements.txt

#help text
echo "just run 'src' whenever you enter the directory now!"
