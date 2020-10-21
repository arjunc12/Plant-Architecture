from scipy.spatial.distance import euclidean
import numpy as np

DIMENSION_COORD = {'x' : 0, 'y' : 1, 'z' : 2}

def angle_between_vectors(v1, v2):
    numerator = np.dot(v1, v2)

    m1 = np.sqrt(np.dot(v1, v1))
    m2 = np.sqrt(np.dot(v2, v2))
    denominator = m1 * m2

    return np.arccos(numerator / denominator)

def rotation_angle(v, dim='y'):
    pass

def translate_to_origin(p0, p1, q):
    '''
    Takes three points (of any dimension) as input; translates the first point to be at
    the origin, and translates the other two points by the same amount in each dimension
    '''
    assert len(p0) == len(p1) == len(q)

    p0_shift = p0[:]
    p1_shift = p1[:]
    q_shift = q[:]

    for i, coord in enumerate(p0):
        for point in [p0_shift, p1_shift, q_shift]:
            point[i] -= coord

    return p0_shift, p1_shirt, q_shift

def optimal_midpoint_approx(p0, p1, q, alpha):
    '''
    approximates the optimal point to insert a point onto a line segment. This method uses
    brute force to try all possible midpoints, within a certain granularity.

    p0, p1 - the points comprising a line segment

    q - the point that should be connected to the line segment

    alpha - the degree to  which we prioritize conduction delay or wiring cost.

    The wiring cost is the distance from q to our chosen midpoint. the conduction delay is
    the sum of the distance from q to our chosen midpoint and the distance from our chosen
    midpoint to p0.

    We want to (mimimize alpha * wiring cost) + ((1 - alpha) * conduction delay)
    '''
    assert len(p0) == len(p1) == len(q)

    p0 = np.array(p0)
    p1 = np.array(p1)
    q = np.array(q)

    '''
    compute the slope between p1 and p1. the line segment can be defined by y = mx + b
    = p0 + m*t, with 0 <= t <= 1
    '''
    m = p1 - p0

    '''
    try all possible 0 <= t <= 1, to  see which midpoint on the line segment minimizes
    the objective best. We can make delta smaller to approximate the optimal midpoint more
    accuraately.
    '''
    delta = 0.01
    best_cost = None
    best_midpoint = None
    best_delta = None
    for t in np.arange(0, 1 + delta, delta):
        midpoint = None
        if t == 0:
            midpoint = p0
            t = int(t)
        elif t == 1:
            midpoint = p1
            t = int(t)
        else:
            midpoint = p0 + m * t
        wiring =  euclidean(midpoint, q)
        delay = euclidean(midpoint, q) + euclidean(p0, midpoint)
        cost = (alpha * wiring) + ((1 - alpha) * delay)

        if best_cost == None or cost < best_cost:
            best_cost = cost
            best_midpoint = midpoint
            best_delta = t

    best_midpoint = tuple(best_midpoint)

    return best_cost, best_midpoint, best_delta

def main():
    p0 = (0, 0)
    p1 = (0.07, 1)
    q = (-1.2, 0.75)
    for alpha in np.arange(0.01, 1, 0.01):
        print(alpha, optimal_midpoint_approx(p0, p1, q, alpha))

if __name__ == '__main__':
    main()