import numpy as np

class AHPCalculation:
    """
    AHP (Analytical Hierarchy Process) Calculation Module
    
    This module handles all AHP calculations including:
    - Weight calculation from pairwise comparison matrix
    - Consistency ratio calculation
    - Matrix normalization
    """
    
    def __init__(self, criteria, pairwise_matrix):
        """
        Initialize AHP calculation
        
        Args:
            criteria: List of criterion names
            pairwise_matrix: 2D list/array of pairwise comparisons
        """
        self.criteria = criteria
        self.n = len(criteria)
        self.pairwise_matrix = np.array(pairwise_matrix, dtype=float)
        
        # Random Index values for different matrix sizes (Saaty's table)
        self.ri_values = {
            1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
        }
    
    def normalize_matrix(self):
        """
        Normalize the pairwise comparison matrix
        Each column is divided by its sum
        
        Returns:
            Normalized matrix as numpy array
        """
        column_sums = self.pairwise_matrix.sum(axis=0)
        normalized_matrix = self.pairwise_matrix / column_sums
        return normalized_matrix
    
    def calculate_weights(self):
        """
        Calculate criteria weights using eigenvector method
        Weight = average of each row in normalized matrix
        
        Returns:
            Array of weights for each criterion
        """
        normalized_matrix = self.normalize_matrix()
        weights = normalized_matrix.mean(axis=1)
        return weights
    
    def calculate_lambda_max(self, weights):
        """
        Calculate the maximum eigenvalue (lambda max)
        
        Args:
            weights: Array of calculated weights
            
        Returns:
            Lambda max value
        """
        weighted_sum = self.pairwise_matrix.dot(weights)
        lambda_max = (weighted_sum / weights).mean()
        return lambda_max
    
    def calculate_consistency_index(self, lambda_max):
        """
        Calculate Consistency Index (CI)
        CI = (lambda_max - n) / (n - 1)
        
        Args:
            lambda_max: Maximum eigenvalue
            
        Returns:
            Consistency Index value
        """
        if self.n <= 1:
            return 0
        ci = (lambda_max - self.n) / (self.n - 1)
        return ci
    
    def calculate_consistency_ratio(self, ci):
        """
        Calculate Consistency Ratio (CR)
        CR = CI / RI
        CR < 0.1 indicates acceptable consistency
        
        Args:
            ci: Consistency Index
            
        Returns:
            Consistency Ratio value
        """
        ri = self.ri_values.get(self.n, 1.49)
        if ri == 0:
            return 0
        cr = ci / ri
        return cr
    
    def get_consistency_details(self, weights):
        """
        Get detailed consistency analysis
        
        Args:
            weights: Array of calculated weights
            
        Returns:
            Dictionary with consistency details
        """
        lambda_max = self.calculate_lambda_max(weights)
        ci = self.calculate_consistency_index(lambda_max)
        cr = self.calculate_consistency_ratio(ci)
        
        return {
            'lambda_max': float(lambda_max),
            'consistency_index': float(ci),
            'consistency_ratio': float(cr),
            'random_index': float(self.ri_values.get(self.n, 1.49)),
            'is_consistent': cr < 0.1
        }
    
    def validate_matrix(self):
        """
        Validate the pairwise comparison matrix
        
        Returns:
            Tuple (is_valid, error_message)
        """
        # Check if matrix is square
        if self.pairwise_matrix.shape[0] != self.pairwise_matrix.shape[1]:
            return False, "Matrix must be square"
        
        # Check if matrix size matches criteria count
        if self.pairwise_matrix.shape[0] != self.n:
            return False, "Matrix size must match number of criteria"
        
        # Check if diagonal elements are 1
        diagonal = np.diag(self.pairwise_matrix)
        if not np.allclose(diagonal, 1):
            return False, "Diagonal elements must be 1"
        
        # Check reciprocal property: a[i,j] * a[j,i] should be close to 1
        for i in range(self.n):
            for j in range(i+1, self.n):
                product = self.pairwise_matrix[i,j] * self.pairwise_matrix[j,i]
                if not np.isclose(product, 1, rtol=0.01):
                    return False, f"Reciprocal property violated at ({i},{j})"
        
        return True, "Matrix is valid"
    
    def calculate(self):
        """
        Main calculation method - performs complete AHP analysis
        
        Returns:
            Dictionary with all results
        """
        # Validate matrix first
        is_valid, error_msg = self.validate_matrix()
        if not is_valid:
            return {
                'success': False,
                'error': error_msg
            }
        
        # Calculate weights
        weights = self.calculate_weights()
        
        # Get consistency details
        consistency = self.get_consistency_details(weights)
        
        # Prepare weight details
        weight_details = []
        for i, criterion in enumerate(self.criteria):
            weight_details.append({
                'criterion': criterion,
                'weight': float(weights[i]),
                'percentage': float(weights[i] * 100)
            })
        
        # Sort by weight descending
        weight_details.sort(key=lambda x: x['weight'], reverse=True)
        
        return {
            'success': True,
            'criteria': self.criteria,
            'weights': weights.tolist(),
            'weight_details': weight_details,
            'normalized_matrix': self.normalize_matrix().tolist(),
            'consistency_ratio': float(consistency['consistency_ratio']),
            'consistency_index': float(consistency['consistency_index']),
            'lambda_max': float(consistency['lambda_max']),
            'random_index': float(consistency['random_index']),
            'is_consistent': bool(consistency['is_consistent'])
        }
    
    def get_weight_ranking(self):
        """
        Get criteria ranked by their weights
        
        Returns:
            List of criteria sorted by weight (descending)
        """
        weights = self.calculate_weights()
        ranking = []
        
        for i, criterion in enumerate(self.criteria):
            ranking.append({
                'criterion': criterion,
                'weight': float(weights[i]),
                'rank': 0
            })
        
        # Sort by weight descending
        ranking.sort(key=lambda x: x['weight'], reverse=True)
        
        # Assign ranks
        for i, item in enumerate(ranking):
            item['rank'] = i + 1
        
        return ranking