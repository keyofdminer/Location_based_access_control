#!/bin/sh

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Create service..."
sudo echo "[Unit]"                                              >> /etc/systemd/system/monitor_service.service
sudo echo "Description=Client that broadcasts network signal strength to server."
                                                                >> /etc/systemd/system/monitor_service.service
sudo echo "After=network.target"                                >> /etc/systemd/system/monitor_service.service

sudo echo "[Service]"                                           >> /etc/systemd/system/monitor_service.service
sudo echo "ExecStart=/bin/python3 -u monitor_service.py"    >> /etc/systemd/system/monitor_service.service
sudo echo "ExecStop=/bin/systemctl kill monitor_service"        >> /etc/systemd/system/monitor_service.service
sudo echo "WorkingDirectory=$PROJECT_ROOT"                      >> /etc/systemd/system/monitor_service.service
sudo echo "StandardOutput=inherit"                              >> /etc/systemd/system/monitor_service.service
sudo echo "StandardError=inherit"                               >> /etc/systemd/system/monitor_service.service
sudo echo "Restart=always"                                      >> /etc/systemd/system/monitor_service.service
sudo echo "RestartSec=10"                                     >> /etc/systemd/system/monitor_service.service
sudo echo "User=root"                                           >> /etc/systemd/system/monitor_service.service

sudo echo "[Install]"                                           >> /etc/systemd/system/monitor_service.service
sudo echo "WantedBy=multi-user.target"                          >> /etc/systemd/system/monitor_service.service

echo "Launch services..."
sudo systemctl daemon-reload
sudo systemctl start monitor_service.service
sudo systemctl enable monitor_service.service
