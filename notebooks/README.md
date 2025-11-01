# ProductHuntDB Kaggle Notebook

This directory contains the production-ready Kaggle notebook for managing Product Hunt datasets with automated daily updates.

## 📁 Files

### Main Notebook
- **`ProductHuntDB Notebook.ipynb`** - Production notebook (11 cells, 21KB)
  - Beautiful HTML header with Product Hunt branding
  - Quick Start Checklist with runtime expectations
  - Streamlined installation and configuration
  - Automated data sync from Product Hunt API
  - CSV export and Kaggle publishing
  - Scheduling guidance for daily updates

### Setup Script
- **`setup.sh`** - Standalone installation script (2.4KB, executable)
  - Detects Kaggle vs local environment
  - Installs ProductHuntDB and dependencies
  - Configures paths and environment
  - Validates installation
  - Can be run independently or from notebook

### Documentation
- **`CRITIQUE.md`** (11KB) - Original analysis identifying issues
- **`REFACTORING_SUMMARY.md`** (10KB) - Implementation details and improvements
- **`BEFORE_AFTER.md`** (12KB) - Visual comparison showing changes

## 🚀 Quick Start

### On Kaggle

1. **Upload Notebook**
   ```
   Upload "ProductHuntDB Notebook.ipynb" to Kaggle
   ```

2. **Configure Secrets** (Settings → Add-ons → Secrets)
   ```
   Required:
   - PRODUCTHUNT_TOKEN = <your token>
   
   Optional (for publishing):
   - KAGGLE_USERNAME = <your username>
   - KAGGLE_KEY = <your API key>
   - KAGGLE_DATASET_SLUG = username/dataset-name
   ```

3. **First Run** (2-4 hours)
   - Uncomment `--full-refresh` in Cell 5
   - Run all cells
   - Complete historical data extraction

4. **Enable Scheduling** (Notebook → Schedule)
   - Re-comment `--full-refresh` in Cell 5
   - Schedule daily runs (~10 minutes each)

### Local Testing

```bash
# Run setup script
bash notebooks/setup.sh

# Or use the notebook
jupyter notebook "notebooks/ProductHuntDB Notebook.ipynb"
```

## 📊 Notebook Structure (11 Cells)

| # | Type | Purpose | Runtime |
|---|------|---------|---------|
| 1 | Code | HTML Header (Product Hunt branding) | Instant |
| 2 | Markdown | Quick Start Checklist | - |
| 3 | Code | Installation & Environment Setup | 30-60s |
| 4 | Code | Initialize Database & Verify API | 10-30s |
| 5 | Code | Sync Data from Product Hunt | 2-4h / 3-5m* |
| 6 | Code | Database Statistics | <5s |
| 7 | Code | Export to CSV | 1-2m |
| 8 | Code | Publish to Kaggle (optional) | 1-2m |
| 9 | Markdown | Scheduling Guide | - |
| 10 | Markdown | Workflow Reference | - |
| 11 | Markdown | Troubleshooting | - |

\* First run: 2-4 hours (full refresh) / Daily: 3-5 minutes (incremental)

## ✨ Key Features

### Beautiful Header
- Product Hunt brand colors (DA552F → FF6154 → FF8A5B gradient)
- Glass-morphism feature badges
- Pattern overlay for depth
- Professional typography

### Quick Start Checklist
- Pre-execution checklist
- Expected runtime table
- Clear configuration guidance
- Resource links

### Smart Installation
- Tries `setup.sh` first (clean, reusable)
- Falls back to inline installation
- Validates configuration automatically
- Clear success/failure indicators

### Flexible Sync Strategies
```python
# First run (full historical data)
sync_command = ["producthuntdb", "sync", "--full-refresh"]

# Daily updates (incremental only)
sync_command = ["producthuntdb", "sync"]

# Testing (limited pages)
sync_command = ["producthuntdb", "sync", "--max-pages", "10"]
```

### Robust Error Handling
- Context-specific troubleshooting
- Graceful degradation
- Clear user guidance
- Non-blocking optional features

### Complete Documentation
- Scheduling guide with best practices
- CLI command reference
- Database schema overview
- Troubleshooting for common issues

## 🎯 Use Cases

### Initial Data Extraction
Run once with `--full-refresh` to populate database with complete Product Hunt history (2-4 hours).

### Daily Updates
Schedule notebook to run daily with incremental sync (3-5 minutes per run).

### Data Analysis
Export CSV files for analysis in pandas, R, or other tools.

### Kaggle Datasets
Automatically publish and version datasets on Kaggle.

## 🔧 Setup Script Usage

The `setup.sh` script can be used independently:

```bash
# Make executable (if needed)
chmod +x notebooks/setup.sh

# Run installation
bash notebooks/setup.sh

# Expected output:
# 📦 Installing ProductHuntDB...
# ✅ Installed from GitHub
# 📦 Installing notebook dependencies...
# ✅ Installed plotly and kaleido
# 🔧 Configuring paths...
# ✅ Setup complete!
```

## 📚 Documentation Guide

### For Users
1. Start with the **Quick Start Checklist** (Cell 2)
2. Follow cells sequentially (1-11)
3. Refer to **Troubleshooting** (Cell 11) if needed

### For Developers
1. Read **CRITIQUE.md** for original analysis
2. Review **REFACTORING_SUMMARY.md** for implementation details
3. Check **BEFORE_AFTER.md** for visual comparison

### For Contributors
- Notebook follows consistent 11-cell structure
- Keep error handling streamlined but robust
- Maintain Product Hunt branding in design
- Test in both Kaggle and local environments

## 🧪 Testing Checklist

Before deploying changes:

- [ ] Test in Kaggle environment
- [ ] Verify setup.sh works
- [ ] Test full refresh sync
- [ ] Test incremental sync
- [ ] Verify CSV export
- [ ] Test Kaggle publishing (if credentials configured)
- [ ] Test scheduled runs
- [ ] Validate error handling paths
- [ ] Check HTML header renders correctly
- [ ] Verify all documentation links work

## 🔍 Troubleshooting

### HTML Header Not Rendering
**Problem:** Cell 1 shows raw HTML code

**Solution:** Cell 1 should be a **code cell** (not markdown) with `%%html` magic:
```python
%%html
<style>...</style>
<div class="ph-header">...</div>
```

### Setup Script Fails
**Problem:** `setup.sh` returns errors

**Solution:** 
1. Check it's executable: `chmod +x setup.sh`
2. Run with bash: `bash setup.sh`
3. Fall back to inline installation in Cell 3

### Secrets Not Loading
**Problem:** PRODUCTHUNT_TOKEN not found

**Solution:**
1. Add in Kaggle: Settings → Add-ons → Secrets
2. Secret name must be exactly `PRODUCTHUNT_TOKEN` (case-sensitive)
3. Re-run Cell 3 (Installation & Setup)

### Sync Takes Too Long
**Problem:** Sync exceeds timeout

**Solution:**
- Use incremental sync (comment out `--full-refresh`)
- Full refresh only needed once
- Data is saved progressively

## 📊 Version History

### Version 2.0 (2025-11-01) - Current
- ✅ Fixed HTML header rendering (code cell with %%html magic)
- ✅ Created standalone setup.sh script
- ✅ Streamlined to 11 focused cells
- ✅ Added Quick Start Checklist
- ✅ Enhanced design with modern CSS
- ✅ Improved error handling
- ✅ Comprehensive documentation

### Version 1.0 (Original)
- 20+ cells with inconsistent numbering
- Markdown cell with broken HTML header
- No setup script
- Verbose error handling
- Basic design

## 🔗 Resources

- **GitHub Repository**: [github.com/wyattowalsh/producthuntdb](https://github.com/wyattowalsh/producthuntdb)
- **Product Hunt API**: [api.producthunt.com/v2/docs](https://api.producthunt.com/v2/docs)
- **Kaggle API**: [kaggle.com/docs/api](https://www.kaggle.com/docs/api)
- **Documentation**: [Main AGENTS.md](../AGENTS.md)

## 📝 License

MIT License - See [LICENSE](../LICENSE) file

## 🤝 Contributing

Contributions welcome! Please:
1. Maintain the 11-cell structure
2. Keep Product Hunt branding consistent
3. Test in both Kaggle and local environments
4. Update documentation for any changes
5. Follow existing error handling patterns

---

**Status**: ✅ Production Ready  
**Version**: 2.0  
**Last Updated**: 2025-11-01  
**Tested**: Kaggle Notebooks, Local Jupyter
