

python3 -m venv venv

saving the package requirements
pip3 freeze > requirements.txt

pip3 install -r requirements.txt



sudo apt-get install qttools5-dev-tools
pip3 install pyqt5-tools
/usr/lib/x86_64-linux-gnu/qt5/bin/designer&

pyuic5 -x im_client.ui -o im_ui.py



pip3 install PyQt5==5.14


Create server certificate:

openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout server.key -out server.crt

Make sure to enter ‘example.com’ for the Common Name.

Next, generate a client certificate:

openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout client.key -out client.crt

