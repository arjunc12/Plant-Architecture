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

    return midpoint

def midpoint_cost(p0, q, midpoint, alpha):
    wiring =  euclidean(midpoint, q)
    delay = euclidean(midpoint, q) + euclidean(p0, midpoint)
    cost = (alpha * wiring) + ((1 - alpha) * delay)
    return cost

def critical_values_wolfram_alpha(x, y, z, gamma):
    critical_values = []

    sqrt_subterm1 = ((gamma ** 2) * (x ** 3) * z)
    sqrt_subterm2 = ((gamma ** 2) * (x ** 2) * (y ** 2))
    sqrt_subterm3 = (gamma * (x ** 3) * z)
    sqrt_subterm4 = (gamma * (x ** 2) * (y ** 2))
    sqrt_term = -sqrt_subterm1 + sqrt_subterm2 + sqrt_subterm3 - sqrt_subterm4

    denom_term = (gamma * (x ** 2)) - (x ** 2)

    if sqrt_term >= 0 and denom_term != 0:
        num_term1 = sqrt_term ** 0.5
        num_term2 = gamma * x * y
        num_term3 = x * y

        t1 = (num_term1 + num_term2 - num_term3) / denom_term
        critical_values.append(t1)

        t2 = (-num_term1 + num_term2 - num_term3) / denom_term
        critical_values.append(t2)

    return critical_values

def critical_values_arjun(x, y, z, gamma):
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

def optimal_midpoint_exact(p0, p1, q, alpha, method="wolfram"):
    p0_shift, p1_shift, q_shift = translate_to_origin(p0, p1, q)

    candidate_times = [0, 1]

    m = slope_vector(p0_shift, p1_shift)

    x, y, z, gamma = intermediate_variables(m, q_shift, alpha)

    critical_values = []
    if method == "wolfram":
        critical_values = critical_values_wolfram_alpha(x, y, z, gamma)
    elif method == "arjun":
        critical_values = critical_values_arjun(x, y, z, gamma)
    critical_values = filter(lambda x : 0 <= x <= 1, critical_values)
    candidate_times += critical_values

    best_cost = float("inf")
    best_midpoint = None
    best_delta = None

    for delta in candidate_times:
        mp = midpoint(p0, m, delta)
        cost = midpoint_cost(p0, q, mp, alpha)
        if cost < best_cost:
            best_cost = cost
            best_delta = delta
            best_midpoint = mp

    return best_cost, best_midpoint, best_delta

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

def optimal_midpoint(p0, p1, q, alpha):
    return optimal_midpoint_exact(p0, p1, q, alpha)

def main():
    #p0 = (0, 0)
    #p1 = (0.07, 1)
    #q = (-1.2, 0.75)

    p0 = (0, 0)
    print(p0)
    p1 = (random.uniform(0, 10), random.uniform(0, 10))
    print(p1)
    q = (random.uniform(0, 10), random.uniform(0, 10))
    print(q)

    m = slope_vector(p0, p1)

    for alpha in np.arange(0.01, 1, 0.01):

        x, y, z, gamma = intermediate_variables(m, q, alpha)

        wolfram_cost, wolfram_midpoint, wolfram_delta = optimal_midpoint_exact(p0, p1, q, alpha, method="wolfram")
        arjun_cost, arjun_midpoint, arjun_delta = optimal_midpoint_exact(p0, p1, q, alpha, method="arjun")
        approx_cost, approx_midpoint, approx_delta = optimal_midpoint_approx(p0, p1, q, alpha)

        if approx_cost < arjun_cost:
            print("-----------------------------------")
            print("alpha = ", alpha)
            print("approx cost", approx_cost)
            print("arjun cost", arjun_cost)
            print("-----------------------------------")

    # for alpha in np.arange(0.01, 1, 0.01):
#         exact_cost, exact_midpoint, exact_delta = optimal_midpoint_exact(p0, p1, q, alpha)
#         approx_cost, approx_midpoint, approx_delta = optimal_midpoint_approx(p0, p1, q, alpha)
#         if approx_cost < exact_cost:
#             print("alpha = ", alpha)
#             print("exact cost:", exact_cost)
#             print("approx cost:", approx_cost)
#             print("------------------------------")

if __name__ == '__main__':
    main()