from scipy.spatial.distance import euclidean
import numpy as np
import random

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

    p0_shift = list(p0[:])
    p1_shift = list(p1[:])
    q_shift = list(q[:])

    for i, coord in enumerate(p0):
        for point in [p0_shift, p1_shift, q_shift]:
            point[i] -= coord

    return tuple(p0_shift), tuple(p1_shift), tuple(q_shift)

def slope_vector(p0, p1):
    assert len(p0) == len(p1)
    m = []
    for i in range(len(p0)):
        m.append(p1[i] - p0[i])
    return m

def midpoint(p0, m, t):
    assert len(p0) == len(m)

    midpoint = []
    for i in range(len(p0)):
        midpoint.append(p0[i] + (m[i] * t))

    return tuple(midpoint)

def midpoint_cost(p0, q, midpoint, alpha, droot):
    wiring =  euclidean(midpoint, q)
    delay = euclidean(midpoint, q) + euclidean(p0, midpoint) + droot
    cost = (alpha * wiring) + ((1 - alpha) * delay)
    return cost

def critical_values(x, y, z, gamma):
    critical_values = []

    a = (x ** 2) - (gamma * (x ** 2))
    b = (2 * gamma * x * y) - (2 * x * y)
    c = (y ** 2) - (gamma * x * z)

    determinant = (b ** 2) - (4 * a * c)

    if determinant >= 0:
        t1 = (-b + (determinant ** 0.5)) / (2 * a)
        critical_values.append(t1)

        if determinant > 0:
            t2 = (-b - (determinant ** 0.5)) / (2 * a)
            critical_values.append(t2)

    return critical_values

def intermediate_variables(m, q, alpha):
    x = np.dot(m, m)
    y = np.dot(q, m)
    z = np.dot(q, q)
    gamma = (1 - alpha) ** 2

    return x, y, z, gamma

def optimal_midpoint_exact(p0, p1, q, alpha, droot):
    p0_shift, p1_shift, q_shift = translate_to_origin(p0, p1, q)

    candidate_times = [0, 1]

    m = slope_vector(p0_shift, p1_shift)

    x, y, z, gamma = intermediate_variables(m, q_shift, alpha)

    crit_values = critical_values(x, y, z, gamma)
    crit_values = filter(lambda x : 0 <= x <= 1, crit_values)
    candidate_times += crit_values

    best_cost = float("inf")
    best_midpoint = None
    best_delta = None

    for delta in candidate_times:
        mp = midpoint(p0, m, delta)
        cost = midpoint_cost(p0, q, mp, alpha, droot)
        if cost < best_cost:
            best_cost = cost
            best_delta = delta
            best_midpoint = mp

    return best_cost, best_midpoint, best_delta

def optimal_midpoint_approx(p0, p1, q, alpha, droot):
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

    '''
    compute the slope between p1 and p1. the line segment can be defined by y = mx + b
    = p0 + m*t, with 0 <= t <= 1
    '''
    m = slope_vector(p0, p1)

    '''
    try all possible 0 <= t <= 1, to  see which midpoint on the line segment minimizes
    the objective best. We can make delta smaller to approximate the optimal midpoint more
    accuraately.
    '''
    delta = 0.01
    best_cost = float("inf")
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
            mp = midpoint(p0, m, t)

        cost = midpoint_cost(p0, q, mp, alpha, droot)

        if cost < best_cost:
            best_cost = cost
            best_midpoint = midpoint
            best_delta = t

    best_midpoint = tuple(best_midpoint)

    return best_cost, best_midpoint, best_delta

def optimal_midpoint(p0, p1, q, alpha, droot):
    return optimal_midpoint_exact(p0, p1, q, alpha, droot)

def optimal_midpoint_alpha1(p0, p1, q):
    p0_shift, p1_shift, q_shift = translate_to_origin(p0, p1, q)

    m = slope_vector(p0_shift, p1_shift)

    t = (np.dot(q_shift, m)) / (np.dot(m, m))

    if t < 0:
        t = 0
    if t > 1:
        t = 1

    mp = midpoint(p0, m, t)
    cost = euclidean(q, mp)
    return cost, mp, t

def main():
   #  p0 = (7.023415, 4.434017)
#     p1 = (6.94346, 4.763061)
#     q = (6.63524, 4.597408)
#
#     print(optimal_midpoint(p0, p1, q, alpha=0.99))
#     print(optimal_midpoint(p0, p1, q, alpha=1))
#     print(optimal_midpoint_alpha1(p0, p1, q))

    p0 = (0, 0)
    p1 = (1, 1)
    q = (0.7, 0.69)
    print(optimal_midpoint_alpha1(p0, p1, q))

if __name__ == '__main__':
    main()