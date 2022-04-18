# Location_based_access_control
'''
Server
	Install Raspbian
	Update and Upgrade OS
	Install RaspAP
			curl -sL https://install.raspap.com | bash
			reboot
		Login Wifi (SSID:raspi-webgui Password:ChangeMe)
		Update router settings in portal (10.3.141.1) (User:admin Password:secret)
			Hotspot - Basic
				Interface = wlan0
				SSID = 526Testing
				Channel 6
			Hotspot - Security
				PSK = 526testing
			Hotspot - Advanced
				Hide SSID
				Country Code = US
			DHCP Server - Server settings
				Static IP & Gateway = 192.168.0.1
				Starting IP = 192.168.0.10
				Ending IP = 192.168.0.254
				DNS Server 1 = 9.9.9.9
				DNS Server 2 = 1.1.1.1
	Reboot Pi and double check router settings
	Plug in LAN

	Install python packages in requirements.txt

	Install openNDS
			sudo apt install git libmicrohttpd-dev
			wget https://codeload.github.com/opennds/opennds/tar.gz/v7.0.1
			tar -xf v9.1.0
			cd openNDS-9.1.0
			make
			sudo make install
			sudo systemctl enable opennds
		Edit /etc/opennds/opennds.conf
			Set GatewayInterface to wlan0
			Uncomment preauthenticated-users firewall rules
				udp 53
				tcp 53
			Uncomment fasport and set to 5000
			Uncomment fas_secure_enabled and set to 0
	Copy python code to Pi
	Install as service (I made it opennds dependent on it)

Clients
	Install kali for raspberry pi using etcher
		sudo apt-get update
		sudo apt-get upgrade
		sudo apt-get install python3-pip
		copy scripts to raspberry pi
		run monitor_service_setup.sh


Process
	Startup
		For all currently pinging devices
			Loop through them
				Send monitor_once
				wait for response and set in dictionary
		For all currently pinging devices
			for each pair of macs
				average m1:m2 and m2:m1 signal strengh
				add to array of lengths
		Plot triangle to web page

	Running
		look up MAC address of web client
		triangulate location of client and plot on webpage
		check if in bounding box
			enable button to join network




Resources
	https://www.craft.do/s/accPuxNGhsRqdy (monitor mode on api)
	https://www.maketecheasier.com/turn-raspberry-pi-captive-portal-wi%E2%80%90fi-access-point/ (tutorial)
	https://opennds.readthedocs.io/en/stable/compile.html (installing opennds)
	https://trevphil.com/posts/captive-portal (FAS captive portal setup) 
	
'''
