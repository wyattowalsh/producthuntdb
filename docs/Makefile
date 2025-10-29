# Makefile for Sphinx documentation

# You can set these variables from the command line.
SPHINXOPTS    ?=
SPHINXBUILD   ?= ../.venv/bin/sphinx-build
SPHINXAUTOBUILD ?= ../.venv/bin/sphinx-autobuild
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Install documentation dependencies
install:
	pip install -r requirements-docs.txt

# Clean build directory
clean:
	rm -rf $(BUILDDIR)/*
	rm -rf $(SOURCEDIR)/api/*
	@echo "Cleaned build and generated API docs"

# Build HTML documentation
html:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

# Build HTML with auto-rebuild on changes
livehtml:
	@echo "Checking for existing servers on port 8000..."
	@pkill -f sphinx-autobuild 2>/dev/null || true
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@sleep 1
	@echo "Starting Sphinx autobuild with live-reload..."
	@echo "Watching directories:"
	@echo "  - $(SOURCEDIR)/"
	@echo "  - ../producthuntdb/"
	@echo ""
	@echo "Server will be available at: http://127.0.0.1:8000"
	@echo "Browser will open automatically"
	@echo "Press Ctrl+C to stop"
	@echo ""
	$(SPHINXAUTOBUILD) "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O) \
		--open-browser \
		--port 8000 \
		--host 127.0.0.1 \
		--delay 1 \
		--watch ../producthuntdb \
		--ignore "*.pyc" \
		--ignore "*.pyo" \
		--ignore "*~" \
		--ignore "__pycache__" \
		--ignore ".git" \
		--ignore "*.swp" \
		--ignore "*.swo" \
		--re-ignore ".*\.egg-info.*" \
		--re-ignore ".*/__pycache__/.*"

# Alias for common typo
htmllive: livehtml

# Build documentation and open in browser
open: html
	@python3 -c "import webbrowser; webbrowser.open('file://$(PWD)/$(BUILDDIR)/html/index.html')"

# Check for broken links
linkcheck:
	@$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)/linkcheck" $(SPHINXOPTS) $(O)
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

# Check documentation coverage
coverage:
	@$(SPHINXBUILD) -b coverage "$(SOURCEDIR)" "$(BUILDDIR)/coverage" $(SPHINXOPTS) $(O)
	@echo
	@echo "Coverage check complete; see $(BUILDDIR)/coverage/python.txt"

# Build PDF documentation (requires LaTeX)
latexpdf:
	@$(SPHINXBUILD) -b latex "$(SOURCEDIR)" "$(BUILDDIR)/latex" $(SPHINXOPTS) $(O)
	@echo "Running LaTeX files through pdflatex..."
	@$(MAKE) -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

# Build EPUB documentation
epub:
	@$(SPHINXBUILD) -b epub "$(SOURCEDIR)" "$(BUILDDIR)/epub" $(SPHINXOPTS) $(O)
	@echo
	@echo "Build finished. The epub file is in $(BUILDDIR)/epub."

# Spell check (requires sphinxcontrib-spelling)
spelling:
	@$(SPHINXBUILD) -b spelling "$(SOURCEDIR)" "$(BUILDDIR)/spelling" $(SPHINXOPTS) $(O)
	@echo
	@echo "Spell check complete; see $(BUILDDIR)/spelling/output.txt"

# Quick build for development (no API docs regeneration)
quickhtml:
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O) -E
	@echo
	@echo "Quick build finished. The HTML pages are in $(BUILDDIR)/html."

# Serve the built documentation
serve:
	@echo "Checking for existing servers on port 8000..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@sleep 1
	@echo "Serving documentation at http://localhost:8000"
	@cd $(BUILDDIR)/html && python3 -m http.server 8000

# Full rebuild from scratch
rebuild: clean html
	@echo "Complete rebuild finished."

# Generate API documentation only
apidoc:
	@echo "Generating API documentation..."
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)

# Development mode: clean, build, and open
dev: clean html open

# Production build
prod: clean
	@$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O) -W --keep-going
	@echo
	@echo "Production build finished. The HTML pages are in $(BUILDDIR)/html."

# Catch-all target: route all unknown targets to Sphinx
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
