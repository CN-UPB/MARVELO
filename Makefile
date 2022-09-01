PWD = $(shell pwd)

AP = ansible-playbook

INV = ansible/inventories/production
PB = ansible/sites.yml

COPY_ID_FLAGS = -Kbi $(INV) $(PB)
NO_COPY_ID_FLAGS = -kKbi $(INV) $(PB)

.PHONY: servers
servers:
	$(AP) $(COPY_ID_FLAGS)

.PHONY: start
start:
	$(AP) $(COPY_ID_FLAGS) --tags "start_service"

.PHONY: stop
stop:
	$(AP) $(COPY_ID_FLAGS) --tags "stop_service"

.PHONY: renew
renew:
	$(AP) $(COPY_ID_FLAGS) --tags "renew_service"

.PHONY: restart
restart:
	$(AP) $(COPY_ID_FLAGS) --tags "restart_service"


.PHONY: servers_pw
servers_pw:
	$(AP) $(NO_COPY_ID_FLAGS)

push:
	git push https://git.cs.uni-paderborn.de/horbach/marvelo-demo.git
