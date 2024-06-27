import pandas as pd
import numpy as np
import math

# For single variable all three libraries return single boolean
x1 = float("nan")
x1 = float(3)


print(f"It's pd.isna: {pd.isna(x1)}")
print(f"It's np.isnan: {np.isnan(x1)}")
print(f"It's math.isnan: {math.isnan(x1)}")