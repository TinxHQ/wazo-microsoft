.PHONY: build-oauth2-sync test-setup test test-image test-prerequisite test-db

test-setup: test-prerequisite build-oauth2-sync test-image egg-info test-db

test-prerequisite:
	docker pull p0bailey/docker-flask
	docker pull rabbitmq
	docker pull swaggerapi/swagger-validator
	docker pull wazopbx/wait
	docker pull wazopbx/wazo-auth
	docker pull wazopbx/wazo-auth-db

build-oauth2-sync:
	docker build --no-cache -t oauth2-synchronization-service -f assets/external_auth/oauth2_synchronization_service/Dockerfile assets/external_auth/oauth2_synchronization_service

test-image:
	docker build --no-cache -t wazopbx/wazo-auth-microsoft-tests -f Dockerfile-auth-microsoft-test ..

egg-info:
	cd .. && python3 setup.py egg_info

test:
	pytest -x
