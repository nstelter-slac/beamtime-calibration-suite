import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sys

mode = eval(sys.argv[1])

# just some random numbers to get started
x = np.random.uniform(-2, 2, 10000)
y = np.random.normal(x**2, np.abs(x) + 1)

if mode == 0:
    sns.regplot(x=x, y=y, x_bins=10, fit_reg=None)
    plt.show()
elif mode == 1:
    fig, ax = plt.subplots()
    sns.regplot(x=x, y=y, x_bins=10, fit_reg=None)
    plt.show()
elif mode == 2:
    fig, ax = plt.subplots()
    sns.regplot(x=x, y=y, x_bins=10, fit_reg=None, ax=ax)
    y = np.random.normal(x**2, np.abs(x) + 2)
    sns.regplot(x=x, y=y, x_bins=10, fit_reg=None, ax=ax)
    plt.show()
elif mode == 3:
    fig, ax = plt.subplots()
    sns.regplot(x=x, y=y, x_bins=10, ax=ax)
    y = np.random.normal(x**2, np.abs(x) + 2)
    sns.regplot(x=x, y=y, x_bins=10, ax=ax)
    plt.show()
elif mode == 4:
    fig, ax = plt.subplots()
    sns.regplot(x=x, y=y, x_bins=10, ax=ax)
    x = np.random.uniform(0, 2, 10000)
    y = np.random.normal(x**2, np.abs(x) + 2)
    sns.regplot(x=x, y=y, x_bins=10, ax=ax)
    plt.show()
