import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import customtkinter as ctk
import netCDF4
import numpy as np
import csv
import threading
import matplotlib.pyplot as plt
from cartopy import crs as ccrs
from cartopy.feature import COASTLINE, BORDERS
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.interpolate import griddata

PAGE_SIZE = 500

class NCExtractorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NC Extractor and Viewer")
        self.geometry("900x640")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.current_file_path = None
        self.selected_variable = None
        self._dataset = None
        self._all_rows = []
        self._current_page = 0
        self.create_widgets()

    def destroy(self):
        if self._dataset:
            try: self._dataset.close()
            except: pass
        super().destroy()

    def create_widgets(self):
        ctk.CTkLabel(self, text="NC Extractor and Viewer",
                     font=("Roboto", 24, "bold")).pack(pady=20)
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill=tk.X, padx=20)
        ctk.CTkButton(btn_frame, text="Select File",
                      command=self.select_file).pack(side=tk.LEFT, padx=(0,10))
        self.status_label = ctk.CTkLabel(btn_frame, text="", font=("Roboto", 12))
        self.status_label.pack(side=tk.LEFT, padx=10)
        self.metadata_tree = ttk.Treeview(self, columns=("Key","Value"), show="headings")
        self.metadata_tree.heading("Key", text="Variable")
        self.metadata_tree.heading("Value", text="Dimensions")
        self.metadata_tree.column("Key", width=200)
        self.metadata_tree.column("Value", width=400)
        self.metadata_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.metadata_tree.bind("<Double-1>", self.on_variable_selected)

    def set_status(self, msg, color="gray"):
        self.after(0, lambda: self.status_label.configure(text=msg, text_color=color))

    def select_file(self):
        fp = filedialog.askopenfilename(
            title="Select a NetCDF file",
            filetypes=[("NetCDF files","*.nc"),("All files","*.*")])
        if fp:
            self.current_file_path = fp
            self.load_metadata(fp)

    def load_metadata(self, fp):
        self.metadata_tree.delete(*self.metadata_tree.get_children())
        if self._dataset:
            try: self._dataset.close()
            except: pass
        try:
            self._dataset = netCDF4.Dataset(fp, 'r')
            skip = {"latitude","longitude","lat","lon","date","valid_time","number","expver"}
            for vn, vd in self._dataset.variables.items():
                if vn not in skip:
                    self.metadata_tree.insert("", tk.END, values=(vn, str(vd.shape)))
            self.set_status(f"Loaded: {fp.split('/')[-1].split(chr(92))[-1]}", "lightgreen")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def on_variable_selected(self, event):
        sel = self.metadata_tree.selection()
        if not sel: return
        self.selected_variable = self.metadata_tree.item(sel, "values")[0]
        if self._dataset is None:
            messagebox.showerror("Error", "No dataset loaded.")
            return
        self.show_variable_data(self._dataset)

    def show_variable_data(self, dataset):
        win = tk.Toplevel(self)
        win.title(f"Variable: {self.selected_variable}")
        win.geometry("940x700")

        # Filter row
        sf = ctk.CTkFrame(win)
        sf.pack(pady=5, fill=tk.X, padx=10)
        ctk.CTkLabel(sf, text="Year:").pack(side=tk.LEFT, padx=(0,4))
        year_var = tk.StringVar(value="All")
        year_dd = ttk.Combobox(sf, textvariable=year_var, width=8)
        year_dd['values'] = ["All"]+[str(y) for y in range(2001,2026)]
        year_dd.pack(side=tk.LEFT, padx=(0,12))
        ctk.CTkLabel(sf, text="Month:").pack(side=tk.LEFT, padx=(0,4))
        month_var = tk.StringVar(value="All")
        month_dd = ttk.Combobox(sf, textvariable=month_var, width=6)
        month_dd['values'] = ["All"]+[f"{m:02d}" for m in range(1,13)]
        month_dd.pack(side=tk.LEFT, padx=(0,12))

        # Coord extract row
        lf = ctk.CTkFrame(win)
        lf.pack(pady=4, fill=tk.X, padx=10)
        ctk.CTkLabel(lf, text="Lat:").pack(side=tk.LEFT, padx=(0,4))
        lat_e = ctk.CTkEntry(lf, width=80)
        lat_e.pack(side=tk.LEFT, padx=(0,10))
        ctk.CTkLabel(lf, text="Lon:").pack(side=tk.LEFT, padx=(0,4))
        lon_e = ctk.CTkEntry(lf, width=80)
        lon_e.pack(side=tk.LEFT, padx=(0,10))
        ctk.CTkButton(lf, text="Extract point",
            command=lambda: self.extract_data(
                lat_e.get(), lon_e.get(),
                year_var.get(), month_var.get())).pack(side=tk.LEFT)

        # Progress label
        prog_lbl = ctk.CTkLabel(win, text="", font=("Roboto",11))
        prog_lbl.pack()

        # Treeview + scrollbar
        tree_frame = tk.Frame(win)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        cols = ["Date","Latitude","Longitude","Value"]
        data_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)
        for c in cols:
            data_tree.heading(c, text=c)
            data_tree.column(c, width=160)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=data_tree.yview)
        data_tree.configure(yscrollcommand=vsb.set)
        data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.LEFT, fill=tk.Y)

        # Pagination row
        pf = ctk.CTkFrame(win)
        pf.pack(pady=4)
        ctk.CTkButton(pf, text="◀ Prev", width=80,
            command=lambda: self._turn_page(data_tree, pg_lbl, -1)).pack(side=tk.LEFT, padx=4)
        pg_lbl = ctk.CTkLabel(pf, text="Page 1")
        pg_lbl.pack(side=tk.LEFT, padx=8)
        ctk.CTkButton(pf, text="Next ▶", width=80,
            command=lambda: self._turn_page(data_tree, pg_lbl, +1)).pack(side=tk.LEFT, padx=4)

        # Action buttons
        bf = ctk.CTkFrame(win)
        bf.pack(pady=6)
        ctk.CTkButton(bf, text="Export visible to CSV",
            command=lambda: self.export_tree_to_csv(data_tree)).pack(side=tk.LEFT, padx=4)
        apply_btn = ctk.CTkButton(bf, text="Apply filter")
        apply_btn.pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(bf, text="Plot map",
            command=lambda: self.plot_data(
                dataset, data_tree, lat_e.get(), lon_e.get())).pack(side=tk.LEFT, padx=4)

        def handle_apply():
            apply_btn.configure(state="disabled", text="Loading…")
            self._current_page = 0
            threading.Thread(
                target=self._load_data_thread,
                args=(dataset, year_var, month_var, data_tree, pg_lbl, apply_btn, prog_lbl),
                daemon=True).start()

        apply_btn.configure(command=handle_apply)

        # Auto-load on open
        apply_btn.configure(state="disabled", text="Loading…")
        threading.Thread(
            target=self._load_data_thread,
            args=(dataset, year_var, month_var, data_tree, pg_lbl, apply_btn, prog_lbl),
            daemon=True).start()

    def _load_data_thread(self, dataset, year_var, month_var,
                          data_tree, pg_lbl, apply_btn, prog_lbl):
        rows = []
        try:
            time_var = dataset.variables.get('valid_time',
                           dataset.variables.get('date'))
            if time_var is None:
                self.after(0, lambda: messagebox.showerror(
                    "Error","No time variable found."))
                return

            units = getattr(time_var,'units','seconds since 1970-01-01')
            cal   = getattr(time_var,'calendar','standard')
            dates = netCDF4.num2date(time_var[:], units, cal)

            lats = dataset.variables.get('latitude',
                       dataset.variables.get('lat'))[:]
            lons = dataset.variables.get('longitude',
                       dataset.variables.get('lon'))[:]
            var  = dataset.variables[self.selected_variable]

            sy = year_var.get()
            sm = month_var.get()
            total = len(dates)

            for i, dt in enumerate(dates):
                if i % 50 == 0:
                    pct = int(i/total*100)
                    self.after(0, lambda p=pct:
                        prog_lbl.configure(text=f"Loading… {p}%"))

                if sy != "All" and str(dt.year) != sy: continue
                if sm != "All" and f"{dt.month:02d}" != sm: continue

                ds = f"{dt.year}-{dt.month:02d}-01"

                for j, la in enumerate(lats):
                    for k, lo in enumerate(lons):
                        if   var.ndim == 3: v = float(var[i,j,k])
                        elif var.ndim == 2: v = float(var[j,k])
                        elif var.ndim == 1: v = float(var[i])
                        else: v = np.nan

                        if isinstance(v, np.ma.MaskedArray):
                            v = float(v.filled(np.nan))

                        if self.selected_variable == "t2m":  v -= 273.15
                        elif self.selected_variable == "tp": v *= 1000

                        rows.append((ds,
                            f"{float(la):.4f}",
                            f"{float(lo):.4f}",
                            f"{v:.4f}" if not np.isnan(v) else "N/A"))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Error", f"Failed to load data:\n{e}"))
            return
        finally:
            self.after(0, lambda: prog_lbl.configure(text=""))
            self.after(0, lambda: apply_btn.configure(
                state="normal", text="Apply filter"))

        self._all_rows = rows
        self.after(0, lambda: self._render_page(data_tree, pg_lbl, 0))

    def _render_page(self, data_tree, pg_lbl, page):
        data_tree.delete(*data_tree.get_children())
        s = page * PAGE_SIZE
        for row in self._all_rows[s:s+PAGE_SIZE]:
            data_tree.insert("", tk.END, values=row)
        tp = max(1,(len(self._all_rows)+PAGE_SIZE-1)//PAGE_SIZE)
        pg_lbl.configure(
            text=f"Page {page+1}/{tp}  ({len(self._all_rows):,} rows total)")
        self._current_page = page

    def _turn_page(self, data_tree, pg_lbl, direction):
        tp = max(1,(len(self._all_rows)+PAGE_SIZE-1)//PAGE_SIZE)
        np_ = self._current_page + direction
        if 0 <= np_ < tp:
            self._render_page(data_tree, pg_lbl, np_)

    def export_tree_to_csv(self, data_tree):
        fp = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv")])
        if not fp: return
        try:
            with open(fp,"w",newline="") as f:
                w = csv.writer(f)
                w.writerow([data_tree.heading(c,"text")
                             for c in data_tree['columns']])
                for rid in data_tree.get_children():
                    w.writerow(data_tree.item(rid,"values"))
            self.set_status(f"Exported → {fp.split(chr(92))[-1]}","lightgreen")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

    def export_all_points_to_csv(self, data):
        fp = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv")])
        if not fp: return
        try:
            with open(fp,"w",newline="") as f:
                w = csv.writer(f)
                w.writerow(["Year","Month","Latitude","Longitude",
                             "t2m (K)","t2m (°C)"])
                for row in data: w.writerow([str(v) for v in row])
            self.set_status("Point data exported.","lightgreen")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

    def plot_data(self, dataset, data_tree, lat, lon):
        lats, lons, vals = [], [], []
        for rid in data_tree.get_children():
            row = data_tree.item(rid,"values")
            if row[3] != "N/A":
                try:
                    lats.append(float(row[1]))
                    lons.append(float(row[2]))
                    vals.append(float(row[3]))
                except ValueError: continue

        if not lats:
            messagebox.showwarning("No data","No plottable rows in current view.")
            return
        if len(np.unique(lons)) < 2 or len(np.unique(lats)) < 2:
            messagebox.showwarning("Insufficient grid",
                "Need ≥2 unique lat and lon values to plot.")
            return

        fig, ax = plt.subplots(figsize=(8,6),
            subplot_kw={'projection': ccrs.PlateCarree()})
        first = data_tree.item(data_tree.get_children()[0],"values")
        ax.set_title(f"{self.selected_variable} — {first[0][:7]}", fontsize=13)
        ax.add_feature(COASTLINE)
        ax.add_feature(BORDERS, linestyle=':')

        gl, gla = np.meshgrid(np.unique(lons), np.unique(lats))
        gv = griddata((lons,lats), vals, (gl,gla), method='linear')
        cmap = {"t2m":"RdYlBu_r","tp":"Blues"}.get(
            self.selected_variable,"viridis")
        ct = ax.contourf(gl, gla, gv, cmap=cmap,
                         transform=ccrs.PlateCarree())
        ax.grid(color='gray', linestyle='--', linewidth=0.5, zorder=5)
        plt.colorbar(ct, ax=ax, orientation='horizontal',
                     label=self.selected_variable, pad=0.05)

        if lat and lon:
            try:
                ax.plot(float(lon), float(lat), marker='o',
                        color='red', markersize=8,
                        transform=ccrs.PlateCarree(), zorder=10)
                ax.text(float(lon), float(lat), '  Selected',
                        fontsize=9, color='red',
                        transform=ccrs.PlateCarree())
            except ValueError: pass

        pw = tk.Toplevel(self)
        pw.title("Map plot")
        pw.geometry("900x700")
        cv = FigureCanvasTkAgg(fig, master=pw)
        cv.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        cv.draw()
        ctk.CTkButton(pw, text="Save plot as PNG",
            command=lambda: self.save_plot(fig)).pack(pady=8)

    def save_plot(self, fig):
        fp = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files","*.png"),("All files","*.*")])
        if fp:
            fig.savefig(fp, dpi=150, bbox_inches='tight')
            self.set_status(f"Plot saved → {fp.split(chr(92))[-1]}","lightgreen")

    def extract_data(self, lat, lon, year, month):
        if not lat or not lon:
            messagebox.showwarning("Missing input",
                "Please enter both Latitude and Longitude.")
            return
        try: float(lat); float(lon)
        except ValueError:
            messagebox.showerror("Invalid input","Lat/Lon must be numbers.")
            return
        threading.Thread(target=self._extract_thread,
            args=(lat,lon,year,month), daemon=True).start()

    def _extract_thread(self, lat, lon, year, month):
        try:
            ds = self._dataset
            lats = ds.variables.get('latitude', ds.variables.get('lat'))[:]
            lons = ds.variables.get('longitude', ds.variables.get('lon'))[:]

            # Vectorised nearest-cell lookup (fixes original bug)
            li = int(np.argmin(np.abs(lats - float(lat))))
            loi= int(np.argmin(np.abs(lons - float(lon))))
            nlat, nlon = float(lats[li]), float(lons[loi])

            tv    = ds.variables.get('valid_time', ds.variables.get('date'))
            units = getattr(tv,'units','seconds since 1970-01-01')
            cal   = getattr(tv,'calendar','standard')
            dates = netCDF4.num2date(tv[:], units, cal)
            var   = ds.variables[self.selected_variable]

            export = []
            for i, dt in enumerate(dates):
                if year  != "All" and str(dt.year)      != year:  continue
                if month != "All" and f"{dt.month:02d}" != month: continue

                if   var.ndim == 3: v = float(var[i,li,loi])
                elif var.ndim == 2: v = float(var[li,loi])
                else:               v = float(var[i])

                vk = v
                if self.selected_variable == "t2m":
                    vc = v - 273.15
                    export.append((dt.year, dt.month,
                        f"{nlat:.4f}", f"{nlon:.4f}",
                        f"{vk:.4f}", f"{vc:.4f}"))
                elif self.selected_variable == "tp":
                    export.append((dt.year, dt.month,
                        f"{nlat:.4f}", f"{nlon:.4f}",
                        f"{v*1000:.4f}", ""))
                else:
                    export.append((dt.year, dt.month,
                        f"{nlat:.4f}", f"{nlon:.4f}",
                        f"{v:.4f}", ""))

            if export:
                self.after(0, lambda: self.export_all_points_to_csv(export))
            else:
                self.after(0, lambda: messagebox.showinfo(
                    "No data","No records for selected filters."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Extraction error", f"Failed:\n{e}"))

if __name__ == "__main__":
    app = NCExtractorGUI()
    app.mainloop()