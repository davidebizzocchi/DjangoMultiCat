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

# Versioning commands
get-version:
	@cat django_cat/VERSION

update-version:
	@VERSION=$$(cat django_cat/VERSION | cut -c2-); \
	COMMIT=$$(git rev-parse --short HEAD); \
	echo "v$$VERSION-$$COMMIT" > django_cat/VERSION

bump-patch:
	@VERSION=$$(cat django_cat/VERSION | cut -d'-' -f1 | cut -c2-); \
	MAJOR=$$(echo $$VERSION | cut -d. -f1); \
	MINOR=$$(echo $$VERSION | cut -d. -f2); \
	PATCH=$$(echo $$VERSION | cut -d. -f3); \
	NEW_PATCH=$$((PATCH + 1)); \
	echo "v$$MAJOR.$$MINOR.$$NEW_PATCH" > django_cat/VERSION; \
	$(MAKE) update-version

bump-minor:
	@VERSION=$$(cat django_cat/VERSION | cut -d'-' -f1 | cut -c2-); \
	MAJOR=$$(echo $$VERSION | cut -d. -f1); \
	MINOR=$$(echo $$VERSION | cut -d. -f2); \
	echo "v$$MAJOR.$$((MINOR + 1)).0" > django_cat/VERSION; \
	$(MAKE) update-version

bump-major:
	@VERSION=$$(cat django_cat/VERSION | cut -d'-' -f1 | cut -c2-); \
	MAJOR=$$(echo $$VERSION | cut -d. -f1); \
	echo "v$$((MAJOR + 1)).0.0" > django_cat/VERSION; \
	$(MAKE) update-version

get-branch-info:
	@BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	ISSUE_NUM=$$(echo $$BRANCH | cut -d'-' -f1); \
	TYPE=$$(echo $$BRANCH | cut -d'-' -f2); \
	echo "$$BRANCH|$$ISSUE_NUM|$$TYPE"

get-commits:
	@git log --pretty=format:"%h - %s" origin/dev..HEAD

create-release-note:
	@BRANCH_INFO=$$(make -s get-branch-info); \
	BRANCH=$$(echo $$BRANCH_INFO | cut -d'|' -f1); \
	ISSUE_NUM=$$(echo $$BRANCH_INFO | cut -d'|' -f2); \
	TYPE=$$(echo $$BRANCH_INFO | cut -d'|' -f3); \
	OLD_VERSION=$$(cat django_cat/VERSION); \
	if [ "$$TYPE" = "issue" ]; then \
		$(MAKE) bump-patch; \
	elif [ "$$TYPE" = "feature" ]; then \
		$(MAKE) bump-minor; \
	elif [ "$$TYPE" = "release" ]; then \
		$(MAKE) bump-major; \
	fi; \
	NEW_VERSION=$$(cat django_cat/VERSION); \
	COMMITS=$$(make -s get-commits); \
	echo "## Release $$NEW_VERSION\n\n### Informazioni Release\n- **Branch di origine**: $$BRANCH\n- **Branch di destinazione**: dev\n- **Issue**: #$$ISSUE_NUM\n- **Tipo**: $$TYPE\n- **Versione precedente**: $$OLD_VERSION\n- **Nuova versione**: $$NEW_VERSION\n\n### Commit\n$$COMMITS\n\n---\n"

update-releases-md:
	@RELEASE_NOTE=$$(make -s create-release-note); \
	echo "$$RELEASE_NOTE" > temp_release.md; \
	sed -i '' '3i\
	\
	'"$$(<temp_release.md)" docs/releases.md; \
	rm temp_release.md

merge-and-close:
	@BRANCH_INFO=$$(make -s get-branch-info); \
	BRANCH=$$(echo $$BRANCH_INFO | cut -d'|' -f1); \
	ISSUE_NUM=$$(echo $$BRANCH_INFO | cut -d'|' -f2); \
	git checkout dev; \
	git merge --no-ff $$BRANCH; \
	git add django_cat/VERSION docs/releases.md; \
	git commit -m "Close #$$ISSUE_NUM"; \
	git push origin dev

release: ## Esegui una nuova release
	@make -s update-releases-md
	@make -s merge-and-close
	@echo "Release completata con successo"