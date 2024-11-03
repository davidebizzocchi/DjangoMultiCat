
.PHONY: help activate requirements

help:	## Print this help 
	@echo "\nCommand to simplify the use of docker in LOCAL and PROD env\n"
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

activate:	## Acvtivate venv
	@echo "source .venv/bin/activate"

requirements:	## Create requirements.txt from requirements.in
	@git pull

	@rm -f requirements/base.txt
	@rm -f requirements/locale.txt
	
	uv pip compile requirements/base.in -o requirements/base.txt
	uv pip compile requirements/locale.in -o requirements/locale.txt

	source .venv/bin/activate && uv pip install -r requirements/locale.txt

	git add requirements/*.txt
	@git commit -m "automatic upgrade requirements"
	@git push

	# docker rmi -f django_cat-app:local

requirements-load-cat:
	source .venv/bin/activate && cp -r .cat-package/cat .venv/lib/python3.12/site-packages