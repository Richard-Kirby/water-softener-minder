# importing the required module
import matplotlib.pyplot as plt


class SaltPlotter:

    def __init__(self):
        plt.rcParams["savefig.format"] = 'svg'

    def plot_save(self, long_term_data, file_name):

        print("plotting")
        x_data = []
        y_data = []

        for i in long_term_data:
            x_data.append(i['datetime'])
            y_data.append(i['salt_level'])

        print(x_data, y_data)

        # plotting the points
        plt.plot(x_data, y_data)

        # naming the x axis
        plt.xlabel('date')
        # naming the y axis
        plt.ylabel('Salt remaining')

        # giving a title to my graph
        plt.title('Salt Level History')

        plt.savefig(file_name)


if __name__ == "__main__":
    salt_plotter = SaltPlotter()
    salt_plotter.plot_save(["15/04", "16/04", "17/04"], [400, 350, 200], "test.jpg")