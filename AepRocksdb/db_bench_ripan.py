#!/usr/bin/python

import threading
import ConfigParser
import sys
import os
import re
import time
import datetime
import subprocess
from glob import glob

ROCKSDB_PATH="/rocksDB/Rocksdb/ApachePassSPDKRocksDB/AepRocksdb"
BENCHMARK_BIN="db_bench"
BENCHMARK_CONFIG="db_bench.config"
BENCHMARK_RESULTS=ROCKSDB_PATH+"/results/"

class benchmark():
        def __init__(self,args):
                usage = '''
Usage: db_bench.py [args]
--verbose
                '''

                self.BENCHMARK_RESULTS_PATH=BENCHMARK_RESULTS+str(time.time())
		os.environ['LD_PRELOAD'] = ROCKSDB_PATH + '/libs/libjemalloc.so.1'
		os.environ['LD_LIBRARY_PATH'] = ROCKSDB_PATH + '/libs'
                os.system("mkdir -p "+self.BENCHMARK_RESULTS_PATH)
                self.collect_sysinfo()
                self.parser_config()
                self.launch_benchmark()
		

        def collect_sysinfo(self):
                os.system("mkdir "+self.BENCHMARK_RESULTS_PATH+"/sys-info")
                os.system("cat /proc/meminfo > "+self.BENCHMARK_RESULTS_PATH+"/sys-info/meminfo.txt")
                os.system("cat /proc/cpuinfo > "+self.BENCHMARK_RESULTS_PATH+"/sys-info/cpuinfo.txt")

        def usage(self):
                print "db_bench arguments must be specified in db_bench.config"

        def read_config(self):
                Config=ConfigParser.ConfigParser()
                Config.read(os.path.join(ROCKSDB_PATH,BENCHMARK_CONFIG))
                return Config

        def parser_config(self):
                self.arguments=""
                Config=self.read_config()
                for option in Config.items("BENCHMARK"):
                        if option[0] == 'num':
                                self.keys_list=option[1].split(",")
                        elif option[0] == 'benchmarks':
                                self.benchmarks_list=option[1].split(",")
			elif option[0] == 'db':
                                self.db_list=option[1].split(",")
                        elif option[0] == 'write_buffer_size':
                                self.write_buffer_size_list=option[1].split(",")
                        elif option[0] == 'cache_size':
                                self.cache_size_list=option[1].split(",")
			elif option[0] == 'block_size':
				self.block_size_list=option[1].split(",")
                        elif option[0] == 'mmap_read':
                                self.mmap_read_list=option[1].split(",")
                        elif option[0] == 'max_write_buffer_number':
                                self.max_write_buffer_number_list=option[1].split(",")
			elif option[0] == 'key_size':
                                self.key_size_list=option[1].split(",")
			elif option[0] == 'value_size':
				self.value_size_list=option[1].split(",")
                        elif option[0] == 'threads':
                                self.threads_list=option[1].split(",")
                        elif option[1] != '':
                                self.arguments+=" --"+option[0]+"="+option[1]
                       # if option[0] == 'db':
                       #         self.db_path=option[1]

        def parse_log(self,stdout,job,benchmark_arg,db_arg,write_buffer_size_arg,key_arg,cache_size_arg,block_size_arg,mmap_read_arg,max_write_buffer_number_arg,key_size_arg,value_size_arg,threads_arg):
                self.f.write(job+','+benchmark_arg.split("=")[1]+','+db_arg.split("=")[1]+','+write_buffer_size_arg.split("=")[1]+','+key_arg.split("=")[1]+','+cache_size_arg.split("=")[1]+','+block_size_arg.split("=")[1]+','+mmap_read_arg.split("=")[1]+','+max_write_buffer_number_arg.split("=")[1]+','+key_size_arg.split("=")[1]+','+value_size_arg.split("=")[1]+','+threads_arg.split("=")[1]+',')
                for line in stdout.split('\n'):
                        if "micros/op" in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[2]+','+line_split[4]+','+line_split[6]+',')
                        elif "Count: " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[1]+','+line_split[3]+','+line_split[5]+',')
                        elif "Min: " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[1]+','+line_split[3]+','+line_split[5]+',')
                        elif "Percentiles: " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[2]+','+line_split[4]+','+line_split[6]+','+line_split[8]+','+line_split[10]+',')
                        elif "rocksdb.memtable.hit " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[3]+',')
                        elif "rocksdb.memtable.miss " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[3]+',')
                        elif "rocksdb.l0.hit " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[3]+',')
                        elif "rocksdb.l1.hit " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[3]+',')
                        elif "rocksdb.number.keys.written " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[3]+',')
                        elif "rocksdb.number.keys.read " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[3]+',')
                        elif "rocksdb.bytes.written " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[3]+',')
                        elif "rocksdb.bytes.read " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[3]+',')
                        elif "rocksdb.wal.bytes " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[3]+',')
                        elif "rocksdb.flush.write.bytes " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[3]+',')
			elif "rocksdb.db.get.micros " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[9]+',')
                        elif "rocksdb.db.write.micros " in line:
                                line_split=re.split('\s+',line.strip())
                                self.f.write(line_split[9]+'\n')


        def iostat_monitor(self,job):
                #os.popen("./iostat_monitor.sh "+str(job)+" "+self.JOB_PATH+"/iostat-"+"job"+str(job)+".txt").read()
                os.system("./iostat_monitor.sh "+str(job)+" "+self.JOB_PATH+"/iostat-"+"job"+str(job)+".txt")

        def vmstat_monitor(self,job):
                #os.popen("./vmstat_monitor.sh "+str(job)+" "+self.JOB_PATH+"/vmstat-"+"job"+str(job)+".txt").read()
                os.system("./vmstat_monitor.sh "+str(job)+" "+self.JOB_PATH+"/vmstat-"+"job"+str(job)+".txt")

        def sar_monitor(self,job):
                #os.popen("./sar_monitor.sh "+str(job)+" "+self.JOB_PATH+"/sar-"+"job"+str(job)+".txt").read()
                os.system("./sar_monitor.sh "+str(job)+" "+self.JOB_PATH+"/sar-"+"job"+str(job)+".txt")

        def parse_jobs(self):
                self.f.write(",\n")
                self.f.write("Defaults: ,"+self.arguments.replace("--","")+"\n")
                for job in glob(self.BENCHMARK_RESULTS_PATH+"/job*/"):
                        f_job=open(job+"db_bench.txt")
                        lines=f_job.readlines()
                        lines[1]=lines[1].replace(ROCKSDB_PATH,"")
                        lines[1]=lines[1].replace(BENCHMARK_BIN,"")
                        lines[1]=lines[1].replace(self.arguments,"")
                        line=lines[1].split()[1]+" "+lines[1].split()[2]+" "+lines[1].split()[3]+" "+lines[1].split()[4]+" "+lines[1].split()[5]+" "+lines[1].split()[6]+" "+lines[1].split()[7]
                        self.f.write(lines[0][:-1]+","+line.replace("--","")+"\n")

        def launch_benchmark(self):
                self.f=open(self.BENCHMARK_RESULTS_PATH+'/db_bench.csv','w')
                self.f.write('Job,benchmark,db,write_buffer_size,keys,cache_size,block_size,mmap_read,max_write_buffer_number,key_size,value_size,threads,Micros/Op,Ops/Sec,MB/s,Count,Average,StdDev,Min,Median,Max,P50,P75,P99,P99.9,P99.99,memtable.hit,memtable.miss,l0.hit,l1.hit,number.keys.written,number.keys.read,bytes.written,bytes.read,wal.bytes,flush.write.bytes,db.get.micros,db.write.micros\n')
                job=1
                for n_benchmarks in self.benchmarks_list:
			for n_db in self.db_list:
	                        for n_write_buffer_size in self.write_buffer_size_list:
        	                        for n_keys in self.keys_list:
                	                        for n_cache_size in self.cache_size_list:
							for n_block_size in self.block_size_list:
	                        	                        for n_mmap_read in self.mmap_read_list:
        	                        	                        for n_max_write_buffer_number in self.max_write_buffer_number_list:
                	                        	                        for n_threads in self.threads_list:
											for n_key_size in self.key_size_list:
		                        	                	                	for n_value_size in self.value_size_list:

													self.db_path=n_db
											                self.JOB_PATH=self.BENCHMARK_RESULTS_PATH+"/job-"+str(job)
        		                        	                        	                os.popen("mkdir "+self.JOB_PATH).read()
													emon_cmd=("emon -i /root/emon/skx-2s-events.txt > "+self.JOB_PATH+"/emon_0.out &")
                                                                                                	#os.popen(emon_cmd).read()

	                		                        	                                benchmark_arg=" --benchmarks="+str(n_benchmarks)
													db_arg=" --db="+str(n_db)
        	        		                                	                        write_buffer_size_arg=" --write_buffer_size="+str(n_write_buffer_size)
                		        	                                	                key_arg=" --num="+str(n_keys)
                		                	                                	        cache_size_arg=" --cache_size="+str(n_cache_size)
													block_size_arg=" --block_size="+str(n_block_size)
                       	        		                	                         	mmap_read_arg=" --mmap_read="+str(n_mmap_read)
                       		                	                	             		max_write_buffer_number_arg=" --max_write_buffer_number="+str(n_max_write_buffer_number)
													key_size_arg=" --key_size="+str(n_key_size)
													value_size_arg=" --value_size="+str(n_value_size)
                                        	                        	  			threads_arg=" --threads="+str(n_threads)
                                                                                                        strgname=str(n_db)
                                                                                                        emonname=re.sub('/mnt/','',strgname)+str(n_keys)

			                                                        	                #f_disk=open(self.JOB_PATH+"/disk_usage.txt","w")
        			                                                        	        #thread_iostat = threading.Thread(target = self.iostat_monitor, args = [job], name = "iostat")
        			                                                                	#thread_iostat.start()
	        	        		                                                        #thread_vmstat = threading.Thread(target = self.vmstat_monitor, args = [job], name = "vmstat")
        		                		                                                #thread_vmstat.start()
        		                        		                                        #thread_sar = threading.Thread(target = self.sar_monitor, args = [job], name = "sar")
        	        	                        		                                #thread_sar.start()
        	                	                        		                        #f_disk.write("Before test: \n")
        	                        	                        		                #f_disk.write(os.popen("df /mnt/pmem/").read()+"\n")

													#sar_cmd=("sar 1 > "+self.JOB_PATH+"/sar.out &")
                                                                                                        #os.popen(sar_cmd).read()


        	                                	                        		        print (os.path.join(ROCKSDB_PATH,BENCHMARK_BIN)+self.arguments+benchmark_arg+db_arg+write_buffer_size_arg+key_arg+cache_size_arg+block_size_arg+mmap_read_arg+max_write_buffer_number_arg+key_size_arg+value_size_arg+threads_arg+" 2>&1 | tee "+self.JOB_PATH+"/LOG-execution.txt")
                	                                	                        		#cmd=os.path.join(ROCKSDB_PATH,BENCHMARK_BIN)+self.arguments+benchmark_arg+write_buffer_size_arg+key_arg+cache_size_arg+" 2>&1 | tee "+self.JOB_PATH+"/LOG-execution.txt"
                                                                                                        os.system("free && sync && echo 3 > /proc/sys/vm/drop_caches && free")
                                                                                                        emonrun="/pnpdata/emon/run_emon.sh " + emonname + " &"
                                                                                                        #os.system(emonrun)
                                                                                                        #time.sleep(2) 
                                                                                                        
                        	                                	                		cmd=os.path.join(ROCKSDB_PATH,BENCHMARK_BIN)+self.arguments+benchmark_arg+db_arg+write_buffer_size_arg+key_arg+cache_size_arg+block_size_arg+mmap_read_arg+max_write_buffer_number_arg+key_size_arg+value_size_arg+threads_arg     #+" 2>&1 | tee "+self.JOB_PATH+"/LOG_execution.log"
	                                                                	        		start = time.clock()
													stdout=os.popen(cmd).read()
													#os.popen(cmd).read()
													t=time.clock() - start
													#os.popen("killall emon").read()
													os.popen("killall sar").read()

	                                                                        			#print stdout
	                                                                        			#f_disk.write("After test: \n")
	                                                                        			#f_disk.write(os.popen("df /mnt/pmem/").read())
	                                                                        			#f_disk.close()
	                                                                        			out=open(self.JOB_PATH+'/db_bench.txt','w')
													#out=open(self.JOB_PATH+'LOG_execution.log','w')
	                                                                        			out.write("job "+str(job)+"\n")
	                                                                        			out.write(cmd+"\n")
													out.write("Duration: "+str(t)+"\n")
	                                                                        			out.write(stdout)
	                                                                        			out.close()
	                                                                        			self.parse_log(stdout,str(job),benchmark_arg,db_arg,write_buffer_size_arg,key_arg,cache_size_arg,block_size_arg,mmap_read_arg,max_write_buffer_number_arg,key_size_arg,value_size_arg,threads_arg)
	                                                                        			os.popen("cp "+self.db_path+"/LOG "+self.JOB_PATH)
	                                                                        			time.sleep(3)
	                                                                        			job=job+1
                self.parse_jobs()
                print "\n"
                print "#########################################################"
                print "###          BENCHMARK FINISHED SUCCESSFULLY          ###"
                print "###    Results of the benchmark are stored here:      ###"
                print "### "+self.BENCHMARK_RESULTS_PATH+"/db_bench.csv  ###"
                print "#########################################################"

        def run(self,args):
                print args


b = benchmark(sys.argv[1:])
#b.run(sys.argv[1:])
#b.usage()
#b.parser_config()
#b.launch_benchmark()
