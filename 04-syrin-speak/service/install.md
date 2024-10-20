sudo pip install numpy
sudo pip install pika
sudo pip install minio
sudo pip install sounddevice

sudo cp ./service/syrin-speak.py /usr/local/bin/syrin-speak.py
sudo chmod +x /usr/local/bin/syrin-speak.py

sudo cp ./service/syrin-speak.service /etc/systemd/system/syrin-speak.service

sudo usermod -aG audio $USER
sudo systemctl daemon-reload
sudo systemctl enable syrin-speak.service
sudo systemctl start syrin-speak.service
sudo systemctl status syrin-speak.service
journalctl -u syrin-speak.service -f

Or
cd /myenv
touch syrin-speak.py
copy content syrin-speak.py and paste in syrin-speak.py
vim syrin-speak.py
sudo apt install portaudio19-dev python3-pyaudio
sudo source myenv/bin/activate
systemctl --user start syrin-speak.service
systemctl --user status syrin-speak.service
journalctl --user-unit syrin-speak.service -f