.PHONY: bootstrap test test-artifacts build verify-artifacts

bootstrap:
	@bash scripts/project-workflow bootstrap

test:
	@bash scripts/project-workflow test

test-artifacts:
	@bash scripts/project-workflow test-artifacts

build:
	@bash scripts/project-workflow build

verify-artifacts:
	@bash scripts/project-workflow verify-artifacts
