restart:
	ssh pi@192.168.0.27 sudo service fission restart
	ssh pi@192.168.0.28 sudo service fission restart
	ssh pi@192.168.0.29 sudo service fission restart
	ssh pi@192.168.0.30 sudo service fission restart

to_adhoc:
	sudo cp /etc/network/interfaces.adhoc /etc/network/interfaces
	ssh pi@192.168.0.27 sudo cp /etc/network/interfaces.adhoc /etc/network/interfaces	
	ssh pi@192.168.0.28 sudo cp /etc/network/interfaces.adhoc /etc/network/interfaces
	ssh pi@192.168.0.29 sudo cp /etc/network/interfaces.adhoc /etc/network/interfaces
	ssh pi@192.168.0.30 sudo cp /etc/network/interfaces.adhoc /etc/network/interfaces

to_inf:
	sudo cp /etc/network/interfaces.backup /etc/network/interfaces
	ssh pi@192.168.0.27 sudo cp /etc/network/interfaces.backup /etc/network/interfaces
	ssh pi@192.168.0.28 sudo cp /etc/network/interfaces.backup /etc/network/interfaces
	ssh pi@192.168.0.29 sudo cp /etc/network/interfaces.backup /etc/network/interfaces
	ssh pi@192.168.0.30 sudo cp /etc/network/interfaces.backup /etc/network/interfaces

push:
	git push https://git.cs.uni-paderborn.de/horbach/marvelo-demo.git

nmap:
	nmap -sP 192.168.0.31/24

