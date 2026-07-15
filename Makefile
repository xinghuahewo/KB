.PHONY: bootstrap test test-artifacts build verify-artifacts release deploy rollback source-ingest canonicalize semantic-build publish-index verify-release

define run_bgpkb_pipeline_stage
	@test -n "$(CANDIDATE_DIR)" || { echo "必须设置 CANDIDATE_DIR 为隔离候选目录" >&2; exit 2; }
	@cd backend && uv run bgpkb-pipeline $(1) --candidate-dir "$(abspath $(CANDIDATE_DIR))" $(PIPELINE_ARGS)
endef

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

source-ingest:
	$(call run_bgpkb_pipeline_stage,source-ingest)

canonicalize:
	$(call run_bgpkb_pipeline_stage,canonicalize)

semantic-build:
	$(call run_bgpkb_pipeline_stage,semantic-build)

publish-index:
	$(call run_bgpkb_pipeline_stage,publish-index)

verify-release:
	$(call run_bgpkb_pipeline_stage,verify-release)
