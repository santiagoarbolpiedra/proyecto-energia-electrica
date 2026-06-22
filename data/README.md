# Data

The data comes from the official portal **[SIMEM](https://www.simem.co/)** (Colombian
Mining and Energy Information System) and from **[PARATEC](https://paratec.xm.com.co/)** (XM).

## Structure

```
data/
├── sample/   # Small versioned samples (used by the app and for demo)
└── raw/      # Full data (NOT versioned — see .gitignore)
```

## How to obtain the full data

The full files are too large to version on GitHub
(`Demanda.csv` ≈ 91 MB, `Generacion.csv` ≈ 86 MB), so they are **not**
included in the repository. To reproduce the full analysis:

1. Download the demand and generation datasets from [SIMEM](https://www.simem.co/).
2. Download the effective capacity from [PARATEC](https://paratec.xm.com.co/).
3. Place them in `data/raw/` with these names:
   - `data/raw/Demanda.csv`
   - `data/raw/Generacion.csv`
   - `data/raw/PARATEC_Capacidadefectiva_27-10-2025.xlsx`

> The samples in `data/sample/` (2,000 rows) are sufficient to run the
> Streamlit application and explore the data structure.
