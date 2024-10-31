import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
plt.style.use("fivethirtyeight")
x = [40,60]
plt.pie(x)
plt.title("Pie Chart")
plt.tight_layout()
plt.savefig("plot.png")
