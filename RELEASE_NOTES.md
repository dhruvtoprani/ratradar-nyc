# Release Notes

## 0.2 — Public Demo

**Live:** [https://ratradar-nyc.vercel.app](https://ratradar-nyc.vercel.app)

### New

- Midnight Plum × Acid Lime × Signal Coral visual system
- Deployable interactive showcase in `web/`
- Real model benchmark and latest June 1, 2026 predictions
- Interactive public risk map and ZIP intelligence view
- Model curves, feature importance, filters, and CSV export
- Launch-focused PRD and deployment guide
- Demo GIF assets generated from verified browser sessions

### Model

- 177 mapped ZIP areas
- 59,472 ZIP-week rows
- Test ROC-AUC: 0.780
- Test PR-AUC: 0.455
- Weekly top-10 precision: 0.488

### Quality

- Leakage tests cover lag features and target thresholds
- All Streamlit pages browser-verified
- Static showcase receives a separate browser verification pass
- Ruff, Black, and pytest remain required release checks
