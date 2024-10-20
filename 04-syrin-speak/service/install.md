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

OR

sudo apt install portaudio19-dev python3-pyaudio

sudo source myenv/bin/activate
cd /myenv
sudo cp syrin-speak.py /root/myenv/syrin-speak.py

mkdir -p ~/.config/systemd/user/
cp ./service/syrin-speak.service ~/.config/systemd/user/syrin-speak.service

systemctl --user daemon-reload
systemctl --user enable syrin-speak.service
systemctl --user start syrin-speak.service
systemctl --user status syrin-speak.service
journalctl --user-unit syrin-speak.service -f