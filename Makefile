# v20-12-2024

VERSION := $(shell cat django_cat/VERSION | cut -d'-' -f1 | cut -c2-)
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

.PHONY: help activate requirements

help:	## Print this help 
	@echo "\nCommand to simplify the use of docker in LOCAL and PROD env\n"
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

activate:	## Acvtivate venv
	@echo "source .venv/bin/activate"

requirements:	## Create requirements.txt from requirements.in
	# @git pull

	@rm -f docker/local/requirements.txt
	
	uv pip compile requirements/local.in -o docker/local/requirements.txt

	source .venv/bin/activate && uv pip install -r docker/local/requirements.txt

	git add */requirements.txt
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
		(docker compose -p django_cat -f docker/local/docker-compose.yml up || exit 1) & \
		PID=$$!; \
		trap 'docker compose -p django_cat -f docker/local/docker-compose.yml down && exit 0' EXIT; \
		wait $$PID; \
	}

shell-bash:			## Open a sh shell in LOCAL inside app
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
	@COMMIT=$$(git rev-parse --short HEAD); \
	echo "v$(VERSION)-$$COMMIT" > django_cat/VERSION

bump-patch:
	@MAJOR=$$(echo $(VERSION) | cut -d. -f1); \
	MINOR=$$(echo $(VERSION) | cut -d. -f2); \
	PATCH=$$(echo $(VERSION) | cut -d. -f3); \
	NEW_PATCH=$$((PATCH + 1)); \
	echo "New patch version: v$$MAJOR.$$MINOR.$$NEW_PATCH"; \
	echo "v$$MAJOR.$$MINOR.$$NEW_PATCH" > django_cat/VERSION; \
	$(MAKE) update-version

bump-minor:
	@MAJOR=$$(echo $(VERSION) | cut -d. -f1); \
	MINOR=$$(echo $(VERSION) | cut -d. -f2); \
	echo "v$$MAJOR.$$((MINOR + 1)).0" > django_cat/VERSION; \
	$(MAKE) update-version

bump-major:
	@MAJOR=$$(echo $(VERSION) | cut -d. -f1); \
	echo "v$$((MAJOR + 1)).0.0" > django_cat/VERSION; \
	$(MAKE) update-version

get-branch-info:
	@ISSUE_NUM=$$(echo $(BRANCH) | cut -d'-' -f1); \
	TYPE=$$(echo $(BRANCH) | cut -d'-' -f2); \
	echo "$(BRANCH)|$$ISSUE_NUM|$$TYPE"

get-commits:
	@git log --pretty=format:"%h - %s" origin/dev..HEAD

create-release-note:
	@BRANCH_INFO=$$(make -s get-branch-info); \
	BRANCH=$$(echo $$BRANCH_INFO | cut -d'|' -f1); \
	ISSUE_NUM=$$(echo $$BRANCH_INFO | cut -d'|' -f2); \
	TYPE=$$(echo $$BRANCH_INFO | cut -d'|' -f3); \
	OLD_VERSION=$$(cat django_cat/VERSION); \
	echo "\n\ntype: $$TYPE"; \
	if [ "$$TYPE" = "issue" ]; then \
		$(MAKE) bump-patch; \
	elif [ "$$TYPE" = "feature" ]; then \
		$(MAKE) bump-minor; \
	elif [ "$$TYPE" = "release" ]; then \
		$(MAKE) bump-major; \
	fi; \
	NEW_VERSION=$$(cat django_cat/VERSION); \
	COMMITS=$$(make -s get-commits); \
	echo "## Release $$NEW_VERSION\n\n### Informazioni Release\n- **Branch di origine**: $$BRANCH\n- **Branch di destinazione**: dev\n- **Issue**: [#$$ISSUE_NUM](https://github.com/davidebizzocchi/DjangoCat/issues/$$ISSUE_NUM)\n- **Tipo**: $$TYPE\n- **Versione precedente**: $$OLD_VERSION\n- **Nuova versione**: $$NEW_VERSION\n\n### Commit\n$$COMMITS\n\n---\n"

update-releases-md:
	echo "update release md $(VERSION) $(BRANCH)"
	@RELEASE_NOTE=$$(make -s create-release-note); \
	echo "# Releases\n\n$$RELEASE_NOTE$$(tail -n +2 docs/releases.md)" > docs/releases.md; \
	git add django_cat/VERSION docs/releases.md;

merge-and-close:
	@BRANCH_INFO=$$(make -s get-branch-info); \
	BRANCH=$$(echo $$BRANCH_INFO | cut -d'|' -f1); \
	ISSUE_NUM=$$(echo $$BRANCH_INFO | cut -d'|' -f2); \
	TYPE=$$(echo $$BRANCH_INFO | cut -d'|' -f3); \
	make update-releases-md; \
	RELEASE_VERSION=$$(cat django_cat/VERSION); \
	git add django_cat/VERSION docs/releases.md; \
	git commit -m "Update version to $$RELEASE_VERSION"; \
	git checkout dev; \
	git merge --no-ff --no-edit $$BRANCH; \
	git commit --amend -m "Close #$$ISSUE_NUM, $$RELEASE_VERSION"; \
	git push origin dev; \
	git push origin --delete $$BRANCH; \
	$(MAKE) git-sync-branches

check-uncommitted:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Errore: Ci sono modifiche non committate. Esegui git status per vedere i dettagli."; \
		exit 1; \
	fi

release: ## Esegui una nuova release
	@make -s check-uncommitted
	@make -s merge-and-close
	@echo "Release completata con successo"