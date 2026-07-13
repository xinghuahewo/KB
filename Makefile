.PHONY: bootstrap test test-artifacts build verify-artifacts release deploy rollback

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

release:
	@bash scripts/project-workflow release $(ARGS)

deploy:
	@bash scripts/project-workflow deploy $(ARGS)

rollback:
	@bash scripts/project-workflow rollback $(ARGS)
