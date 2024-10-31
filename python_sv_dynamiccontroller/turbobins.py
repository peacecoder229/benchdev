#!/usr/bin/python

import sys, getopt
import csv
import math

doubleline = "======================================================================"
singleline = "----------------------------------------------------------------------"
verbose = 0
max_cores = 28

# this specifies the "last" core at a given frequency
# there should be 8 entries in the array
buckets=[2,4,8,12,16,20,24,28]

def main(argv):
   global colid
   global binsize
   global verbose
   global excel_out
   inputfile = ''
   max_samples = 10000
   excel_out = 0
   exponent = 2.6 # tunable parameter for current to cores
   usage =  'turbobins.py --p0 34 --p0n 28 --cores 20\nturbobins.py -i lira.csv'
   try:
     opts, args = getopt.getopt(argv,"hvei:a:n:c:s:", ["help","verbose","excel_out","ifile=","p0=","p0n=","cores=","exponent="])
   except getopt.GetoptError:
      print usage
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print usage
         sys.exit()
      elif opt in ("-v", "--verbose"):
        verbose = 1
      elif opt in ("-e", "--excel_out"):
        excel_out = 1
      elif opt in ("-a", "--p0"):
        p0 = int(arg)
      elif opt in ("-n", "--p0n"):
        p0n = int(arg)
      elif opt in ("-c", "--cores"):
        cores = int(arg)
      elif opt in ("-s", "--exponent"):
        exponent = float(arg)
      elif opt in ("-i", "--ifile"):
         inputfile = arg

   if (inputfile == ""): 
     calculate_bins(p0, p0n, cores, exponent)
   else: 
     with open(inputfile, 'rb') as f:
       # name,cores,p0,p0n,p0_avx,p0n_avx,p0_avx3,p0n_avx3
       reader = csv.reader(f)

       if (excel_out == 0):
         # print LIRA header
         string = "QDF,CPU SPEED IN LOW FREQ MODE,CLM RAPL SCALE FACTOR"
         for x in ["sse", "avx2", "avx3"]:
           for y in range(8):
              string += ",%s_corebucket%d"%(x, y)
           for y in range(8):
              string += ",%s_ratiobucket%d"%(x, y)
         string += ",QDF"
         print string

       # default locations in csv file
       core_col = 1
       name_col = 0
       freq_start_col = 2
       for row in reader:
         try:
           if (row[0] <> "Current"):
             x = float(row[0])
         except:
           for x in range(len(row)):
             if (row[x] == "All Core Turbo Freq Rate"):
               freq_start_col = x
             elif (row[x] == "Spec Sequential Number"):
               name_col = x
             elif (row[x] == "Functional Core"):
               core_col = x        
             elif (row[x] == "Speed"):
               speed_col = x        
           continue

         name=row [name_col]
         if (verbose == 1):
           print ">> Processing %s <<"%(name)

         #print freq_start_col
         #print row[freq_start_col]

         #convert GHz to ratio
         #for x in range(2,8,1):
         #  row[x] = float(row[x])

         # hack to handle blank rows
         try:
           x = float(row[freq_start_col+4])
         except:
           print row[name_col]
           continue

         # hack to handle ghz
         for x in range (11):
           row[freq_start_col + x] = row[freq_start_col + x].replace(" GHz", "")

         row[speed_col] = row[speed_col].replace(" GHz", "")

         p0  = float(row[freq_start_col+1])
         p0n = float(row[freq_start_col+0])

         p0_avx2  = float(row[freq_start_col+4])
         p0n_avx2 = float(row[freq_start_col+3])

         p0_avx3  = float(row[freq_start_col+7])
         p0n_avx3 = float(row[freq_start_col+6])
         
         p1_avx3 = float(row[freq_start_col+5])
         p1n_sse = float(row[speed_col])
         clm_p1 = float(row[freq_start_col+9])
         try:
           clm_p0 = float(row[freq_start_col+10])
         except:
           print row[name_col]
           continue

         # error checking
         if (p0n < p0n_avx2):
           print "FAILURE: P0n < P0n_AVX2"
           continue
           sys.exit(0)
         if (p0n < p0n_avx3):
           print "FAILURE: P0n < P0n_AVX3"
           continue
           sys.exit(0)
         if (p0n_avx2 < p0n_avx3):
           print "FAILURE: P0n_AVX2 < P0n_AVX3"
           continue
           sys.exit(0)
         if (p0 < p0_avx2):
           print "FAILURE: P0 < P0_AVX2"
           continue
           sys.exit(0)
         if (p0 < p0n_avx3):
           print "FAILURE: P0 < P0_AVX3"
           continue
           sys.exit(0)
         if (p0_avx2 < p0_avx3):
           print "FAILURE: P0_AVX2 < P0_AVX3"
           continue
           sys.exit(0)

         buckets = []
         # sse
         buckets.append(calculate_bins(p0=p0, p0n=p0n, cores=float(row[core_col]), exponent=exponent, name=row[name_col] + ",SSE", freq_format="GHz"))
         # avx
         buckets.append(calculate_bins(p0=p0_avx2, p0n=p0n_avx2, cores=float(row[core_col]), exponent=exponent, name=row[name_col] + ",AVX2", freq_format="GHz"))
         # avx3
         buckets.append(calculate_bins(p0=p0_avx3, p0n=p0n_avx3, cores=float(row[core_col]), exponent=exponent, name=row[name_col] + ",AVX3", freq_format="GHz"))

         # old code.  harder to read :)
         # sse
         #buckets.append(calculate_bins(p0=10*float(row[freq_start_col+1]), p0n=10*float(row[freq_start_col+0]), cores=float(row[core_col]), exponent=exponent, name=row[name_col]))
         # avx
         #buckets.append(calculate_bins(p0=10*float(row[freq_start_col+4]), p0n=10*float(row[freq_start_col+3]), cores=float(row[core_col]), exponent=exponent, name=row[name_col]))
         # avx3
         #buckets.append(calculate_bins(p0=10*float(row[freq_start_col+7]), p0n=10*float(row[freq_start_col+6]), cores=float(row[core_col]), exponent=exponent, name=row[name_col]))

         # pad the lists
         for bucket in buckets:
           while len(bucket[0]) < max_cores:
             bucket[0].append("")
           # pad the fuse lists out to 8
           while len(bucket[1]) < 8:
             bucket[1].append(0)
             bucket[2].append(0)

         # print the LIRA output
         string = name
         # Set pn based on p1_avx3. We want to maintain a dynamic range between pn and p1_avx3
         if p1_avx3 > 1.8:
            pn = 1.2
         elif p1_avx3 > 1.1:
            pn = 1.0
         else:
            pn = 0.8
         string += ",%.1f" %pn

         # Compute CLM RAPL SCALE FACTOR from core P0n, core P1n, CLM P0 and CLM P1
         if (p0n == p1n_sse):
           #print row[name_col]
           #print "ERROR: P0n is equal to P1n_sse"
           #continue
           clm_rapl_scale_factor = 0.25
         elif (clm_p0 == clm_p1):
           #print row[name_col]
           #print "ERROR: clm_p0 is equal to clm_p1"
           #continue
           clm_rapl_scale_factor = 0.25
         else:
           #print "%f, %f, %f, %f" %(clm_p0, clm_p1, p0n, p1n_sse)
           clm_rapl_scale_factor = (clm_p0-clm_p1)/float(p0n-p1n_sse)

         #string += ',%1.4f' %(math.ceil(clm_rapl_scale_factor*16)/16)
         #string += ',%1.4f' %(math.ceil(clm_rapl_scale_factor*16)/16.0)
         # Starting SKX H-step, fix clm_rapl_scale_factor to 0.5625
         string += ',0.5625'
         
         for bucket in buckets:
           for core in bucket[1]:
             string += ",%d"%core
           for delta in bucket[2]:
             string += ",%d"%delta
         string += "," + name
         if (excel_out == 0):
           print string

         #print buckets


def calculate_bins(p0, p0n, cores, exponent=3.0, name="", freq_format="ratio"):
  global verbose
  # note: this calculates the DEFAULT answer for a given SKU
  # we must have the option to pick a more (or less) aggressive frequency if needed (by hand)
  # special SKUs may move these values around
  if (freq_format is "GHz"):
    p0 = 10*float(p0)
    p0n = 10*float(p0n)

  p0 = int(p0)
  p0n = int(p0n)
  cores = int(cores)
  config = ["p0", p0, "p0n", p0n, "cores", cores]

  if (p0 < p0n):
     print "FAILURE: P0 < P0n"
     sys.exit(0)

  # calculate pfail constraint
  # 
  # our pfail algorithm sets P01 and P02 to the same frequency
  # we then drop down by 2 bins for P03 and P04
  #   - this can be pessimistic in some cases, but is what we will start with
  # we then drop down 1 more bin for P05 to P0n
  #
  pfail = []
  pfail.append(p0) # 1 and 2 cores turbo get p0
  pfail.append(p0)
  pfail.append(max(p0-2, p0n))  # 3 and 4 core turbo step down by 2 bins (unless we drop below P0n)
  pfail.append(max(p0-2, p0n))
  for core in range(cores - 4):
    pfail.append(max(p0-3, p0n))  # 5+ core turbo steps down 3 bins  (unless we drop below p0n)
    

  # calculate iccmax constraints and min w/ pfail
  iccmax = []
  iccmax_raw = []
  minstate = []
  for core in range (cores):
    iccmax_raw.append(round((p0n * (1.0 * cores / (core+1)) ** float(1.0/exponent)), 2))
    iccmax.append(int(p0n * (1.0 * cores / (core+1)) ** float(1.0/exponent)))
    minstate.append(min(pfail[core], iccmax[core]))


  # create buckets
  # 
  # we identify core counts that we want to have transitions
  #    these are hard coded in the "buckets" array
  # 
  # we work backwards from P0n to P01
  #  - if the core count is one of the "buckets", then we figure out the min of (iccmax, pfail) for picking that frequency
  #  - if the core count is not one of the buckets, then it gets the same frequency as "1 core higher"

  bucketized = []
  bucketized.insert(0,p0n)
  bucketprint = []
  bucketprint.insert(0,88)
  prev = p0n
  
  for core in range (cores-1, 0, -1):
    if core in buckets:
      bucketized.insert(0,minstate[core-1])
      bucketprint.insert(0, 88)
    else:
      bucketized.insert(0,prev)
      bucketprint.insert(0, 11)
    prev = bucketized[0]
  
  # generate the fuse values
  ratio_deltas = []  # this holds the "cumulative ratio deltas" associated with our N buckets
  delta_cores = []    # this holds the last core count before we step down in frequency
 
  last_ratio = p0
  last_core = 0
  for core in buckets:
    # if the bucket core is less or equal to than the number of cores in this sku
    # then we should assign a ratio delta to it
    if (core <= cores):
      # handle a ratio_delta > 7 as it gets encoded into a 3 bit fuse
      if (last_ratio - bucketized[core-1] > 7):
        ratio_deltas[-1] = ratio_deltas[-1] + (last_ratio - bucketized[core-1] - 7)
        last_ratio = bucketized[core-1] + 7 
      ratio_deltas.append(last_ratio - bucketized[core-1])
      delta_cores.append(core) 
      last_ratio = bucketized[core-1]
      if (core == cores):
        last_core = 1
    # handle the case where the "last" core of the SKU is not in a bucket
    # we will just skip hte "next" bucket with the total core count
    # example:
    #   on a 22 core SKU, we will use "22" instead of "24"
    elif (last_core == 0):
      last_core = 1
      delta_cores.append(cores)
      ratio_deltas.append(last_ratio - p0n)
    # for the remaining buckets, just fill them in
    #   - keep the existing bucket numbers, and use a delta of 0
    else:
      ratio_deltas.append(0)
      delta_cores.append(core)
  for ratio_delta in ratio_deltas:
    if ratio_delta > 7:
      print "FAILURE.  ratio_delta>7"
      sys.exit(0)

  if (verbose == 1):
    print doubleline
    print "config:     %s"%(config)
    print "pfail:      %s"%(pfail)
    print "iccmax_raw: %s"%(iccmax_raw)
    print "iccmax: %s"%(iccmax)
    print "Min:        %s"%minstate
    print "buckets   : %s"%(bucketprint)
    print "bucketed  : %s"%(bucketized)
    print "%10s: %s - %s"%(name, config, bucketized)
    print "deltaratio: %s"%(ratio_deltas)
    print "cores     : %s"%(delta_cores)

  if (excel_out == 1):
    line = name
    for x in range(len(bucketized)):
      print (line + "," +"iccmax," + str(x+1) + "," + str(iccmax_raw[x]))
      print (line + "," +"resolved," + str(x+1) + "," + str(bucketized[x]))

  # check out the deltas
  if ratio_deltas[0] <> 0:
    print "ERRORL ratio_delta[0] is not 0"
    sys.exit(0)
  tot = 0
  for x in ratio_deltas:
    tot += x
    if (x < 0):
      print "FAILURE!!! Delta < 0"
      sys.exit(0)
  if (tot <> (p0 - p0n)):
    print "FAILURE!!!! Number of deltas does not add up to difference between P0 and P0n"
    print "Delta Sum: %d"%(tot)
    sys.exit(0)

  prev = -1
  for x in delta_cores:
    if (prev == x):
      print "FAILURE.  Duplicate core count"
      sys.exit(0)

  return [bucketized, delta_cores, ratio_deltas]


if __name__ == "__main__":
   main(sys.argv[1:])


