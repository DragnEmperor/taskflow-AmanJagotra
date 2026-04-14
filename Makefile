format:
	@echo "Formatting code..."
	uvx ruff check --fix . || true
	uvx ruff format .