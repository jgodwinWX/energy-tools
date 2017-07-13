# energy-tools
Tools for estimating energy costs using climate data

energy_analysis.py - This file is the only python script in this repository so far. More detailed information can be found in the block header, but in short, this script uses climate data and past electric usage data to attempt to forecast electric usage (and rates) based on monthly normal climate data.

dfw.csv - A file containing daily high, low, and precipitation data from Dallas/Fort Worth since 1900.

dfw_monthly.csv - A file containing monthly averages, standard deviations, and 25th/75th average temperature percentiles for Dallas/Fort Worth. A file like this can be generated using monthly.py in climate-tools.

kwhhistory.csv - A file containing electrical usage and billed amounts for each billing cycle.
