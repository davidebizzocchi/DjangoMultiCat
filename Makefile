
.PHONY: help activate requirements

help:	## Print this help 
	@echo "\nCommand to simplify the use of docker in LOCAL and PROD env\n"
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

activate:	## Acvtivate venv
	@echo "source .venv/bin/activate"

requirements:	## Create requirements.txt from requirements.in
	# @git pull

	@rm -f requirements/base.txt
	@rm -f requirements/locale.txt
	
	uv pip compile requirements/base.in -o requirements/base.txt
	uv pip compile requirements/locale.in -o requirements/locale.txt

	source .venv/bin/activate && uv pip install -r requirements/locale.txt

	git add requirements/*.txt
	@git commit -m "automatic upgrade requirements"
	@git push

	docker rmi -f django_cat-app:local

requirements-load-cat:
	source .venv/bin/activate && cp -r .cat-package/cat .venv/lib/python3.13/site-packages

up-local:           ## Run the LOCAL stack via Docker on http://0.0.0.0:8000/
	@{ \
		if ! docker info > /dev/null 2>&1; then \
			echo "Docker non è in esecuzione. Avvio Docker Desktop..."; \
			open -n /Applications/Docker.app; \
			echo "Attendo che Docker sia pronto..."; \
			while ! docker info > /dev/null 2>&1; do \
				sleep 1; \
			done; \
		fi; \
		(docker compose -p django_cat -f docker-compose.local.yml up || exit 1) & \
		PID=$$!; \
		trap 'docker compose -p django_cat -f docker-compose.local.yml down && exit 0' EXIT; \
		wait $$PID; \
	}

shell-sh:			## Open a sh shell in LOCAL inside app
	@docker compose -f docker-compose.local.yml exec app /bin/sh

django-log:
	@docker logs -f django_cat-app-1