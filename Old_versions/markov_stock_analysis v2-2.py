"""
@author: Nikhil Bhaip
@version: 2.2
@since: 6/15/16

The S&P 500 program implements an algorithm that finds the percentage change in the S&P 500 Index based on
historical weekly data and visualizes the information as a time series plot in matplotlib. The program also creates a
Markov chain model in which the states are bull market, bear market, and stagnant market. Using the probabilities
associated with this Markov chain model and external technical analysis, the program will predict the future S&P 500
data through a random walk.

The next step would be to include other newer variables like seasonality and clean this up in terms of organization.

"""
# import pandas as pd
# import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator, DateFormatter
from matplotlib.ticker import MultipleLocator
import matplotlib.mlab as mlab
import numpy as np
import quandl


def get_data():
    """
    This function obtains data under certain parameters from Quandl and returns the following information as a Pandas
    DataFrame: date, adjusted closing, and percentage change in adjusted closing from the last week.

    :return: A Pandas DataFrame with columns: Date, Adjusted Close, and Percentage Change.
    """
    quandl.ApiConfig.api_key = "7NU4-sXfczxA9fsf_C8E"
    name = "AMZN" #INDEX_GSPC
    start = "2009-05-23"
    end = "2016-05-23"
    period = "weekly"
    raw_df = quandl.get("YAHOO/" + name, start_date=start, end_date=end, collapse=period)
    adjusted_df = raw_df.ix[:, ['Adjusted Close']]
    adjusted_df["Percentage Change"] = adjusted_df['Adjusted Close'].pct_change() * 100
    return adjusted_df


def percent_change_as_time_plot(adjusted_df):
    """
    This function visualizes the percentage change data as a time series plot.

    :param adjusted_df: Pandas DataFrame with columns: Date, Adjusted Close, and Percentage Change.
    """

    pct_change_list = adjusted_df['Percentage Change'].tolist()
    date_list = adjusted_df.index.values
    fig, ax = plt.subplots()
    ax.plot(date_list, pct_change_list)
    #ax.plot(date_list, adjusted_df["Adjusted Close"])
    plt.xlabel("Years")
    plt.ylabel("Percentage change from last week")
    plt.title("Percentage change in S&P 500 weekly data from 2009 to 2016")
    ax.xaxis.set_minor_locator(MonthLocator())
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    ax.fmt_xdata = DateFormatter('%Y-%m-%d')
    ax.autoscale_view()
    fig.autofmt_xdate()

    plt.show()


def get_params_for_norm_dist(adjusted_df):
    """
    This function returns the mean and standard deviation in the percentage change column of a DataFrame.
    :param adjusted_df: <Data Frame> must have 'Percentage Change' column

    :returns mean and standard deviation of the percentage change column
    """
    mean = adjusted_df["Percentage Change"].mean()
    std = adjusted_df["Percentage Change"].std()
    return mean, std


def percent_change_as_hist(adjusted_df):
    """
    This function visualizes the percentage change data as a histogram. The graph is also fitted to a normal
     distribution curve.

    :param adjusted_df: Pandas DataFrame with columns: Date, Adjusted Close, and Percentage Change.
    """
    pct_change_list = adjusted_df['Percentage Change']

    # Code below removes the NaN value and plots the histogram. Bins are left adjusted right now, so when plotting the
    # normal distribution function, we must adjust it to be based off the center (average) of the bins.
    n, bins, patches = plt.hist(pct_change_list.dropna(), bins=25, normed=True)
    bincenters = 0.5*(bins[1:]+bins[:-1])

    plt.xlabel("Percentage change")
    plt.ylabel("Frequency")
    mean, std = get_params_for_norm_dist(adjusted_df)
    plt.title("Distribution of percentage change in S&P 500. Mu: %.3f, Sigma: %.3f" % (mean, std), y=1.03)

    # adds vertical lines to the graph corresponding to the x's that represent the number of deviations from the mean
    for num_std_from_mean in range(-3, 4):
        plt.axvline(mean + std * num_std_from_mean)

    # plots the normal pdf of best fit
    y = mlab.normpdf(bincenters, mean, std)
    plt.plot(bincenters, y, 'r--', linewidth=1)

    plt.show()


def percent_change_prob_2x2(adjusted_df, threshold=0):
    """
    This function finds the probabilities associated with the Markov chain of the percentage change column. There are
    two states: % change greater than or equal to a threshold (A) and % change less than a threshold (B). The threshold
    is defaulted to zero, so that the states are roughly divided into positive and negative changes. The four
    probabilities are: a (A | A), b (B | A) , c (A | B) , d (B | B). By definition, the sum of the rows in the right
    stochastic transition matrix must add up to 1: (a + b = 1 and c + d = 1)

            A   B
    P = A   a   b
        B   c   d

    :param adjusted_df: <DataFrame> Pandas DataFrame with columns: Date, Adjusted Close, and Percentage Change.
    :param threshold: <float> Represents the level dividing events A (change >= threshold) & B (change < threshold).
    """
    a_count = 0  # counts frequency of when A occurs then the next period A occurs
    b_count = 0  # counts frequency of when A occurs then the next period B occurs
    c_count = 0  # counts frequency of when B occurs then the next period A occurs
    d_count = 0  # counts frequency of when B occurs then the next period B occurs

    # creates a n
    new_df = adjusted_df['Percentage Change'].dropna().to_frame()
    new_df = new_df.set_index(np.arange(new_df.size, 0, -1))

    for index, pct in new_df['Percentage Change'].iteritems():
        if index == 1:  # prevents program from calculating a future probability
            break
        if pct >= threshold:
            if new_df['Percentage Change'][index-1] >= threshold:
                a_count += 1
            else:
                b_count += 1
        else:
            if new_df['Percentage Change'][index-1] >= threshold:
                c_count += 1
            else:
                d_count += 1

    # Given event A just happened, this is the probability that another event A occurs
    a_prob = a_count / (a_count + b_count)

    # Given event A just happened, this is the probability that event B occurs
    b_prob = b_count / (a_count + b_count)

    # Given event B just happened, this is the probability that event A occurs
    c_prob = c_count / (c_count + d_count)

    # Given event B just happened, this is the probability that another event B occurs
    d_prob = d_count / (c_count + d_count)

    prob_list = [[a_prob, b_prob], [c_prob, d_prob]]
    print(prob_list, "\n")

    print("\nIf the S&P 500 has a positive percentage change this week, there is a %.3f chance that "
          "next week there will be a repeat positive percentage change. If the index rises this week, then there is a "
          "%.3f chance that next week the index will fall. However, if the S&P drops in one week there is a %.3f that"
          " next week there will be a repeat negative percentage change. If the index falls this week, then there is a "
          "%.3f chance that the index will rise next week. \n" % (a_prob, b_prob, d_prob, c_prob))
    return prob_list


def percent_change_prob_3x3(adjusted_df, lower_thresh=-1.0, upper_thresh=1.0):
    """
    This function finds the probabilities associated with the Markov chain of the percentage change column. There are
    three states: % change less than or equal to a lower threshold (A), % change between the upper and lower
    thresholds (B)and % change greater than or equal to an upper threshold (C). The lower threshold is defaulted to -1,
    and the upper threshold is defaulted to +1. Percentage changes below the lower threshold may be considered bearish,
    in between the two thresholds considered stagnant, and above the threshold considered bullish. The nine
    probabilities are: a P(A | A), b (B | A) , c (C | A) , d (A | B), e (B | B), f (C | B), g (A | C), h (B | C), and
    i (C | C). The sum of the rows in the matrix must add up to 1: (a + b + c = 1 and d + e + f = 1 and g + h + i = 1)

            A   B   C
    P = A   a   b   c
        B   d   e   f
        C   g   h   i

    See percent_change_prob_2x2 for more details

    :param adjusted_df: <DataFrame> Pandas DataFrame with columns: Date, Adjusted Close, and Percentage Change.
    :param lower_thresh: <float> Represents the level dividing events A & B
    :param upper_thresh: <float> Represents the level dividing events B & C
    """
    # counts frequency of sub-events
    count_list = [[0, 0, 0],    # a_count, b_count, c_count
                  [0, 0, 0],    # d_count, e_count, f_count
                  [0, 0, 0]]    # g_count, h_count, i_count

    new_df = adjusted_df['Percentage Change'].dropna().to_frame()
    new_df = new_df.set_index(np.arange(new_df.size, 0, -1))

    for index, pct in new_df['Percentage Change'].iteritems():
        if index == 1:  # prevents program from calculating a future probability
            break
        if pct <= lower_thresh:

            if new_df['Percentage Change'][index-1] <= lower_thresh:
                count_list[0][0] += 1  # increment a_count
            elif lower_thresh < new_df['Percentage Change'][index-1] < upper_thresh:
                count_list[0][1] += 1  # increment b_count
            else:
                count_list[0][2] += 1  # increment c_count

        elif lower_thresh < pct < upper_thresh:

            if new_df['Percentage Change'][index-1] <= lower_thresh:
                count_list[1][0] += 1  # increment d_count
            elif lower_thresh < new_df['Percentage Change'][index-1] < upper_thresh:
                count_list[1][1] += 1  # increment e_count
            else:
                count_list[1][2] += 1  # increment f_count

        else:

            if new_df['Percentage Change'][index-1] <= lower_thresh:
                count_list[2][0] += 1  # increment g_count
            elif lower_thresh < new_df['Percentage Change'][index-1] < upper_thresh:
                count_list[2][1] += 1  # increment h_count
            else:
                count_list[2][2] += 1  # increment i_count

    prob_list = [[count / sum(group) for count in group] for group in count_list]
    for group in prob_list:
        print(group)
    lower_thresh_str = "{:.2f}%".format(lower_thresh)
    upper_thresh_str = "{:.2f}%".format(upper_thresh)
    for i in range(3):
        if i == 0:
            part_1_summary = "\nIf the security falls below {lower_thresh} in one period (bearish),"
        elif i == 1:
            part_1_summary = "\nIf the security changes between {lower_thresh} and {upper_thresh} in one period " \
                             "(stagnant),"
        else:
            part_1_summary = "\nIf the security rises above {upper_thresh} in one period (bullish),"

        part_2_summary = "in the next period, there is a {:.3f} chance that the security will fall by more than " \
                         "{lower_thresh} (bearish), a {:.3f} chance that the security will change somewhere between " \
                         "{lower_thresh} and {upper_thresh} (stagnant), and a {:.3f} chance that the security will " \
                         "rise by more than {upper_thresh} (bullish)."
        print((part_1_summary + part_2_summary).format(prob_list[i][0], prob_list[i][1], prob_list[i][2],
                                                       lower_thresh=lower_thresh_str, upper_thresh=upper_thresh_str))

    return prob_list


def random_walk_norm_pdf(adjusted_df, start=2099, num_periods=12):
    """
    This function calculates and visualizes a random walk assuming that S&P 500 data are independent of current state.
    Based on a basic normal distribution and a starting point, the function will predict the S&P 500
    Index movement for a finite number of periods. This is the most fundamental random walk and has many unrealistic
    assumptions, such as the data are independently and identically distributed, which is likely not true for the
    S&P500 Index.

    :param adjusted_df: <DataFrame> Pandas DataFrame with columns: Date, Adjusted Close, and Percentage Change.
    :param start: <float> starting value for S&P 500 random walk
    :param num_periods: <int> number of steps in the random walk process

    """
    mean, std = get_params_for_norm_dist(adjusted_df)
    pct_change_list = []
    all_walks = []  # will hold all the random walk data
    for i in range(100):
        random_walk = [start]
        for period in range(num_periods):
            # sets the step as the last element in the random walk
            step = random_walk[-1]

            # picks a random percent change from a Gaussian distribution based on historical mean and standard deviation
            pct_change = np.random.normal(mean, std)
            pct_change_list.append(pct_change)

            # reordering of percent change formula
            step = ((pct_change * step / 100) + step)

            random_walk.append(step)
        all_walks.append(random_walk)
    show_rand_walks(all_walks)


def prob_from_bins(heights, bins):
    """
    Chooses a random bin based on the prob distribution in the histogram. Then returns a random percentage change from
    that bin.

    :param heights: <list> heights of the histogram
    :param bins: <list> left-hand edges of each bin; must have at least two values in list
    :return: <float> random percentage change
    """
    np_heights = np.asarray(heights)
    bin_length = bins[1]-bins[0]
    np_area = bin_length * np_heights  # sum of area is equal to 1
    bin_num = np.random.choice(np.arange(start=1, stop=len(bins)), p=np_area)
    rand_pct_change = bin_length * np.random.ranf() + bins[bin_num-1]
    return rand_pct_change


def rand_walk_2x2_markov(adjusted_df, prob_list, num_bins=10, threshold=0, start=2099, num_periods=12):
    """

    :param adjusted_df: <DataFrame> Pandas DataFrame with columns: Date, Adjusted Close, and Percentage Change.
    :param prob_list: <list> Contains a 2x2 list that holds the probabilities from a Markov chain with two states
    :param num_bins: <int> Specifies number of bins in the histogram distribution. The more bins, the more realistic
                            the probability distribution will be
    :param threshold: <float> Represents the level dividing events A (change >= threshold) & B (change < threshold)
    :param start: <float> starting value for S&P 500 random walk
    :param num_periods: <int> number of steps in the random walk process
    """

    pct_change_array = np.array(adjusted_df["Percentage Change"].dropna())
    pct_above_threshold_array = pct_change_array[pct_change_array >= threshold]
    pct_below_threshold_array = pct_change_array[pct_change_array < threshold]
    n_above, bins_above, patches_above = plt.hist(pct_above_threshold_array, bins=num_bins, normed=True)
    n_below, bins_below, patches_below = plt.hist(pct_below_threshold_array, bins=num_bins, normed=True)

    # First percentage change is determined from a basic normal distribution. Every following period is based on the
    # percentage change of the previous period
    pct_change_list = []
    all_walks = []  # will hold all the random walk data
    for i in range(1000):
        mean, std = get_params_for_norm_dist(adjusted_df)
        first_pct_change = np.random.normal(mean, std)
        pct_change_list.append(first_pct_change)
        first_step = ((first_pct_change * start / 100) + start)
        random_walk = [start, first_step]

        for period in range(num_periods):
            step = random_walk[-1]
            prev_pct_change = pct_change_list[-1]

            # random number used to test whether event A will occur or event B will occur
            rand_prob = np.random.random_sample()
            if prev_pct_change >= threshold:  # If true, event A occurred
                # prob_list[0][0] is probability that another event A will occur, given event A has happened already
                if rand_prob <= prob_list[0][0]:  # If true, A then A
                    pct_change = prob_from_bins(n_above, bins_above)
                else:  # If true, A then B
                    pct_change = prob_from_bins(n_below, bins_below)
            else:  # If true, event B occurred
                # prob_list[1][0] is probability that event A will occur, given event B has happened already
                if rand_prob <= prob_list[1][0]:  # If true, B then A
                    pct_change = prob_from_bins(n_above, bins_above)
                else:  # If true, B then B
                    pct_change = prob_from_bins(n_below, bins_below)

            pct_change_list.append(pct_change)

            step = ((pct_change * step / 100) + step)

            random_walk.append(step)
        all_walks.append(random_walk)
    show_rand_walks(all_walks)


def rand_walk_3x3_markov(adjusted_df, prob_list, num_bins=10, lower_thresh=-1, upper_thresh=1, start=2099,
                         num_periods=12):
    """

    :param adjusted_df: <DataFrame> Pandas DataFrame with columns: Date, Adjusted Close, and Percentage Change.
    :param prob_list: <list> Contains a 2x2 list that holds the probabilities from a Markov chain with two states
    :param num_bins: <int> Specifies number of bins in the histogram distribution. The more bins, the more realistic
                            the probability distribution will be
    :param lower_thresh: <float> Represents the level dividing events A (pct change < lower thresh) & B(lower thresh <=
    pct change < upper thresh)
    :param upper_thresh: <float> Represents the level dividing events B (lower thresh < pct change < upper thresh) &
    C(upper thresh < pct change)
    :param start: <float> starting value for S&P 500 random walk
    :param num_periods: <int> number of steps in the random walk process
    """

    pct_change_array = np.array(adjusted_df["Percentage Change"].dropna())
    pct_above_array = pct_change_array[pct_change_array >= upper_thresh]
    pct_between_array = pct_change_array[np.logical_and(pct_change_array > lower_thresh,
                                                        pct_change_array < upper_thresh)]
    pct_below_array = pct_change_array[pct_change_array <= lower_thresh]
    n_above, bins_above, patches_above = plt.hist(pct_above_array, bins=num_bins, normed=True)
    n_between, bins_between, patches_between = plt.hist(pct_between_array, bins=num_bins, normed=True)
    n_below, bins_below, patches_below = plt.hist(pct_below_array, bins=num_bins, normed=True)

    # First percentage change is determined from a basic normal distribution. Every following period is based on the
    # percentage change of the previous period
    pct_change_list = []
    all_walks = []  # will hold all the random walk data
    for i in range(1000):
        mean, std = get_params_for_norm_dist(adjusted_df)
        first_pct_change = np.random.normal(mean, std)
        pct_change_list.append(first_pct_change)
        first_step = ((first_pct_change * start / 100) + start)
        random_walk = [start, first_step]

        for period in range(num_periods):
            step = random_walk[-1]
            prev_pct_change = pct_change_list[-1]

            # random number used to test whether event A will occur or event B will occur
            rand_prob = np.random.random_sample()
            if prev_pct_change <= lower_thresh:  # If true, event A occurred
                # prob_list[0][0] is probability that another event A will occur, given event A has happened already
                if 0 < rand_prob <= prob_list[0][0]:  # If true, A then A
                    pct_change = prob_from_bins(n_below, bins_below)
                elif prob_list[0][0] < rand_prob < (prob_list[0][0] + prob_list[0][1]):  # If true, A then B
                    pct_change = prob_from_bins(n_between, bins_between)
                else:  # If true, A then C
                    pct_change = prob_from_bins(n_above, bins_above)

            elif lower_thresh < prev_pct_change < upper_thresh:  # If true, event B occurred
                # prob_list[1][0] is probability that  event A will occur, given event B has happened already
                if 0 < rand_prob <= prob_list[1][0]:  # If true, B then A
                    pct_change = prob_from_bins(n_below, bins_below)
                elif prob_list[1][0] < rand_prob < (prob_list[1][0] + prob_list[1][1]):  # If true, B then B
                    pct_change = prob_from_bins(n_between, bins_between)
                else:  # If true, B then C
                    pct_change = prob_from_bins(n_above, bins_above)

            else:  # If true, event C occurred
                # prob_list[2][0] is probability that  event A will occur, given event C has happened already
                if 0 < rand_prob <= prob_list[2][0]:  # If true, C then A
                    pct_change = prob_from_bins(n_below, bins_below)
                elif prob_list[2][0] < rand_prob < (prob_list[2][0] + prob_list[2][1]):  # If true, C then B
                    pct_change = prob_from_bins(n_between, bins_between)
                else:  # If true, C then C
                    pct_change = prob_from_bins(n_above, bins_above)

            pct_change_list.append(pct_change)

            step = ((pct_change * step / 100) + step)

            random_walk.append(step)
        all_walks.append(random_walk)
    show_rand_walks(all_walks)


def show_rand_walks(all_walks):
    """
    Visualizes all random walks as a plot and distribution.

    :param all_walks: list of all random walks conducted
    """
    np_aw = np.array(all_walks)  # converts the list of all random walks to a Numpy Array
    np_aw_t = np.transpose(np_aw)  # must transpose the array for graph to display properly
    plt.clf()
    plt.plot(np_aw_t)
    plt.xlabel("Steps")
    plt.ylabel("S&P 500 Index Value")
    plt.title("All Random Walks of the S&P 500 Index")
    plt.show()

    # Select last row from np_aw_t: ends
    ends = np_aw_t[-1]

    # Plot histogram of ends, display plot
    n, bins, patches = plt.hist(ends, bins=25, normed=True)
    plt.xlabel("Final S&P 500 Index Value at end of period.")
    plt.ylabel("Frequency")
    rand_mean = ends.mean()
    rand_std = ends.std()

    plt.title("Distribution of Random Walk Final Values. Mean is %d and Standard Deviation is %d"
              % (rand_mean, rand_std), y=1.03)
    for num_std_from_mean in range(-3, 4):
        plt.axvline(rand_mean + rand_std * num_std_from_mean)
    bincenters = 0.5*(bins[1:]+bins[:-1])
    # plots the normal pdf of best fit
    y = mlab.normpdf(bincenters, rand_mean, rand_std)
    plt.plot(bincenters, y, 'r--', linewidth=3)
    plt.show()


markov_df = get_data()
#print(type(markov_df))
#print(markov_df)
percent_change_as_time_plot(markov_df)
percent_change_as_hist(markov_df)
prob_matrix = percent_change_prob_2x2(markov_df)
prob_matrix2 = percent_change_prob_3x3(markov_df, lower_thresh= -1, upper_thresh= 1)
rand_walk_2x2_markov(markov_df, prob_list=prob_matrix)
rand_walk_3x3_markov(markov_df, prob_matrix2, lower_thresh= -1, upper_thresh= 1)
#random_walk_norm_pdf(markov_df, num_periods=12)
