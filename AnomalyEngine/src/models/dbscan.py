import math
import numpy as np

class Point:
    def __init__(self, coords):
        self.coords = list(coords)
        self.visited = False
        self.cluster_id = 0  # 0 = unclassified, -1 = noise


class DBSCAN:
    def __init__(self, eps: float = 0.5, min_pts: int = 5):
        self.eps = eps
        self.min_pts = min_pts
        self.points: list[Point] = []

   
    def fit(self, X):
        self.points = [Point(row) for row in X]

        cluster_id = 0

        for p in self.points:
            if p.visited:
                continue

            p.visited = True
            neighbors = self._region_query(p)

            if len(neighbors) < self.min_pts:
                p.cluster_id = -1  # noise
            else:
                cluster_id += 1
                self._expand_cluster(p, neighbors, cluster_id)

        return self

    def _expand_cluster(self, p, neighbors, cluster_id):
        p.cluster_id = cluster_id
        i = 0

        while i < len(neighbors):
            np = neighbors[i]

            if not np.visited:
                np.visited = True
                np_neighbors = self._region_query(np)

                if len(np_neighbors) >= self.min_pts:
                    neighbors.extend(np_neighbors)

            if np.cluster_id == 0:
                np.cluster_id = cluster_id

            i += 1

    #
    def _region_query(self, p):
        return [
            q for q in self.points
            if self._distance(p.coords, q.coords) <= self.eps
        ]

    def _distance(self, a, b):
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


    def get_labels(self):
        return [p.cluster_id for p in self.points]

    
    def fit_predict(self,X):
        self.fit(X);
        return np.array(self.get_labels());