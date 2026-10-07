PYTHON ?= .venv/bin/python
TARGET ?= $(HOME)/.agents/skills
SKILL_ARG = $(if $(SKILL),--skill $(SKILL),)

.PHONY: setup check test list diff install rollback upstream-check upstream-diff

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt

list:
	@$(PYTHON) scripts/manage.py list

check:
	@$(PYTHON) scripts/manage.py check

test:
	@$(PYTHON) -m unittest discover -s tests -v

diff:
	@$(PYTHON) scripts/manage.py diff $(SKILL_ARG) --target "$(TARGET)"

install:
	@$(PYTHON) scripts/manage.py install $(SKILL_ARG) --target "$(TARGET)"

rollback:
	@$(PYTHON) scripts/manage.py rollback --target "$(TARGET)"

upstream-check:
	@$(PYTHON) scripts/manage.py upstream-check

upstream-diff:
	@$(PYTHON) scripts/manage.py upstream-diff --skill "$(SKILL)"
