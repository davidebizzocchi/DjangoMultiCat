
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

destroy-django:
	docker rmi -f django_cat-app:local

destroy-cat:
	docker rmi -f django_cat-cheshire-cat-core:latest

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
	@docker exec -it django_cat-app-1 /bin/bash

shell-django:		## Open a django shell in LOCAL
	@docker exec -it django_cat-app-1 python manage.py shell 

django-log:
	@docker logs -f django_cat-app-1


remove-migrations:	## Remove migrations
	@echo "Cleaning migrations directory..."
	@find . -type d -name "migrations" -exec sh -c 'cd "{}" && find . -type f ! -name "__init__.py" -delete' \;
	@echo "Migration directory cleaned!"

destroy-database: 	## Destroy local database
	@echo "Destroying Docker volume 'django_cat_postgres_data-local'..."
	@docker volume rm -f django_cat_postgres_data-local
	@echo "Docker volume destroyed!"

remove-all:			## Remove migrations and DB local
	@echo "Remove migrations and DB local"
	@make remove-migrations
	@make destroy-database

git-sync-branches:
	@echo "Fetching..."
	@git fetch --prune
	
	@echo "Deleting local branch..."
	@git branch -vv | grep ': gone]' | awk '{print $$1}' | xargs -r git branch -D
	
	@echo "Creating new branch from origin..."
	@git branch -r | grep -v '\->' | grep -v 'origin/main\|origin/dependabot' | sed 's/origin\///' | while read branch; do git branch --track "$$branch" "origin/$$branch" 2>/dev/null || true; done

up-ngrok:
	@ngrok http 8000