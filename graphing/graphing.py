# importing the required module
import matplotlib
import matplotlib.pyplot as plt

# Need to use this if no interactive window.
matplotlib.use('Agg')


class SaltPlotter:
    def __init__(self, max_plot_points):
        matplotlib.pyplot.rcParams["savefig.format"] = 'svg'
        self.max_plot_points = max_plot_points

    def plot_save(self, long_term_data, file_name):

        print("plotting")
        x_data = []
        y_data = []

        for i in long_term_data:
            x_data.append(i['datetime'])
            y_data.append(i['salt_level'])

        # print(x_data, y_data)

        fig, ax = plt.subplots()
        ax.plot(x_data[-self.max_plot_points:], y_data[-self.max_plot_points:])

        # rotate and align the tick labels so they look better
        fig.autofmt_xdate()

        # use a more precise date string for the x axis locations in the
        # toolbar
        ax.set_title('Salt History')


        '''
        # plotting the points, adhering the maximum number of points
        matplotlib.pyplot.plot()

        fig, ax = matplotlib.pyplot.subplots()
        #ax.plot(date, r.close)

        # rotate and align the tick labels so they look better
        fig.autofmt_xdate()

        # naming the x axis
        matplotlib.pyplot.xlabel('date')
        # naming the y axis
        matplotlib.pyplot.ylabel('Salt remaining')

        # giving a title to my graph
        matplotlib.pyplot.title('Salt Level History')

        matplotlib.pyplot.savefig(file_name)
        ''' 

if __name__ == "__main__":
    salt_plotter = SaltPlotter()
    salt_plotter.plot_save(["15/04", "16/04", "17/04"], [400, 350, 200], "test.jpg")