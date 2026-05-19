.PHONY: help setup build test clean watch

help:
	@echo "Lean Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  setup   - Install Lean toolchain via elan"
	@echo "  build   - Build Lean library and proofs"
	@echo "  test    - Run Lean tests"
	@echo "  clean   - Clean build artifacts"
	@echo "  watch   - Watch files and rebuild on change"

setup:
	@command -v elan >/dev/null 2>&1 || { \
		echo "Installing elan (Lean version manager)..."; \
		curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y; \
	}
	@lake update

build:
	@lake build

test:
	@lake build OptionHedge.Tests.UnitTests

clean:
	@lake clean

watch:
	@lake build --watch
