# script generator for hwdrc
# jinshi.chen@intel.com 2020/12/22
import getopt, sys


class Args:
	@staticmethod
	def usage(msg=''):
		print(msg)
		print("usage:")
		print("--hp <workload>, specify hp workload, if # passed to --hp or --lp, generate all workloads")
		print("--lp <workload>, specify lp workload, if # passed to --hp or --lp, generate all workloads")
		print("--hinst <inst>, hp instance used by docker, for example, 10")
		print("--linst <inst>, lp instance used by docker, for example, 10")
		print("--hcs <cpus>, hp cpuset used by docker, for example, 0-9, 20-29")
		print("--lcs <cpus>, lp cpuset used by docker, for example, 10-19, 30-39")
		print("--help, print this help message")
		sys.exit(1)

	def __init__(self):
		self.hp = None
		self.lp = None
		self.hcs = None
		self.lcs = None
		self.hinst = None
		self.linst = None

	def __valid__(self):
		if not self.hp or not self.lp \
				or not self.hcs or not self.lcs \
				or not self.hinst or not self.linst:
			return False
		return True

	# report my collected input
	def report(self):
		print("Input: hp: %s, cpuset: %s, instance: %s" % (self.hp, self.hcs, self.hinst))
		print("Input: lp: %s, cpuset: %s, instance: %s" % (self.lp, self.lcs, self.linst))

	# parse user input, if error occurred print usage() then exit
	def parse_input(self):
		opts = []
		try:
			opts, args = getopt.getopt(sys.argv[1:], None, ["hp=", "lp=", "hcs=", "lcs=", "hinst=", "linst=", "help"])
		except getopt.GetoptError as err:
			Args.usage('parse failed')
		for o, a in opts:
			if o in ("--lp"):
				self.lp = a
			elif o in ("--hp"):
				self.hp = a
			elif o in ("--hcs"):
				self.hcs = a
			elif o in ("--lcs"):
				self.lcs = a
			elif o in ("--hinst"):
				self.hinst = a
			elif o in ("--linst"):
				self.linst = a
			elif o in ("--help"):
				Args.usage('received help commmand')
			else:
				assert False, "unhandled option"
		if not self.__valid__():
			Args.usage('invalid input')


def save_script(args, code):
	filename = "../%s-%s_colocation.sh" % (args.hp, args.lp)
	with open(filename, "w") as f:
		f.write(code)
		f.close()


def gen_script(args):
	nl = "\n"
	res = "#!/bin/bash" + nl
	res += "set -u" + nl
	res += nl
	res += "source process/restctl_process.inc.sh" + nl
	res += "# source hook/pqos_msr.inc.sh" + nl
	res += "# source hook/emon.inc.sh" + nl
	res += nl
	res += "HP_CORES=" + args.hcs + nl
	res += "LP_CORES=" + args.lcs + nl
	res += nl
	res += "HP_INSTANCES=" + args.hinst + nl
	res += "LP_INSTANCES=" + args.linst + nl
	res += nl
	res += "LP_MBA=10"
	res += nl
	res += "workload_pair_restctl " + args.hp + " " + args.lp
	return res


def main():
	print(sys.argv)
	args = Args()
	args.parse_input()
	args.report()
	genAll = args.hp == "#" or args.lp == "#"
	if genAll:
		HP_WL = ["specjbb", "rn50", "widedeep", "mlc_benchmark"]
		LP_WL = ["rn50", "specjbb", "mlc_benchmark", "bwaves"]
		for hp in HP_WL:
			for lp in LP_WL:
				args.hp = hp
				args.lp = lp
				code = gen_script(args)
				save_script(args, code)
	else:
		code = gen_script(args)
		save_script(args, code)
	print("finish all")


main()

