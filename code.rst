# Code Application

## SDB.ipynb

### Configuration

Before running the pipeline, all user-defined parameters must be set
in the configuration cell. The pipeline follows the processing structure
shown in Figure 2, proceeding from preprocessing through water depth
estimation, water constituent retrieval, parameter optimization, and
tide correction.

#### Quick Start

```python
mission      = "Landsat"
data_source  = "gee"
startdate    = "2014-03-15"
enddate      = "2014-04-30"
TARGET_SCALE = 10
PLOT_BANDS   = True
CX_METHOD    = "albert"
CP_METHOD    = "ficek"
AY_METHOD    = "wong"
```

#### Parameters

##### `mission`
Satellite mission to use.

| Value | Description |
|---|---|
| `"Landsat"` | Landsat 8 OLI (currently the only supported mission) |

---

##### `data_source`
Defines how satellite imagery is loaded.

| Value | Description |
|---|---|
| `"gee"` | Retrieve imagery via the Google Earth Engine API |
| `"local"` | Load locally stored image files |

---

##### `startdate` / `enddate`
Date range for image search. Only relevant if `data_source == "gee"`.  
Format: `YYYY-MM-DD`

> **Note:** Scenes are filtered to minimize temporal distance to
> in-situ reference measurements. See Section 5.1 for details on
> scene selection criteria.

---

##### `TARGET_SCALE`
Target pixel size in metres. Images are resampled to this resolution
via bilinear interpolation.

**Default:** `10`

---

##### `PLOT_BANDS`
If `True`, intermediate processing steps and band results are
displayed as plots.

**Default:** `True`

---

##### `CX_METHOD`
Method used to estimate Total Suspended Matter concentration *C*ₓ
(Step 2.2 in the pipeline).

| Value | Reference |
|---|---|
| `"albert"` | Albert & Mobley (2003) |
| `"ficek"` | Ficek et al. (2011) |
| `"parwarti"` | Parwati et al. (2022) |

---

##### `CP_METHOD`
Method used to estimate Phytoplankton Chlorophyll-a concentration *C*ₚ
(Step 2.3 in the pipeline).

| Value | Reference |
|---|---|
| `"albert"` | Albert & Mobley (2003) |
| `"ficek"` | Ficek et al. (2011) |
| `"abbas"` | Abbas et al. (2019) |

---

##### `AY_METHOD`
Method used to estimate CDOM absorption *a*ᵧ(λ₀) (Step 2.3 in
the pipeline).

| Value | Reference |
|---|---|
| `"albert"` | Albert & Mobley (2003) |
| `"ficek"` | Ficek et al. (2011) |
| `"wong"` | Wong et al. (2019) |

---

### Step 0 – Preprocessing

```python
# [Zelle hier einfügen]
```

**What this cell does:**

---

### Step 1 – Empirical Coefficients & Metadata

#### 1.1 Empirical Coefficients & Backscattering Albedo ω_b

```python
# [Zelle hier einfügen]
```

**What this cell does:**

---

#### 1.2 Metadata Extraction & Angle Conversion

```python
# [Zelle hier einfügen]
```

**What this cell does:**

---

#### 1.3 Downward Diffuse Attenuation Coefficient & Deep Water Reflectance

```python
# [Zelle hier einfügen]
```

**What this cell does:**

---

### Step 2 – Water Constituent Retrieval

#### 2.1 Water Depth

```python
# [Zelle hier einfügen]
```

**What this cell does:**

---

#### 2.2 Total Suspended Matter

```python
# [Zelle hier einfügen]
```

**What this cell does:**

---

#### 2.3 Phytoplankton Chlorophyll-a and CDOM

```python
# [Zelle hier einfügen]
```

**What this cell does:**

---

### Step 3 – Parameter Optimization

```python
# [Zelle hier einfügen]
```

**What this cell does:**

---

### Step 4 – Tide Correction

```python
# [Zelle hier einfügen]
```

**What this cell does:**

---

## sdb.py

*Dokumentation folgt.*

---

## parameters.py

*Dokumentation folgt.*
