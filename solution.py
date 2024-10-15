import os

os.environ['MPLCONFIGDIR'] = os.path.expanduser('~/.matplotlib_cache')
import typing
from sklearn.gaussian_process.kernels import *
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.kernel_approximation import Nystroem
import matplotlib.pyplot as plt
from matplotlib import cm
import random

# Set a seed
random.seed(42)

# Set `EXTENDED_EVALUATION` to `True` in order to visualize your predictions.
EXTENDED_EVALUATION = True
EVALUATION_GRID_POINTS = 300  # Number of grid points used in extended evaluation

# Cost function constants
COST_W_UNDERPREDICT = 50.0
COST_W_NORMAL = 1.0

SQUARES = 8


class Model(object):
    """
    Model for this task.
    You need to implement the train_model and generate_predictions methods
    without changing their signatures, but are allowed to create additional methods.
    """

    def __init__(self):
        """
        Initialize your model here.
        We already provide a random number generator for reproducibility.
        """
        self.rng = np.random.default_rng(seed=0)
        self.model = np.random.default_rng(seed=0)
        self.model_grid = self.model_grid(squares=SQUARES)

        # TODO: Add custom initialization for your model here if necessary
    
    def model_grid(self, squares:int, seed=0):
        ""
        model_grid = np.empty((squares, squares), dtype=object)
        for i in range(squares):
            for j in range(squares):
                # just for initialisation
                model_grid[i][j] = np.random.default_rng(seed)
        return model_grid

    def getCoords(self, squares):
        # need to doc better but just creates ranges for grid coords
        # e.g if squares = 4 [(0,0.25),(0.25,0.5),(0.5,0.75),(0.75,1)]
        coords = []
        for i in range(squares):
            start = i/squares
            end = (i+1)/squares
            coords.append([start, end])
        return coords

    def generate_predictions(self, test_coordinates: np.ndarray, test_area_flags: np.ndarray) -> typing.Tuple[
        np.ndarray, np.ndarray, np.ndarray]:
        # Ensure test_area_flags is a boolean array
        test_area_flags = test_area_flags.astype(bool)  # Convert to boolean if not already

        # Prepare the feature array including the test_area_flags
        x_test_feat = np.hstack((test_coordinates, test_area_flags[:, np.newaxis]))
        num_samples = x_test_feat.shape[0]
        gp_mean = np.zeros(num_samples)
        gp_std = np.zeros(num_samples)

        coords = self.getCoords(SQUARES)

        for i in range(SQUARES):
            for j in range(SQUARES):
                mask = (x_test_feat[:, 0] >= coords[j][0]) & (x_test_feat[:, 0] < coords[j][1]) & \
                       (x_test_feat[:, 1] >= coords[i][0]) & (x_test_feat[:, 1] < coords[i][1])
                x_test_square = x_test_feat[mask]

                if x_test_square.size > 0:
                    gp_mean_square, gp_std_square = self.model_grid[i][j].predict(x_test_square, return_std=True)
                    gp_mean[mask] = gp_mean_square
                    gp_std[mask] = gp_std_square

        predictions = gp_mean.copy()
        # Update predictions where test_area_flags is True
        predictions[test_area_flags] += gp_std[test_area_flags]

        return predictions, gp_mean, gp_std

    def train_model(self, train_targets: np.ndarray, train_coordinates: np.ndarray, train_area_flags: np.ndarray):
        """
        Fit your model on the given training data.
        :param train_coordinates: Training features as a 2d NumPy float array of shape (NUM_SAMPLES, 2)
        :param train_targets: Training pollution concentrations as a 1d NumPy float array of shape (NUM_SAMPLES,)
        :param train_area_flags: Binary variable denoting whether the 2D training point is in the residential area (1) or not (0)
        """

        x_feat = np.concatenate((train_coordinates, train_area_flags[:, np.newaxis]), axis=1)
        train_targets = train_targets[:, np.newaxis]
        x_feat_1 = np.empty(shape=(0,3))
        train_targets_1 = np.empty(shape=(0,1))
        x_feat_0 = np.empty(shape=(0,3))
        train_targets_0 = np.empty(shape=(0,1))


        for i in range(0, x_feat.shape[0] - 1):
            # Since flags are stored as booleans, just changed this check to 'Check if True'
            if train_area_flags[i]:
                x_feat_1 = np.vstack([x_feat_1,x_feat[i]])
                train_targets_1 = np.vstack([train_targets_1,train_targets[i]])
            else:
                x_feat_0 = np.vstack([x_feat_0,x_feat[i]])
                train_targets_0 = np.vstack([train_targets_0,train_targets[i]])


        # x_feat_temp = np.empty(shape=(0,3))
        # train_targets_temp = np.empty(shape=(0,1))
        # for i in range(0, 5000):
        #     a = random.randint(0, x_feat_1.shape[0] - 1)
        #     x_feat_temp = np.vstack([x_feat_temp,x_feat_1[a]])
        #     train_targets_temp = np.vstack([train_targets_temp,train_targets_1[i]])
        # for i in range(0, 1000):
        #     a = random.randint(0, x_feat_0.shape[0] - 1)
        #     x_feat_temp = np.vstack([x_feat_temp,x_feat_0[a]])
        #     train_targets_temp = np.vstack([train_targets_temp,train_targets_0[i]])

        #x_feat = x_feat_temp
        #train_targets = train_targets_temp

        # New kernel formula
        #kernel = ConstantKernel() * RationalQuadratic(alpha=1e+04, length_scale=0.0761) + DotProduct(
        #    sigma_0=23.3) + RBF(length_scale=1e+04) + WhiteKernel(noise_level=177)
        
        coords = self.getCoords(SQUARES)

        for i in range(SQUARES): # concerns lat (up and down)
            for j in range(SQUARES): # concerns long (left and right)
                # x_feat has long, lat, residential
                mask = (x_feat[:, 0] >= coords[j][0]) & (x_feat[:, 0] < coords[j][1]) & (
                        x_feat[:, 1] >= coords[i][0]) & (x_feat[:, 1] < coords[i][1])
                x_feat_square = x_feat[mask,:]
                y_square = train_targets[mask,:]
                kernel = ConstantKernel() * RationalQuadratic(alpha=1, length_scale=1) + DotProduct(
                    sigma_0=23.3) + RBF(length_scale=1e-05)+ WhiteKernel(noise_level=177)
                self.model_grid[i][j] = GaussianProcessRegressor(kernel).fit(y=y_square, X=x_feat_square)


# You don't have to change this function
def calculate_cost(ground_truth: np.ndarray, predictions: np.ndarray, area_flags: np.ndarray) -> float:
    """
    Calculates the cost of a set of predictions.

    :param ground_truth: Ground truth pollution levels as a 1d NumPy float array
    :param predictions: Predicted pollution levels as a 1d NumPy float array
    :param area_flags: city_area info for every sample in a form of a bool array (NUM_SAMPLES,)
    :return: Total cost of all predictions as a single float
    """
    assert ground_truth.ndim == 1 and predictions.ndim == 1 and ground_truth.shape == predictions.shape

    # Unweighted cost
    cost = (ground_truth - predictions) ** 2
    weights = np.ones_like(cost) * COST_W_NORMAL

    # Case i): underprediction
    mask = (predictions < ground_truth) & [bool(area_flag) for area_flag in area_flags]
    weights[mask] = COST_W_UNDERPREDICT

    # Weigh the cost and return the average
    return np.mean(cost * weights)


# You don't have to change this function
def check_within_circle(coordinate, circle_parameters):
    """
    Checks if a coordinate is inside a circle.
    :param coordinate: 2D coordinate
    :param circle_parameters: 3D coordinate of the circle center and its radius
    :return: True if the coordinate is inside the circle, False otherwise
    """
    return (coordinate[0] - circle_parameters[0]) ** 2 + (coordinate[1] - circle_parameters[1]) ** 2 < \
        circle_parameters[2] ** 2


# You don't have to change this function
def identify_city_area_flags(grid_coordinates):
    """
    Determines the city_area index for each coordinate in the visualization grid.
    :param grid_coordinates: 2D coordinates of the visualization grid
    :return: 1D array of city_area indexes
    """
    # Circles coordinates
    circles = np.array([[0.5488135, 0.71518937, 0.17167342],
                        [0.79915856, 0.46147936, 0.1567626],
                        [0.26455561, 0.77423369, 0.10298338],
                        [0.6976312, 0.06022547, 0.04015634],
                        [0.31542835, 0.36371077, 0.17985623],
                        [0.15896958, 0.11037514, 0.07244247],
                        [0.82099323, 0.09710128, 0.08136552],
                        [0.41426299, 0.0641475, 0.04442035],
                        [0.09394051, 0.5759465, 0.08729856],
                        [0.84640867, 0.69947928, 0.04568374],
                        [0.23789282, 0.934214, 0.04039037],
                        [0.82076712, 0.90884372, 0.07434012],
                        [0.09961493, 0.94530153, 0.04755969],
                        [0.88172021, 0.2724369, 0.04483477],
                        [0.9425836, 0.6339977, 0.04979664]])

    area_flags = np.zeros((grid_coordinates.shape[0],))

    for i, coordinate in enumerate(grid_coordinates):
        area_flags[i] = any([check_within_circle(coordinate, circ) for circ in circles])

    return area_flags


# You don't have to change this function
def execute_extended_evaluation(model: Model, output_dir: str = '/results'):
    """
    Visualizes the predictions of a fitted model.
    :param model: Fitted model to be visualized
    :param output_dir: Directory in which the visualizations will be stored
    """
    print('Performing extended evaluation')

    # Visualize on a uniform grid over the entire coordinate system
    grid_lat, grid_lon = np.meshgrid(
        np.linspace(0, EVALUATION_GRID_POINTS - 1, num=EVALUATION_GRID_POINTS) / EVALUATION_GRID_POINTS,
        np.linspace(0, EVALUATION_GRID_POINTS - 1, num=EVALUATION_GRID_POINTS) / EVALUATION_GRID_POINTS,
    )
    visualization_grid = np.stack((grid_lon.flatten(), grid_lat.flatten()), axis=1)
    grid_area_flags = identify_city_area_flags(visualization_grid)

    # Obtain predictions, means, and stddevs over the entire map
    predictions, gp_mean, gp_stddev = model.generate_predictions(visualization_grid, grid_area_flags)
    predictions = np.reshape(predictions, (EVALUATION_GRID_POINTS, EVALUATION_GRID_POINTS))
    gp_mean = np.reshape(gp_mean, (EVALUATION_GRID_POINTS, EVALUATION_GRID_POINTS))

    vmin, vmax = 0.0, 65.0

    # Plot the actual predictions
    fig, ax = plt.subplots()
    ax.set_title('Extended visualization of task 1')
    im = ax.imshow(predictions, vmin=vmin, vmax=vmax)
    cbar = fig.colorbar(im, ax=ax)

    # Save figure to pdf
    figure_path = os.path.join(output_dir, 'extended_evaluation.pdf')
    print(figure_path)
    fig.savefig(figure_path)
    print(f'Saved extended evaluation to {figure_path}')

    plt.show()


def extract_area_information(train_x: np.ndarray, test_x: np.ndarray) -> typing.Tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Extracts the city_area information from the training and test features.
    :param train_x: Training features
    :param test_x: Test features
    :return: Tuple of (training features' 2D coordinates, training features' city_area information,
        test features' 2D coordinates, test features' city_area information)
    """
    # Extract the 2D coordinates and area flags from training data
    train_coordinates = train_x[:, 0:2]
    train_area_flags = train_x[:, 2].astype(bool)

    # Extract the 2D coordinates and area flags from test data
    test_coordinates = test_x[:, 0:2]
    test_area_flags = test_x[:, 2].astype(bool)

    assert train_coordinates.shape[0] == train_area_flags.shape[0] and test_coordinates.shape[0] == \
           test_area_flags.shape[0]
    assert train_coordinates.shape[1] == 2 and test_coordinates.shape[1] == 2
    assert train_area_flags.ndim == 1 and test_area_flags.ndim == 1

    return train_coordinates, train_area_flags, test_coordinates, test_area_flags


# you don't have to change this function
def main():
    # Load the training dateset and test features
    train_x = np.loadtxt('train_x.csv', delimiter=',', skiprows=1)
    train_y = np.loadtxt('train_y.csv', delimiter=',', skiprows=1)
    test_x = np.loadtxt('test_x.csv', delimiter=',', skiprows=1)


    # Extract the city_area information
    train_coordinates, train_area_flags, test_coordinates, test_area_flags = extract_area_information(train_x, test_x)

    # Fit the model
    print('Training model')
    model = Model()
    model.train_model(train_y, train_coordinates, train_area_flags)

    # Predict on the test features
    print('Predicting on test features')
    predictions = model.generate_predictions(test_coordinates, test_area_flags)
    print(predictions)

    if EXTENDED_EVALUATION:
        execute_extended_evaluation(model, output_dir='.')


if __name__ == "__main__":
    main()