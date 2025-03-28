# v29-03-2025

VERSION := $(shell cat django_cat/VERSION | cut -d'-' -f1 | cut -c2-)
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

.PHONY: help activate requirements

help:  ## Print this help 
	@echo "\nCommands to simplify the use of docker in LOCAL and PROD env\n"
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

activate:	## Acvtivate venv
	@echo "source .venv/bin/activate"

requirements:	## Create requirements.txt from requirements.in

	@rm -f docker/local/requirements.txt
	@rm -f docker/prod/requirements.txt
	
	uv pip compile requirements/local.in -o docker/local/requirements.txt
	uv pip compile requirements/prod.in -o docker/prod/requirements.txt

	source .venv/bin/activate && uv pip install -r docker/local/requirements.txt

build-local-cat:
	docker build -t cheshire-cat-core:latest -f core/core/Dockerfile core/core
	@echo "Image cheshire-cat-core:latest builded and tagged: cheshire-cat-core:latest"

build-ghcr-cat:
	docker pull ghcr.io/cheshire-cat-ai/core:latest
	docker tag ghcr.io/cheshire-cat-ai/core:latest cheshire-cat-core:latest
	@echo "Image cheshire-cat-core:latest builded and tagged: cheshire-cat-core:latest"

destroy-django:
	docker rmi -f django_cat-app:local

destroy-cat:
	docker rmi -f cheshire-cat-core:latest

requirements-load-cat:
	source .venv/bin/activate && cp -r .cat-package/cat .venv/lib/python3.13/site-packages

wait-docker:
	@if ! docker info > /dev/null 2>&1; then \
		if [ -e "/Applications/Docker.app" ]; then \
			echo "Docker is not running. Starting Docker Desktop..."; \
			open -a Docker; \
			echo "Waiting for Docker to be ready..."; \
			until docker info > /dev/null 2>&1; do \
				sleep 2; \
			done; \
			echo "Docker is ready!"; \
		else \
			echo "WARNING: Docker.app not found in standard path."; \
			echo "Make sure Docker is installed and configured correctly."; \
			echo "If you're not on MacOS, or if it works anyway, ignore this message!"; \
		fi; \
	fi

up:
	@{ \
		(docker compose -p django_cat -f docker/local/docker-compose.yml up || exit 1) & \
		PID=$$!; \
		trap 'docker compose -p django_cat -f docker/local/docker-compose.yml down && exit 0' EXIT; \
		wait $$PID; \
	}

upd:
	docker compose -p django_cat -f docker/local/docker-compose.yml up -d

down:
	docker compose -p django_cat -f docker/local/docker-compose.yml down

up-local:
	@$(MAKE) wait-docker
	@$(MAKE) up


shell-bash:			## Open a sh shell in LOCAL inside app
	@docker exec -it django_cat-app-1 /bin/bash

shell-django:		## Open a django shell in LOCAL
	@docker exec -it django_cat-app-1 python manage.py shell 

django-log:
	@docker logs -f django_cat-app-1

init-db:
	@docker exec -it django_cat-app-1 python manage.py init_db

remove-migrations:  ## Remove migrations
	@echo "Cleaning migrations directory..."
	@find . -type d -name "migrations" -exec sh -c 'cd "{}" && find . -type f ! -name "__init__.py" -delete' \;
	@echo "Migration directory cleaned!"

destroy-database:  ## Destroy local database
	@echo "Destroying Docker volume 'django_cat_postgres_data-local'..."
	@docker volume rm -f django_cat_postgres_data-local
	@echo "Docker volume destroyed!"

remove-all:  ## Remove migrations and local DB
	@echo "Removing migrations and local DB"
	@$(MAKE) remove-migrations
	@$(MAKE) destroy-database

git-sync-branches:
	@echo "Fetching..."
	@git fetch --prune
	
	@echo "Deleting local branch..."
	@git branch -vv | grep ': gone]' | grep -vE 'prod|main' | awk '{print $1}' | xargs -r git branch -D
	
	@echo "Creating new branch from origin..."
	@git branch -r | grep -v '\->' | grep -v 'origin/main\|origin/dependabot' | sed 's/origin\///' | while read branch; do git branch --track "$$branch" "origin/$$branch" 2>/dev/null || true; done

# Versioning commands (if your are MAINTAINER)
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
	@git log --pretty=format:"- %h - %s (%an)" origin/dev..HEAD

get-diff-stats:
	@git diff --stat origin/dev..HEAD | tail -n 1

create-release-note:
	@BRANCH_INFO=$$($(MAKE) -s get-branch-info); \
	BRANCH=$$(echo $$BRANCH_INFO | cut -d'|' -f1); \
	ISSUE_NUM=$$(echo $$BRANCH_INFO | cut -d'|' -f2); \
	TYPE=$$(echo $$BRANCH_INFO | cut -d'|' -f3); \
	OLD_VERSION=$$(cat django_cat/VERSION); \
	DIFF_STATS=$$($(MAKE) -s get-diff-stats); \
	echo "\n\ntype: $$TYPE"; \
	if [ "$$TYPE" = "issue" ]; then \
		$(MAKE) bump-patch; \
	elif [ "$$TYPE" = "feature" ]; then \
		$(MAKE) bump-minor; \
	elif [ "$$TYPE" = "release" ]; then \
		$(MAKE) bump-major; \
	fi; \
	NEW_VERSION=$$(cat django_cat/VERSION); \
	COMMITS=$$($(MAKE) -s get-commits); \
	echo "## Release $$NEW_VERSION\n\n### Information\n- **Source branch**: $$BRANCH\n- **Target branch**: dev\n- **Issue**: [#$$ISSUE_NUM](https://github.com/davidebizzocchi/DjangoCat/issues/$$ISSUE_NUM)\n- **Type**: $$TYPE\n- **Previous version**: $$OLD_VERSION\n- **New version**: $$NEW_VERSION\n- **Code change statistics**: $$DIFF_STATS\n\n### Commits\n$$COMMITS\n\n---\n"

update-releases-md:
	echo "update release md $(VERSION) $(BRANCH)"
	@RELEASE_NOTE=$$($(MAKE) -s create-release-note); \
	echo "# Releases\n\n$$RELEASE_NOTE$$(tail -n +2 docs/releases.md)" > docs/releases.md; \
	git add django_cat/VERSION docs/releases.md;

merge-and-close:
	@BRANCH_INFO=$$($(MAKE) -s get-branch-info); \
	BRANCH=$$(echo $$BRANCH_INFO | cut -d'|' -f1); \
	ISSUE_NUM=$$(echo $$BRANCH_INFO | cut -d'|' -f2); \
	TYPE=$$(echo $$BRANCH_INFO | cut -d'|' -f3); \
	$(MAKE) update-releases-md; \
	RELEASE_VERSION=$$(cat django_cat/VERSION); \
	git add django_cat/VERSION docs/releases.md; \
	git commit -m "Update version to $$RELEASE_VERSION"; \
	git checkout dev; \
	git merge --no-ff --no-edit $$BRANCH; \
	git commit --amend -m "Close #$$ISSUE_NUM, $$RELEASE_VERSION"; \
	git tag -a $$RELEASE_VERSION -m "Release $$RELEASE_VERSION"; \
	git push origin dev; \
	git push origin $$RELEASE_VERSION; \
	git push origin --delete $$BRANCH; \
	$(MAKE) git-sync-branches

check-uncommitted:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: There are uncommitted changes. Run git status to see details."; \
		exit 1; \
	fi

release: ## Execute a new release
	@$(MAKE) -s check-uncommitted
	@$(MAKE) -s merge-and-close
	@echo "Release completed successfully"