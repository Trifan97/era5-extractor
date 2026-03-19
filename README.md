# ERA5 NetCDF Extractor & Viewer

A desktop application for exploring, filtering, visualising, and extracting ERA5 reanalysis climate data from NetCDF (`.nc`) files — built with Python, customtkinter, Cartopy, and Matplotlib.

Developed as part of PhD research on **agricultural drought vulnerability across the Danube River Basin** at the Czech University of Life Sciences, Prague.

---

![Map plot](https://raw.githubusercontent.com/Trifan97/era5-extractor/main/screenshots/map_plot.png)

---

## Features

- **Load any ERA5 NetCDF file** — automatically detects variables and dimensions
- **Filter by year and month** — instantly subset large datasets without waiting
- **Threaded loading** — UI stays fully responsive while data loads (progress shown)
- **Paginated table** — handles 60,000+ rows smoothly (500 rows per page)
- **Interactive map plot** — Cartopy-powered contour map with coastlines, borders, and colorbar
- **Point extraction** — enter lat/lon coordinates to extract the nearest grid cell time series
- **CSV export** — export visible table page or full extracted point series
- **Save map as PNG** — high-resolution output (150 dpi)
- **Unit conversions** — t2m automatically converted K → °C, tp converted m → mm

---

## Screenshots

### Main window
![Main window](https://raw.githubusercontent.com/Trifan97/era5-extractor/main/screenshots/main.png)

### Filtered data table
![Filtered data](https://raw.githubusercontent.com/Trifan97/era5-extractor/main/screenshots/data_filtered.png)

### Map plot — t2m July 2007
![Map plot](https://raw.githubusercontent.com/Trifan97/era5-extractor/main/screenshots/map_plot.png)

---

## Supported Variables

| Variable | Description | Unit displayed |
|---|---|---|
| `t2m` | 2m air temperature | °C (converted from K) |
| `tp` | Total precipitation | mm (converted from m) |
| Any other variable | Generic display | raw units |

---

## Installation

### Requirements

- Python 3.11 (recommended — tested on 3.11.6)
- Miniconda or Anaconda (recommended for Cartopy on Windows)

### Step 1 — Clone the repository

```bash
git clone https://github.com/Trifan97/era5-extractor.git
cd era5-extractor
```

### Step 2 — Install dependencies

**With conda (recommended):**

```bash
conda install -c conda-forge cartopy netcdf4 numpy matplotlib scipy
pip install customtkinter
```

**With pip only:**

```bash
pip install -r requirements.txt
```

> ⚠️ **Note:** Cartopy installation via pip can be problematic on Windows.
> Using conda is strongly recommended.

### Step 3 — Run the application

```bash
python NC_app.py
```

---

## Usage

### Loading a file

1. Launch the app — `python NC_app.py`
2. Click **Select File** and choose any `.nc` ERA5 file
3. Available variables appear in the main table — coordinate and metadata
   variables (`latitude`, `longitude`, `valid_time`, `expver`) are hidden automatically

### Exploring data

4. **Double-click** any variable (e.g. `t2m`) to open the data window
5. Data loads in the background — a progress percentage is shown
6. Use the **Year** and **Month** dropdowns then click **Apply filter** to subset

### Plotting a map

7. Filter to a specific year + month (single time step)
8. Click **Plot map** — a Cartopy contour map renders in a new window with
   coastlines, country borders, and a colorbar
9. Click **Save plot as PNG** to export at 150 dpi

### Extracting a point time series

10. Enter **Lat** and **Lon** coordinates in decimal degrees
    (e.g. Lat: `48.49`, Lon: `28.30`)
11. Optionally filter by year and/or month
12. Click **Extract point** — the tool finds the nearest grid cell and
    prompts you to save the full time series as CSV

### Exporting table data

- **Export visible to CSV** — saves the current page (up to 500 rows)
- Use **Extract point** for a full coordinate-based time series export

---

## Data source

This tool is designed for ERA5 monthly reanalysis data from the
**Copernicus Climate Data Store (CDS)**:

> [ERA5 monthly averaged data on single levels](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means)

Download `.nc` files for variables such as `2m_temperature` and
`total_precipitation` and open them directly in this tool.
A free CDS account is required to download ERA5 data.

---

## Tech stack

| Library | Purpose |
|---|---|
| `customtkinter` | Modern dark-theme desktop UI |
| `netCDF4` | NetCDF file reading and robust time decoding via `num2date` |
| `numpy` | Array operations and vectorised nearest-cell lookup |
| `matplotlib` | Plotting engine |
| `cartopy` | Geospatial map projections, coastlines, country borders |
| `scipy` | Spatial interpolation (`griddata`) for contour map rendering |
| `threading` | Background data loading — keeps UI responsive |

---

## Planned features

- [ ] Statistics panel — min, max, mean, std per year/month selection
- [ ] Export all pages to CSV in one operation
- [ ] Time series line chart for extracted point
- [ ] Support for multi-variable side-by-side comparison
- [ ] SPEI / SPI drought index calculation layer

---

## Author

**Tudor Trifan**

- 💼 LinkedIn: [linkedin.com/in/tudor-trifan](https://www.linkedin.com/in/tudor-trifan)

---

## License

This project is licensed under the **MIT License** —
free to use, modify, and distribute with attribution.
See [LICENSE](LICENSE) for full terms.
