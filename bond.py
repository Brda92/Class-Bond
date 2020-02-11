import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np
from scipy.interpolate import splev, splrep



rsd_yields = {'3M':[2.30, 136], '6M':[2.64, 276], '53W':[3.48, 551], '2Y':[2.69, 913],
		'3Y':[3.39, 1461], '5Y':[4.00, 2191], '7Y':[3.40, 3104], '10Y':[4.80, 5000]}




def get_rsd_yield(num_of_days):
	for i in rsd_yields:
		if num_of_days < rsd_yields[i][1]:
			return rsd_yields[i][0]/100


def interpolated_rsd_yield(num_of_days):	
	num_of_days_list = [90, 180, 371, 730, 1095, 1826, 2555, 3652]
	yld_list = [rsd_yields[i][0] for i in rsd_yields]

	tcks = splrep(num_of_days_list, yld_list)
	return splev(num_of_days, tcks)/100 


class Bond:

	def __init__(self, settlement_date, maturity_date, coupon_rate, frequency=1, face_value=10000, currency='RSD'):	
		self.settlement_date = self.__format_date(settlement_date)
		self.maturity_date = self.__format_date(maturity_date)
		self.coupon_rate = coupon_rate
		self.frequency = frequency
		self.face_value = face_value
		self.currency = currency
		self.coupon = self.face_value * self.coupon_rate/100

		if (self.maturity_date - self.settlement_date).days < 0:
			print("Maturity date should be after settlement_date")

	def __format_date(self, dat):
		try:
			dat = dt.datetime.strptime(dat, '%d.%m.%Y').date()
			return dat
		except:
			print("Date should be in format 'dd.mm.yyyy'")

	def __date_diff(self, settle_date, maturity_date):
		if not isinstance(settle_date, dt.date):
			settle_date = self.__format_date(settle_date)
		
		if not isinstance(maturity_date, dt.date):
			maturity_date = self.__format_date(maturity_date)

		return (maturity_date - settle_date).days

	def __create_date_diff_lists(self, settle_date):
		cpc = self.coup_dates_to_come(settle_date)
		dl = np.array([self.__date_diff(settle_date, i) for i in cpc])
		return dl

	def __yield_map(self, date_diff_list, yield_curve):
		if yield_curve == 'rsd':
			l = np.array(list(map(get_rsd_yield, date_diff_list)))/self.frequency + 1
		elif yield_curve == 'rsd_inter':
			l = np.array(list(map(interpolated_rsd_yield, date_diff_list)))/self.frequency + 1
		return l
		
# Returns all coupon dates of a bond
	def all_coup_dates(self):
		hlp = self.settlement_date
		all_cd = []

		while self.__date_diff(hlp, self.maturity_date) > 0:
			all_cd.append(hlp + relativedelta(months=+12/self.frequency))
			hlp = all_cd[-1]
		return all_cd	


# Returns next coupon date
	def next_coup_date(self, dat):		
		dat = self.__format_date(dat)
		all_cd = self.all_coup_dates()

		for i in range(0,len(all_cd)):
			if self.__date_diff(all_cd[i], dat) > 0 and self.__date_diff(all_cd[i+1], dat) < 0:
				return all_cd[i+1]
			elif self.__date_diff(all_cd[i], dat) < 0 and self.__date_diff(all_cd[i+1], dat) < 0:
				return all_cd[0]

# Returns all coupon dates to come
	def coup_dates_to_come(self, settle_date):
		all_cd = self.all_coup_dates()
		cdl = all_cd[all_cd.index(self.next_coup_date(settle_date)):]
		return cdl		

# Returns numpy array of cash flows
	def cash_flow(self, settle_date=None):
		if settle_date is None:
			ln = len(self.all_coup_dates())
		else:
			ln = len(self.coup_dates_to_come(settle_date))

		l = []	
		cp = self.coupon/self.frequency
		
		l = [cp for i in range(1, ln)]
		l.append(cp + self.face_value)
		return np.array(l)
 
 # Returns present value of a cash flow
	def cash_flow_pv(self, settle_date, yield_curve):
		ddl = self.__create_date_diff_lists(settle_date)
		cf = self.cash_flow(settle_date)
		ylds = self.__yield_map(ddl, yield_curve)
		exp = ddl/(365.25/self.frequency)
		cf_pv = cf / (ylds ** exp)

		return cf_pv
# Returns price of a bond using interpolated RSD curve		
	def bond_price(self, settle_date, yield_curve='rsd_inter'):
		sumc = round(np.sum(self.cash_flow_pv(settle_date,yield_curve)), 4)

		return sumc
			
# Returns price of a bond using "normal" method
	def bond_price2(self, settle_date, yield_curve='rsd'):
		exp = self.__create_date_diff_lists(settle_date)/(365.25/self.frequency)
		cf = self.cash_flow(settle_date)
		ylds = np.full(len(cf), get_rsd_yield(self.__date_diff(settle_date, self.maturity_date))/self.frequency+1)		
		cf_pv = cf/(ylds ** exp)

		sumc = round(np.sum(cf_pv),4)
		return sumc
		
# Returns duration of a bond
	def duration(self, settle_date, yield_curve='rsd'):
		cf_pv = self.cash_flow_pv(settle_date, yield_curve)
		d = self.__create_date_diff_lists(settle_date)/365.25
		bp = self.bond_price(settle_date, yield_curve)
		dur = np.sum(cf_pv/bp*d)

		return dur

# Returns modified duration of a bond
	def mduration(self, settle_date, yield_curve='rsd'):
		cf_pv = self.cash_flow_pv(settle_date, yield_curve)
		dl = self.__create_date_diff_lists(settle_date)
		bp = self.bond_price(settle_date, yield_curve)
		y = self.__yield_map(dl, yield_curve)
		d = dl/365.25
		mdur = np.sum((cf_pv/bp*d)/y)

		return mdur


#rsd = Bond('10.10.2014', '10.10.2021', 5, frequency=1)

