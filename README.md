# ENEE457 Team 7 - ML-Based Malware Detection

## Project Overview
Machine learning-based malware detection system using static analysis of Windows PE files with the EMBER dataset.

## Team Members
- **Samuel**: ML Model Training
- **Nathaniel**: GUI Design
- **Vaibhav**: GUI Implementation
- **Stephen**: GUI-Model Integration

## Project Components

### Dataset
- **EMBER 2018**: 1.1M Windows PE files with 2,381 pre-extracted features
- 400k malicious + 400k benign + 300k unlabeled samples

### Machine Learning Approach
- **Primary Model**: XGBoost (Gradient Boosted Decision Trees)
- **Baseline**: Random Forest
- **Analysis Type**: Static analysis of file structure

### Feature Categories (2,381 total)
- File metadata (10 features)
- PE headers (62 features)
- Imported functions (1,280 features)
- Byte entropy histogram (256 features)
- String metadata (104 features)
- Section characteristics (255 features)

### Performance Goals
- **Minimum Target**: 80% accuracy
- **Stretch Goal**: 95% accuracy
- **Precision**: ≥85%
- **Recall**: ≥90%
- **False Positive Rate**: <5%

## Development Environment
- Python 3.10+
- Google Colab (GPU acceleration)
- Libraries: XGBoost, scikit-learn, pandas, NumPy

## Timeline
8-week development schedule (October - December 2025)

## Repository Structure
- `/code/` - ML training scripts
- `SLIDE_CONTENT.md` - Presentation content
- `TEAM_ROLES_REFINED.md` - Team role definitions

---

**University of Maryland**
**ENEE457 - Computer Systems Security**
**Fall 2025**