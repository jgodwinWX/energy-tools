import datetime
import numpy
import pandas

from scipy.optimize import fmin

def costProjection(avg,lower,upper,critical,func):
    # first we find which bound will cost more
    if abs(lower - critical) > abs(upper - critical):
        expensive = func(lower)
        cheap = func(upper)
    elif abs(upper - critical) > abs(lower - critical):
        expensive = func(upper)        
        cheap = func(lower)
    else:
        expensive = func(upper)
        cheap = func(lower)
    expected = func(avg)
    return expected,expensive,cheap

# create data frames for the two CSVs
energy_df = pandas.read_csv("kwhhistory.csv",\
    dtype={'Start Date':str,'End Date':str,'Usage':float,'Bill':float,'Provider':str})
temp_df = pandas.read_csv("dfw.csv",dtype={'dates':str,'highs':float,'lows':float,'precip':str})
monthly_df = pandas.read_csv("dfw_monthly.csv",dtype={'Month':str,'Average':float,'StDev':float,\
    '25th Pct':float,'75th Pct':float})

# extract the fields from the dataframes
electric_start_dates = energy_df['Start Date']  # billing period start date (mm/dd/yyyy)
electric_end_dates = energy_df['End Date']      # billing period end date (mm/dd/yyyy)
electric_usage = energy_df['Usage']             # electric usage (kWh)
electric_bill = energy_df['Bill']               # electric bill (total bill in USD)
electric_provider = energy_df['Provider']       # electric provider/plan
climo_date = temp_df['dates']                   # date of climate data (mm/dd/yyyy)
highs = temp_df['highs']                        # daily high temperature (deg F)
lows = temp_df['lows']                          # daily low temperature (deg F)
months = monthly_df['Month']                    # calendar month
monthly_avg = monthly_df['Average']             # average monthly temperature (deg F)
monthly_lower = monthly_df['25th Pct']          # 25th percentile average temperature (deg F)
monthly_upper = monthly_df['75th Pct']          # 75th percentile average temperature (deg F)

# convert all date variables into datetimes
electric_start_datetimes = numpy.array([datetime.datetime.strptime(x,'%m/%d/%Y')\
    for x in electric_start_dates])
electric_end_datetimes = numpy.array([datetime.datetime.strptime(y,'%m/%d/%Y')\
    for y in electric_end_dates])
climo_datetimes = numpy.array([datetime.datetime.strptime(z,'%m/%d/%Y') for z in climo_date])

# compute the average temperature for each day
avg_temp = numpy.zeros(len(highs))
for i in range(len(climo_datetimes)):
    avg_temp[i] = (highs[i] + lows[i]) / 2.0

# compute the average temperature for each billing cycle
cycle_avg_temp = numpy.zeros(len(electric_end_datetimes))
for i in range(len(cycle_avg_temp)):
    cycle_avg_temp[i] =\
        numpy.mean(avg_temp[numpy.where((climo_datetimes>=electric_start_datetimes[i]) &\
        (climo_datetimes<=electric_end_datetimes[i]))])

# normalize energy usage to a 30 days
electric_norm = numpy.zeros(len(electric_end_datetimes))
for i in range(len(electric_end_datetimes)):
    days = float((electric_end_datetimes[i] - electric_start_datetimes[i]).days)
    electric_norm[i] = electric_usage[i] / (days / 30.0)

# derive polyfit
coefs = numpy.polyfit(cycle_avg_temp,electric_norm,2)

# compute rate by provider
providers = set(electric_provider)
provider_list = list(providers)
provider_amount = dict((x,0.0) for x in providers)
provider_billed = dict((x,0.0) for x in providers)
provider_rate = dict((x,0.0) for x in providers)
for provider in providers:
    for i in range(len(electric_provider)):
        if provider == electric_provider[i]:
            provider_amount[provider] += electric_usage[i]
            provider_billed[provider] += electric_bill[i]
    provider_rate[provider] = provider_billed[provider] / provider_amount[provider]

# user computation section
compute = True
provider_string = ''
for i in range(len(providers)):
    provider_string += "%i: %s\n" % (i,provider_list[i])
while compute:
    print provider_string
    user_provider = int(raw_input('Who is your provider (enter a choice listed above as a number)? '))
    print "%s, Rate: $%.03f per kWh" % (provider_list[user_provider],\
        provider_rate[provider_list[user_provider]])

    user_month = int(raw_input("Month (1-12)? "))
    
    # we need a critical point of the function to pass to the billing forecast function
    func = lambda x: coefs[0] * x ** 2 + coefs[1] * x + coefs[2]
    critical = fmin(func,65.0,full_output=False,disp=False)[0]

    # compute the expected costs
    expected,expensive,cheap = costProjection(monthly_avg[user_month-1],monthly_lower[user_month-1],\
        monthly_upper[user_month-1],critical,func)
    expected_cost = expected * provider_rate[provider_list[user_provider]]
    expensive_cost = expensive * provider_rate[provider_list[user_provider]]
    cheap_cost = cheap * provider_rate[provider_list[user_provider]]

    print "----------------------------"
    print "Month: %s" % months[user_month-1]
    print "\tExpected usage, cost: %.0f kWh, $%.02f" % (expected, expected_cost)
    print "\tInner quartile usage, cost: %.0f-%.0f kWh, $%.02f-%.02f" % \
        (cheap,expensive,cheap_cost,expensive_cost)

    # ask the user if they want another analysis
    again = raw_input("Do another (y=yes,n=no)?")
    if again.lower() == 'n':
        compute = False
