# TODO: think about capping the number of interations of the while loop in fair_distribute
# TODO: think about making the eff in the case of scalability derived be the same range (1-4) as the sw based eff

import math

max_ratio = 32
min_ratio = 10
ncores = 4
def fair_distribute(budget=0, weight=[1] * ncores, request=[max_ratio, max_ratio, max_ratio, max_ratio]):
 iterations = 0
 residual = budget
 allocation = [0] * ncores
 while residual > 0.1 and sum(weight) != 0:
  fair_share = float(residual)/sum(weight)
  residual = 0
  iterations = iterations + 1
  for i in range(ncores):
   if allocation[i] + fair_share * weight[i] > request[i]:
    residual = residual + allocation[i] + fair_share * weight[i] - request[i]
    allocation[i] = request[i]
    weight[i] = 0
   else:
    allocation[i] = allocation[i] + fair_share * weight[i]
 return [iterations, allocation]

def per_core_budget(pkg_pbm_limit, mins, maxs, epp):
 budget = pkg_pbm_limit * ncores
 eff = [0] * ncores
 ratio_limit = [0] * ncores
 request = [0] * ncores
 for i in range(ncores):
  # EPP -> eff: 0-63 -> 4, 64-127 -> 3, 128-191 -> 2, 192-255 -> 1
  eff[i] = (255 - epp[i])/64 + 1
  mins[i] = max(min_ratio, mins[i])
  maxs[i] = min(max_ratio, maxs[i])
 if pkg_pbm_limit >= max_ratio:
  return [max_ratio] * ncores
 if sum(mins) > budget:
  #"min based budgeting"
  [iter, ratio_limit] = fair_distribute(budget, weight=[1] * ncores, request=mins)
 else:
  #"min+eff based budgeting"
  ratio_limit = list(mins)
  budget = budget - sum(mins)
  for i in range(ncores):
   request[i] = maxs[i] - mins[i]
  [iter, eff_distrib] = fair_distribute(budget, eff, request)
  for i in range(ncores):
   ratio_limit[i] = ratio_limit[i] + eff_distrib[i]
 # Add LPF filtering here
 print "%d iterations" %iter
 return [math.floor(x) for x in ratio_limit]
 
def test():
 print per_core_budget(20, [0] * ncores, [max_ratio] * ncores, [0,1,2,255])
 print per_core_budget(30, [0] * ncores, [31, 23, 15, 7], [0, 64, 128, 192])