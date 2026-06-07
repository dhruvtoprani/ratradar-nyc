# Deployment

**Current public release:** [https://ratradar-nyc.vercel.app](https://ratradar-nyc.vercel.app)

RatRadar has two release surfaces because Streamlit requires a long-running Python server and websocket connection.

## Public Showcase

The `web/` directory is a static interactive release built from the latest trained model artifacts. It is suitable for Vercel and includes:

- Overview metrics and weekly brief
- Interactive NYC risk map
- ZIP drilldown charts
- Model evaluation curves
- Feature importance
- Filterable prediction table and CSV export
- Methodology and ethical framing

Rebuild its data:

```bash
source .venv/bin/activate
python scripts/build_showcase.py
```

Preview locally:

```bash
python -m http.server 4173 --directory web
```

Deploy:

```bash
vercel deploy web -y
```

The Vercel project is named `ratradar-nyc`.

## Full Streamlit Application

Run locally:

```bash
source .venv/bin/activate
streamlit run app/Home.py
```

For a hosted full application, use a platform designed for persistent Python web processes, such as Streamlit Community Cloud, Render, Railway, or a container service.

## Artifact Contract

The public showcase is generated from:

- `data/predictions/latest_predictions.parquet`
- `data/predictions/all_predictions.parquet`
- `data/external/nyc_modzcta.geojson`
- `models/metrics.json`
- `models/feature_importance.parquet`

Do not manually edit `web/data/`. Rebuild it with `scripts/build_showcase.py`.
