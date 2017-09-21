#!/usr/bin/env python

# KAPow model. Interfaces with one or more KAPow controllers to build and update a power model
# James Davis, 2016

import lib.power_avg as power_avg
import numpy
import time

class rls:

	def __init__(self, kapow_ctrls, max_N = None, lamb = 0.999, meas_to_avg = 10, meas_settle_time = 1):
		self.kapow_ctrls = kapow_ctrls
		self.max_N = max_N																	# Specify to limit the number of counters used in modelling
		self.lamb_inv = float(1)/lamb														# Inverse of forgetting factor lamb(da)
		self.meas_to_avg = meas_to_avg														# Averaged number of measurements per power measurement taken
		self.meas_settle_time = meas_settle_time											# Settling time (s) to wait before taking power measurements
		if self.max_N:
			order = sum(min(kapow_ctrl.N, self.max_N) for kapow_ctrl in self.kapow_ctrls.values()) + 1
		else:
			order = sum(kapow_ctrl.N for kapow_ctrl in self.kapow_ctrls.values()) + 1
		self.x_hat = numpy.zeros((order, 1))
		self.P = 1000*numpy.identity(order)
		self.a = numpy.zeros((order, 1))													# Static component 'activity' is always largest possible counter value
		self.a[-1, 0] = 2**max(kapow_ctrl.W for kapow_ctrl in self.kapow_ctrls.values()) - 1
		self.updates_remaining = order														# Keep track of number of updates needed until model output is valid

	def update(self):
		'Update model with new activity and power measurements'
		time.sleep(self.meas_settle_time)													# Allow power to settle before measuring
		power = 1000*power_avg.measPower(self.meas_to_avg)
		i = 0
		for kapow_ctrl in self.kapow_ctrls.values():
			if self.max_N:
				N = min(kapow_ctrl.N, self.max_N)
			else:
				N = kapow_ctrl.N
			self.a[i:i + N, 0] = numpy.array(kapow_ctrl.measure()[:N])
			i += N
		k = self.lamb_inv*numpy.dot(self.P, self.a)/(1 + self.lamb_inv*numpy.dot(self.a.T, numpy.dot(self.P, self.a)))
		y_hat = numpy.dot(self.a.T, self.x_hat)
		e = power - y_hat
		self.x_hat = self.x_hat + e*k
		self.P = self.lamb_inv*self.P - self.lamb_inv*numpy.dot(k, numpy.dot(self.a.T, self.P))
		if self.updates_remaining:
			self.updates_remaining -= 1;
		
	def split(self):
		'Split power estimate by kapow_ctrl. Returns dict of estimates including static along with True/False for whether or not model is built yet'
		breakdown = {}
		i = 0
		for kernel, kapow_ctrl in self.kapow_ctrls.iteritems():
			if self.max_N:
				N = min(kapow_ctrl.N, self.max_N)
			else:
				N = kapow_ctrl.N
			a_m = self.a[i:i + N, 0]
			x_hat_m = self.x_hat[i:i + N, 0]
			breakdown[kernel] = float(numpy.dot(a_m.T, x_hat_m))
			i += N
		breakdown['static'] = float(self.x_hat[-1, 0]*self.a[-1, 0])
		return (breakdown, self.updates_remaining == 0)
		