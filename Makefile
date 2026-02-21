.PHONY: install test build clean publish-test publish

# Install the package in editable mode with dev dependencies
install:
	pip install -e .
	pip install pytest requests-mock build twine

# Run tests with the src directory added to PYTHONPATH
test:
	export PYTHONPATH=$${PYTHONPATH}:$(shell pwd)/src && pytest

# Remove build artifacts and temporary files
clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Build the distribution packages (wheel and sdist)
build: clean
	python3 -m build

# Upload to TestPyPI
publish-test: build
	python3 -m twine upload --repository testpypi dist/*

# Upload to real PyPI
publish: build
	python3 -m twine upload dist/*