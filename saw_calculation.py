import numpy as np

class SAWCalculation:
    """
    SAW (Simple Additive Weighting) Calculation Module
    
    This module handles all SAW calculations including:
    - Decision matrix normalization (benefit and cost criteria)
    - Weighted score calculation
    - Alternative ranking
    """
    
    def __init__(self, alternatives, criteria, weights, decision_matrix, criteria_types):
        """
        Initialize SAW calculation
        
        Args:
            alternatives: List of alternative names (e.g., game names)
            criteria: List of criterion names
            weights: List/array of criterion weights (from AHP)
            decision_matrix: 2D list/array of alternative values for each criterion
            criteria_types: List of 'benefit' or 'cost' for each criterion
        """
        self.alternatives = alternatives
        self.criteria = criteria
        self.weights = np.array(weights, dtype=float)
        self.decision_matrix = np.array(decision_matrix, dtype=float)
        self.criteria_types = criteria_types
        
        self.n_alternatives = len(alternatives)
        self.n_criteria = len(criteria)
    
    def normalize_benefit_criterion(self, column):
        """
        Normalize benefit criterion (higher is better)
        Formula: r_ij = x_ij / max(x_ij)
        
        Args:
            column: Array of values for a criterion
            
        Returns:
            Normalized array
        """
        max_val = column.max()
        if max_val == 0:
            return column
        return column / max_val
    
    def normalize_cost_criterion(self, column):
        """
        Normalize cost criterion (lower is better)
        Formula: r_ij = min(x_ij) / x_ij
        
        Args:
            column: Array of values for a criterion
            
        Returns:
            Normalized array
        """
        min_val = column.min()
        if min_val == 0:
            # Avoid division by zero
            return np.ones_like(column)
        
        # Handle zero values in column
        normalized = np.zeros_like(column, dtype=float)
        for i, val in enumerate(column):
            if val == 0:
                normalized[i] = 0
            else:
                normalized[i] = min_val / val
        
        return normalized
    
    def normalize_matrix(self):
        """
        Normalize the entire decision matrix based on criteria types
        
        Returns:
            Normalized decision matrix as numpy array
        """
        normalized_matrix = np.zeros_like(self.decision_matrix, dtype=float)
        
        for j in range(self.n_criteria):
            column = self.decision_matrix[:, j]
            
            if self.criteria_types[j].lower() == 'benefit':
                normalized_matrix[:, j] = self.normalize_benefit_criterion(column)
            else:  # cost
                normalized_matrix[:, j] = self.normalize_cost_criterion(column)
        
        return normalized_matrix
    
    def calculate_weighted_scores(self, normalized_matrix):
        """
        Calculate weighted scores for each alternative
        Formula: V_i = Σ(w_j × r_ij)
        
        Args:
            normalized_matrix: Normalized decision matrix
            
        Returns:
            Array of scores for each alternative
        """
        scores = normalized_matrix.dot(self.weights)
        return scores
    
    def create_ranking(self, scores):
        """
        Create ranking of alternatives based on scores
        
        Args:
            scores: Array of scores for each alternative
            
        Returns:
            List of dictionaries with ranking information
        """
        ranking = []
        
        for i, alternative in enumerate(self.alternatives):
            ranking.append({
                'alternative': alternative,
                'score': float(scores[i]),
                'rank': 0
            })
        
        # Sort by score descending (higher score is better)
        ranking.sort(key=lambda x: x['score'], reverse=True)
        
        # Assign ranks
        for i, item in enumerate(ranking):
            item['rank'] = i + 1
        
        return ranking
    
    def get_detailed_scores(self, normalized_matrix, scores):
        """
        Get detailed breakdown of scores for each alternative
        
        Args:
            normalized_matrix: Normalized decision matrix
            scores: Final scores
            
        Returns:
            List of detailed score information
        """
        detailed_scores = []
        
        for i, alternative in enumerate(self.alternatives):
            criterion_contributions = []
            
            for j, criterion in enumerate(self.criteria):
                contribution = normalized_matrix[i, j] * self.weights[j]
                criterion_contributions.append({
                    'criterion': criterion,
                    'normalized_value': float(normalized_matrix[i, j]),
                    'weight': float(self.weights[j]),
                    'contribution': float(contribution),
                    'percentage': float((contribution / scores[i] * 100) if scores[i] > 0 else 0)
                })
            
            detailed_scores.append({
                'alternative': alternative,
                'total_score': float(scores[i]),
                'contributions': criterion_contributions
            })
        
        return detailed_scores
    
    def validate_inputs(self):
        """
        Validate input data
        
        Returns:
            Tuple (is_valid, error_message)
        """
        # Check matrix dimensions
        if self.decision_matrix.shape != (self.n_alternatives, self.n_criteria):
            return False, f"Decision matrix must be {self.n_alternatives}x{self.n_criteria}"
        
        # Check weights length
        if len(self.weights) != self.n_criteria:
            return False, f"Number of weights must match number of criteria ({self.n_criteria})"
        
        # Check if weights sum to approximately 1
        weight_sum = self.weights.sum()
        if not np.isclose(weight_sum, 1.0, rtol=0.01):
            return False, f"Weights must sum to 1.0 (current sum: {weight_sum:.4f})"
        
        # Check criteria types length
        if len(self.criteria_types) != self.n_criteria:
            return False, "Number of criteria types must match number of criteria"
        
        # Check criteria types values
        valid_types = ['benefit', 'cost']
        for i, ctype in enumerate(self.criteria_types):
            if ctype.lower() not in valid_types:
                return False, f"Criteria type must be 'benefit' or 'cost' (got '{ctype}' at index {i})"
        
        # Check for negative values in decision matrix
        if (self.decision_matrix < 0).any():
            return False, "Decision matrix cannot contain negative values"
        
        return True, "Inputs are valid"
    
    def calculate(self):
        """
        Main calculation method - performs complete SAW analysis
        
        Returns:
            Dictionary with all results
        """
        # Validate inputs first
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            return {
                'success': False,
                'error': error_msg
            }
        
        # Normalize decision matrix
        normalized_matrix = self.normalize_matrix()
        
        # Calculate weighted scores
        scores = self.calculate_weighted_scores(normalized_matrix)
        
        # Create ranking
        ranking = self.create_ranking(scores)
        
        # Get detailed scores
        detailed_scores = self.get_detailed_scores(normalized_matrix, scores)
        
        return {
            'success': True,
            'ranking': ranking,
            'normalized_matrix': normalized_matrix.tolist(),
            'scores': scores.tolist(),
            'detailed_scores': detailed_scores,
            'decision_matrix': self.decision_matrix.tolist(),
            'weights': self.weights.tolist(),
            'criteria': self.criteria,
            'alternatives': self.alternatives,
            'criteria_types': self.criteria_types
        }
    
    def get_best_alternative(self):
        """
        Get the best alternative (highest score)
        
        Returns:
            Dictionary with best alternative information
        """
        normalized_matrix = self.normalize_matrix()
        scores = self.calculate_weighted_scores(normalized_matrix)
        
        best_index = scores.argmax()
        
        return {
            'alternative': self.alternatives[best_index],
            'score': float(scores[best_index]),
            'index': int(best_index)
        }
    
    def get_worst_alternative(self):
        """
        Get the worst alternative (lowest score)
        
        Returns:
            Dictionary with worst alternative information
        """
        normalized_matrix = self.normalize_matrix()
        scores = self.calculate_weighted_scores(normalized_matrix)
        
        worst_index = scores.argmin()
        
        return {
            'alternative': self.alternatives[worst_index],
            'score': float(scores[worst_index]),
            'index': int(worst_index)
        }
    
    def compare_alternatives(self, alt1_index, alt2_index):
        """
        Compare two alternatives
        
        Args:
            alt1_index: Index of first alternative
            alt2_index: Index of second alternative
            
        Returns:
            Dictionary with comparison results
        """
        normalized_matrix = self.normalize_matrix()
        scores = self.calculate_weighted_scores(normalized_matrix)
        
        comparison = {
            'alternative_1': {
                'name': self.alternatives[alt1_index],
                'score': float(scores[alt1_index])
            },
            'alternative_2': {
                'name': self.alternatives[alt2_index],
                'score': float(scores[alt2_index])
            },
            'score_difference': float(abs(scores[alt1_index] - scores[alt2_index])),
            'better_alternative': self.alternatives[alt1_index] if scores[alt1_index] > scores[alt2_index] else self.alternatives[alt2_index]
        }
        
        return comparison